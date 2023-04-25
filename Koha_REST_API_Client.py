# -*- coding: utf-8 -*- 

# Coded for Koha 20.11

# external imports
import logging
import json
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os

NS = {"marc": "http://www.loc.gov/MARC21/slim"}

# A faire
# J'ai juste copier-coller la structure de l'API biblios_liblime
# A l'init du client, reprendre InitOAuth2Session
# Ensuite, faire les appels

class KohaRESTAPIClient(object):
    """KohaRESTAPIClient
    =======
    A set of function to use https://wiki.koha-community.org/wiki/Koha_/svc/_HTTP_API
    On init take as arguments :
    - koha_url : Koha server URL (no trailing /)
    - userid
    - password
    - service [opt] : service name
"""
    def __init__(self, koha_url, userid, password, service='KohaRESTAPIClient'):
        self.logger = logging.getLogger(service)
        self.endpoint = str(koha_url) + "cgi-bin/koha/svc/"
        self.service = service

        try:
            r = requests.get('{}authentication?userid={}&password={}'.format(self.endpoint, urllib.parse.quote(userid), urllib.parse.quote(password)))
            r.raise_for_status()
        except requests.exceptions.RequestException as generic_error:
            self.status = "Error"
            self.logger.error("KohaRESTAPIClient_Init :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(r.url, r.status_code, r.reason, generic_error))
            self.error_msg = "Generic exception"
        else:
            # Authentication did not succeed
            if ET.fromstring(r.content.decode("utf-8")).find("status").text != "ok":
                self.status = "Error"
                self.logger.error("KohaRESTAPIClient_Init :: Authentication failed : {}".format(ET.fromstring(r.content.decode("utf-8")).find("status").text))
                self.error_msg = "Authentication failed"

            # Authentication succeeded
            self.cookie_jar = r.cookies
            self.status = "Success"
            self.logger.debug("KohaRESTAPIClient_Init :: Successfully logged in")

    def get_biblio(self, id):
        """Returns the XML record as a tupple :
            - {bool} : success ?
            - {str} the XML record if success, error message if not
        
            Takes as an argument a biblionumber
        """
        # Checks if the provided ID is a number
        valid_bibnb, bibnb = validate_bibnb(id)
        # Leaves if not
        if not valid_bibnb:
            self.logger.error("{} :: {} (get_biblio) :: Invalid input biblionumber".format(str(id), self.service))
            return False, "Invalid input biblionumber"
        
        try:
            r = requests.get('{}bib/{}'.format(self.endpoint, bibnb), cookies=self.cookie_jar)
            r.raise_for_status()
        except requests.exceptions.RequestException as generic_error:
            self.logger.error("{} (get_biblio) :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(self.service, r.url, r.status_code, r.reason, generic_error))
            if r.status_code == 404:
                return False, "Record biblionumber {} does not exist".format(bibnb)
            else:
                return False, "Generic exception"
        else:
            self.logger.debug("{} :: {} (get_biblio) :: Record retrieved".format(str(id), self.service))
            return True, r.content.decode('utf-8')

    def post_biblio(self, id, data=None, file_path=None, items=False, action="update"):
        """Update the record 
        Returns the XML record as a tupple :
            - {bool} : success ?
            - {str} the XML record if success, error message if not
        
        Takes as an argument :
            - a biblionumber
            - data OR file_path : data should be a XML record, file_path must be the full path to a MARCXML record
            - action :
                - "update"
                - "new"
                - NOT ACTIVE "import"
        
        IMPORTANT : data is priotized over file_path

        Does not support import_mode options except items
        """
        # Checks if action is correct
        if not action in ["update", "new"]:
            data = "Action is not supported"
            self.logger.error("{} :: {} (post_biblio) :: {}".format(str(id), self.service, data))
            return False, data

        # Checks if data is looks like valid MARCXML
        valid_data, data = validate_xml(data, file_path) # If valid_data is False, data is an error msg
        if not valid_data:
            self.logger.error("{} :: {} (update_biblio) :: {}".format(str(id), self.service, data))
            return False, data

        # If the action is update
        if action == "update":
            # Checks if the provided ID is a number
            valid_bibnb, bibnb = validate_bibnb(id)
            # Leaves if not
            if not valid_bibnb:
                data = "Invalid input biblionumber"
                self.logger.error("{} :: {} (update_biblio) :: ".format(str(id), self.service, data))
                return False, data
            
            api = "bib/" + bibnb

        # If it is not an update
        else:
            api = action + "_bib"
        
        # Checks if it must parse items
        include_item = update_item(items)

        # Updates the data
        headers = {"Content-Type": "text/xml"}
        try:
            r = requests.post('{}{}{}'.format(self.endpoint, api, include_item), cookies=self.cookie_jar, headers=headers, data=data)
            r.raise_for_status()
        except requests.exceptions.RequestException as generic_error:
            self.logger.error("{} (update_biblio) :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(self.service, r.url, r.status_code, r.reason, generic_error))
            if r.status_code == 404:
                return False, "Record biblionumber {} does not exist".format(bibnb)
            else:
                return False, "Generic exception"
        else:
            self.logger.debug(("{} :: {} ({}_biblio) :: Record updated".format(str(id), self.service, action)))
            return True, r.content.decode('utf-8')