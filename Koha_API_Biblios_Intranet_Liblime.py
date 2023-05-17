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

def validate_bibnb(id):
    """Checks if the biblionumber is onyl a number, returns a tupple :
        - {bool}
        - {str} : biblionumber stripped"""
    id = id.strip()
    if not(re.search("^\d*$", id)):
        return False, id
    else:
        return True, id

def validate_xml(data=None, file_path=None):
    """Checks if data or file_path (if data is None) looks like a correct MARCXML.
    Returns a tupple :
        - {bool}
        - ET element if valid, error message else"""
    # If data is a string, checks if it's valid XML
    if type(data) == str:
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return False, "data is invalid XML"
    # If data is a ET.Element, do nothing
    elif type(data) == ET.Element:
        root = data
    # If a file_path was provided
    # Checks if it exists
    elif not os.path.exists(file_path):
        return False, "Provided file does not exist"
    # Checks if it's valid XML
    elif type(file_path) == str:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError:
            return False, "Provided file is invalid XML"
    else:
        return False, "No data (or inavlid format) provided"
    
    # Checks if it looks like MARCXML
    if len(root.findall("marc:leader", NS)) != 1:
        return False, "Valid XML but no (or too much) leader was find"
    elif len(root.findall("marc:controlfield", NS)) < 1:
        return False, "Valid XML but no controlfield was find"
    elif len(root.findall("marc:datafield", NS)) < 1:
        return False, "Valid XML but no datafield was find"
    else:
        return True, ET.tostring(root)

def update_item(items):
    """Returns "?items=1" if items should be included, or return an empty string.
    
    items should be a bool and be true to include items"""
    if type(items) == bool and items:
        return "?items=1"
    else:
        return ""

def get_biblionumber(record):
    """Returns the biblionumber of a record as a string, if no biblionumber is found, return an empty string.
    
    Takes as argument a MARCXML record as a string."""
    root = ET.fromstring(record)
    if root.find("biblionumber") != None:
        return root.find("biblionumber").text
    else:
        return ""

class KohaAPIBibliosClient(object):
    """KohaAPIBibliosClient
    =======
    A set of function to use https://wiki.koha-community.org/wiki/Koha_/svc/_HTTP_API
    On init take as arguments :
    - koha_url : Koha server URL (no trailing /)
    - userid
    - password
    - service [opt] : service name
"""
    def __init__(self, koha_url, userid, password, service='KohaAPIBibliosClient'):
        self.logger = logging.getLogger(service)
        self.endpoint = str(koha_url) + "/cgi-bin/koha/svc/"
        self.service = service

        try:
            r = requests.get('{}authentication?userid={}&password={}'.format(self.endpoint, urllib.parse.quote(userid), urllib.parse.quote(password)))
            r.raise_for_status()
        except requests.exceptions.RequestException as generic_error:
            self.status = "Error"
            self.logger.error("KohaAPIBibliosClient_Init :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(r.url, r.status_code, r.reason, generic_error))
            self.error_msg = "Generic exception"
        else:
            # Authentication did not succeed
            if ET.fromstring(r.content.decode("utf-8")).find("status").text != "ok":
                self.status = "Error"
                self.logger.error("KohaAPIBibliosClient_Init :: Authentication failed : {}".format(ET.fromstring(r.content.decode("utf-8")).find("status").text))
                self.error_msg = "Authentication failed"

            # Authentication succeeded
            self.cookie_jar = r.cookies
            self.status = "Success"
            self.logger.debug("KohaAPIBibliosClient_Init :: Successfully logged in")

    # ------------- UNIFNISHED
    # Not found on my server so no why bother coding it
    # def get_bib_profile(self):
    #     """Returns fields """
    #     try:
    #         r = requests.get('{}bib_profile'.format(self.endpoint), cookies=self.cookie_jar)
    #         r.raise_for_status()
    #     except requests.exceptions.RequestException as generic_error:
    #         self.status = "Error"
    #         self.logger.error("{} :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(self.service, r.url, r.status_code, r.reason, generic_error))
    #         self.error_msg = "Generic exception"
    #     else:
    #         self.status = "Success"
    #         self.logger.debug("KohaAPIBibliosClient_Init :: Successfully logged in")

    # Not reason for me to do it at the moment
    # def import_bib(self):
    #    """"""

    def get_biblio(self, id, items=False):
        """Returns the XML record as a tupple :
            - {bool} : success ?
            - {str} the XML record if success, error message if not
        
            Takes as an argument :
            - a biblionumber
            - [optionnal] items {bool} : include items (False by default)
        """
        # Checks if the provided ID is a number
        valid_bibnb, bibnb = validate_bibnb(id)
        # Leaves if not
        if not valid_bibnb:
            self.logger.error("{} :: {} (get_biblio) :: Invalid input biblionumber".format(str(id), self.service))
            return False, "Invalid input biblionumber"
        
        if items:
            item_param = "?items=1"
        else:
            item_param = ""

        try:
            r = requests.get('{}bib/{}{}'.format(self.endpoint, bibnb, item_param), cookies=self.cookie_jar)
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