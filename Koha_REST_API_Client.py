# -*- coding: utf-8 -*- 

# Coded for Koha 20.11

# external imports
import logging
import json
import requests
import urllib.parse
import xml.etree.ElementTree as ET

NS = {"marc": "http://www.loc.gov/MARC21/slim"}

# A faire
# J'ai juste copier-coller la structure de l'API biblios_liblime
# Ensuite, faire les appels

# Token expire après 3600, check sa validité + relancer un get token si nécessaire
# ya moyen qu'après un call les inforamtions du tokken sont renvoyés

class KohaRESTAPIClient(object):
    """KohaRESTAPIClient
    =======
    A set of function to use Koha REST APIs
    On init take as arguments :
    - koha_url : Koha server URL (no trailing /)
    - client_id
    - client_secret
    - service [opt] : service name
"""
    def __init__(self, koha_url, client_id, client_secret, service='KohaRESTAPIClient'):
        self.logger = logging.getLogger(service)
        self.endpoint = str(koha_url) + "/api/v1/"
        self.service = service

        try:
            r = requests.request(method="POST", url=koha_url + "oauth/token",
                            data={
                                "grant_type": "client_credentials",
                                "client_id": client_id,
                                "client_secret": client_secret
                            }
                        )
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.status = 'Error'
            self.logger.error("KohaRESTAPIClient_Init :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(r.status_code, r.request.method, r.url, r.text))
            self.error_msg = r.reason
        except requests.exceptions.RequestException as generic_error:
            try:
                self.status = "Error"
                self.logger.error("KohaRESTAPIClient_Init :: Generic exception. HTTP Status: {} || Method: {} || URL : {} || Reason : {} || {}".format(r.status_code, r.request.method, r.url, generic_error))
                self.error_msg = "Generic exception : " + str(r.reason)
            except NameError as e:
                self.status = "Error"
                self.logger.error("KohaRESTAPIClient_Init :: Generic exception then NameError || {}".format(e))
                self.error_msg = e
            
        else:
            # Access authorized
            token = json.loads(r.content)
            self.token = token
            self.status = "Success"
            self.logger.debug("KohaRESTAPIClient_Init :: Access authorized")

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
        
# ----- Temp tests
import os
from dotenv import load_dotenv
load_dotenv()
a = KohaRESTAPIClient(os.getenv("KOHA_TEST_URL"), os.getenv("KOHA_TEST_CLIENT_ID"), os.getenv("KOHA_TEST_CLIENT_SECRET"))
print(a.error_msg)
# ----- End temp tests