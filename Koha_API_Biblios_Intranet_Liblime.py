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

class KohaAPIBibliosClient(object):
    """KohaAPIBibliosClient
    =======
    A set of function to use 
    https://api.koha-community.org/20.11.html#operation/getBiblioPublic
    On init take as arguments :
    - koha_url : Koha server URL (no trailing /)
    - userid
    - password
    - service [opt] : service name
"""
    def __init__(self, koha_url, userid, password, service='KohaAPIBibliosClient'):
        self.logger = logging.getLogger(service)
        self.endpoint = str(koha_url) + "cgi-bin/koha/svc/"
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

    def update_biblio(self, id, data=None, file_path=None):
        """Update the record 
        Returns the XML record as a tupple :
            - {bool} : success ?
            - {str} the XML record if success, error message if not
        
        Takes as an argument :
            - a biblionumber
            - data OR file_path : data should be a XML record, file_path must be the full path to a MARCXML record
        
        IMPORTANT : data is priotized over file_path
        """
        # Checks if data is looks like valid MARCXML
        valid_data, data = validate_xml(data, file_path) # If valid_data is False, data is an error msg
        if not valid_data:
            self.logger.error("{} :: {} (update_biblio) :: {}".format(str(id), self.service, data))
            return False, data

        # Checks if the provided ID is a number
        valid_bibnb, bibnb = validate_bibnb(id)
        # Leaves if not
        if not valid_bibnb:
            self.logger.error("{} :: {} (update_biblio) :: Invalid input biblionumber".format(str(id), self.service))
            return False, "Invalid input biblionumber"
        
        # Updates the data
        headers = {"Content-Type": "text/xml"}
        try:
            r = requests.post('{}bib/{}'.format(self.endpoint, bibnb), cookies=self.cookie_jar, headers=headers, data=data)
            r.raise_for_status()
        except requests.exceptions.RequestException as generic_error:
            self.logger.error("{} (update_biblio) :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(self.service, r.url, r.status_code, r.reason, generic_error))
            if r.status_code == 404:
                return False, "Record biblionumber {} does not exist".format(bibnb)
            else:
                return False, "Generic exception"
        else:
            self.logger.debug(("{} :: {} (update_biblio) :: Record updated".format(str(id), self.service)))
            return True, r.content.decode('utf-8')

# #temp -------------------------------------------------------------------------------------------------
# with open("files/settings.json", encoding="utf-8") as f:
#     settings = json.load(f)

# userid = settings["KOHA-USERID"]
# password = settings["KOHA-PASSWORD"]

# koha_url = settings["KOHA_URL"]
# id = "1234"

# record_file = settings["RECORD_FILE_PATH"] # temp
# # record_file = "files/1234_inv.xml"

# xml = """<?xml version="1.0" encoding="UTF-8"?>
# <record
#     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#     xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"
#     xmlns="http://www.loc.gov/MARC21/slim">

#   <leader>02503cas0 2200685   4500</leader>
#   <controlfield tag="001">1234</controlfield>
#   <controlfield tag="003">http://www.sudoc.fr/039235394</controlfield>
#   <controlfield tag="005">20230315151801.0</controlfield>
#   <controlfield tag="009">039235394</controlfield>
#   <datafield tag="011" ind1=" " ind2=" ">
#     <subfield code="a">0038-0296</subfield>
#     <subfield code="f">0038-0296</subfield>
#   </datafield>
#   <datafield tag="033" ind1=" " ind2=" ">
#     <subfield code="a">https://reseau-mirabel.info/revue/titre-id/316</subfield>
#   </datafield>
# </record>
# """
# a = KohaAPIBibliosClient(koha_url, userid, password)
# print(a.update_biblio("1234", file_path=record_file))
# print("ara ara just a breakpoint")

# #temp -------------------------------------------------------------------------------------------------