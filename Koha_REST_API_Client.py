# -*- coding: utf-8 -*- 

# Coded for Koha 22.11

# external imports
import logging
import json
import requests
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Tuple 
from enum import Enum


NS = {"marc": "http://www.loc.gov/MARC21/slim"}

# ↓ Tf ?
# Ensuite, faire les appels
# Token expire après 3600, check sa validité + relancer un get token si nécessaire
# ya moyen qu'après un call les inforamtions du tokken sont renvoyés

# ----------------- Enum def -----------------

class Content_Type(Enum):
    MARCXML = "application/marcxml+xml"
    MARC_IN_JSON = "application/marc-in-json"
    RAW_MARC = "application/marc"
    RAW_TEXT = "text/plain"

class Errors(Enum):
    # Request Error
    GENERIC_REQUEST_ERROR = 0
    HTTP_ERROR = 1
    GENERIC_REQUEST_ERROR_INTO_NAME_ERROR = 2
    # Data error
    INVALID_BIBNB = 10
    RECORD_DOES_NOT_EXIST = 11

class Status(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    ERROR = 2

class Api_Name(Enum):
    GET_BIBLIO = 0

# ----------------- Func def -----------------

def validate_bibnb(id:str) -> str|None:
    """Checks if the biblionumber is only a number, returns it as a string striped.
    Returns None if biblinoumber is invalid"""
    id = str(id).strip()
    if not(re.search("^\d*$", id)):
        return None
    else:
        return id

# ----------------- Class def -----------------

class KohaRESTAPIClient(object):
    """KohaRESTAPIClient
    =======
    A set of function to use Koha REST APIs
    On init take as arguments :
    - koha_url : Koha server URL
    - client_id
    - client_secret
    - service [opt] : service name
"""
    def __init__(self, koha_url, client_id, client_secret, service='KohaRESTAPIClient'):
        self.service = service
        self.init_logger()
        self.endpoint = str(koha_url).rstrip("/") + "/api/v1/"
        self.error:Errors = None
        self.error_msg:str = None
        self.status:Status = Status.UNKNOWN

        # Try authentification
        try:
            r = requests.request(method="POST", url=self.endpoint + "oauth/token",
                            data={
                                "grant_type": "client_credentials",
                                "client_id": client_id,
                                "client_secret": client_secret
                            }
                        )
            r.raise_for_status()
        # Error managing
        except requests.exceptions.HTTPError:
            self.status = Status.ERROR
            self.error = Errors.HTTP_ERROR
            self.log.http_error(r, init=True)
            self.error_msg = r.reason
        except requests.exceptions.RequestException as generic_error:
            try:
                self.status = Status.ERROR
                self.error = Errors.GENERIC_REQUEST_ERROR
                self.log.request_generic_error(r, generic_error, msg="Generic exception", init=True)
                self.error_msg = f"Generic exception : {r.reason}"
            except NameError as e:
                self.status = Status.ERROR
                self.error = Errors.GENERIC_REQUEST_ERROR_INTO_NAME_ERROR
                self.log.generic_error(e, msg="Generic exception then NameError", init=True)
                self.error_msg = e
        # Access authorized
        else:
            token = json.loads(r.content)
            # Store token 
            self.token = token
            self.status = Status.SUCCESS
            self.log.info(f"{self.log.init_name} :: Access authorized")

    # ---------- API methods ----------

    # ----- Biblios -----

    def get_biblio(self, id:str, format:Content_Type=Content_Type.RAW_MARC) -> str|Errors:
        """Returns the record WITHOUT decoding it.
        If an error occurred, returns an Errors element"""
        # Checks if the provided ID is a number
        api = Api_Name.GET_BIBLIO
        bibnb = validate_bibnb(id)
        # Leaves if not
        if bibnb == None:
            self.log.error(f"{api.name} Invalid input biblionumber ({id})")
            return Errors.INVALID_BIBNB
        
        # Checks if content-type is correct
        content_type = Content_Type.RAW_MARC.value
        if type(format) == Content_Type:
            content_type = format.value
        elif type(format) == str:
            for member in Content_Type:
                if member.value == format:
                    content_type = format

        # Try getting the biblio
        try:
            headers = {
                "Authorization":f"{self.token['token_type']} {self.token['access_token']}",
                "accept":content_type
            }
            r = requests.get(f"{self.endpoint}/biblios/{bibnb}", headers=headers)
            r.raise_for_status()
        # Error handling
        except requests.exceptions.RequestException as generic_error:
            self.log.request_generic_error(r, generic_error, msg=f"{api.name} Generic exception")
            if r.status_code == 404:
                return Errors.RECORD_DOES_NOT_EXIST
            else:
                return Errors.GENERIC_REQUEST_ERROR
        # Succesfully retrieve the record
        else:
            self.log.debug(f"{api.name} Record {id} retrieved")
            return r.content

    # ---------- Logger methods for other classes / functions ----------
    def init_logger(self):
        """Init the logger"""
        self.log = self.Logger(self)

    class Logger(object):
        def __init__(self, parent) -> None:
            self.parent:KohaRESTAPIClient = parent
            self.logger = logging.getLogger(self.parent.service)
            self.init_name = "KohaRESTAPIClient_Init"

        def http_error(self, r:requests.Response, msg:str="", init=False):
            """Log an error statement with the service then HTTP Status, Method, URL and response.
            
            Takes as argument :
                - requests.Reponse
                - [optional] msg : a message to display before HTTP infos
                - [optionnal, default to False] init : if True, set service as 'KohaRESTAPIClient_Init'"""
            # Optinnal Message
            if msg != "":
                msg = f"{msg}. "
            # Service
            service = self.parent.service
            if init:
                service = self.init_name
            self.logger.error(f"{service} :: {msg}HTTP Status : {r.status_code} || Method : {r.request.method} || URL : {r.url} || Reason : {r.text}")

        def request_generic_error(self, r:requests.Response, reason, msg:str="", init=False):
            """Log an error statement with the service then HTTP Status, Method, URL and error reason.
            
            Takes as argument :
                - requests.Reponse
                - reason : the exception message
                - [optional] msg : a message to display before HTTP infos
                - [optionnal, default to False] init : if True, set service as 'KohaRESTAPIClient_Init'"""
            # Optinnal Message
            if msg != "":
                msg = f"{msg}. "
            # Service
            service = self.parent.service
            if init:
                service = self.init_name
            self.logger.error(f"{service} :: {msg}HTTP Status : {r.status_code} || Method : {r.request.method} || URL : {r.url} || Reason : {reason}")

        def generic_error(self, reason, msg:str, init=False):
            """Log an error statement with the service followed by the error message then the error reason.
            
            Takes as argument :
                - reason : the exception message
                - msg : a message to display before HTTP infos
                - [optionnal, default to False] init : if True, set service as 'KohaRESTAPIClient_Init'"""
            # Optinnal Message
            if msg != "":
                msg = f"{msg}. "
            # Service
            service = self.parent.service
            if init:
                service = self.init_name
            self.logger.error(f"{service} :: {msg} || {reason}")

        def critical(self, msg:str):
            """Basic log critical function"""
            self.logger.critical(f"{msg}")

        def debug(self, msg:str):
            """Log a debug statement logging first the service then the message"""
            self.logger.debug(f"{self.parent.service} :: {msg}")

        def info(self, msg:str):
            """Basic log info function"""
            self.logger.info(f"{msg}")

        def error(self, msg:str):
            """Log a error statement logging first the service then the message"""
            self.logger.error(f"{self.parent.service} :: {msg}")






    # def post_biblio(self, id, data=None, file_path=None, items=False, action="update"):
    #     """Update the record 
    #     Returns the XML record as a tupple :
    #         - {bool} : success ?
    #         - {str} the XML record if success, error message if not
        
    #     Takes as an argument :
    #         - a biblionumber
    #         - data OR file_path : data should be a XML record, file_path must be the full path to a MARCXML record
    #         - action :
    #             - "update"
    #             - "new"
    #             - NOT ACTIVE "import"
        
    #     IMPORTANT : data is priotized over file_path

    #     Does not support import_mode options except items
    #     """
    #     # Checks if action is correct
    #     if not action in ["update", "new"]:
    #         data = "Action is not supported"
    #         self.logger.error("{} :: {} (post_biblio) :: {}".format(str(id), self.service, data))
    #         return False, data

    #     # Checks if data is looks like valid MARCXML
    #     valid_data, data = validate_xml(data, file_path) # If valid_data is False, data is an error msg
    #     if not valid_data:
    #         self.logger.error("{} :: {} (update_biblio) :: {}".format(str(id), self.service, data))
    #         return False, data

    #     # If the action is update
    #     if action == "update":
    #         # Checks if the provided ID is a number
    #         valid_bibnb, bibnb = validate_bibnb(id)
    #         # Leaves if not
    #         if not valid_bibnb:
    #             data = "Invalid input biblionumber"
    #             self.logger.error("{} :: {} (update_biblio) :: ".format(str(id), self.service, data))
    #             return False, data
            
    #         api = "bib/" + bibnb

    #     # If it is not an update
    #     else:
    #         api = action + "_bib"
        
    #     # Checks if it must parse items
    #     include_item = update_item(items)

    #     # Updates the data
    #     headers = {"Content-Type": "text/xml"}
    #     try:
    #         r = requests.post('{}{}{}'.format(self.endpoint, api, include_item), cookies=self.cookie_jar, headers=headers, data=data)
    #         r.raise_for_status()
    #     except requests.exceptions.RequestException as generic_error:
    #         self.logger.error("{} (update_biblio) :: Generic exception || URL : {} || Status code : {} || Reason : {} || {}".format(self.service, r.url, r.status_code, r.reason, generic_error))
    #         if r.status_code == 404:
    #             return False, "Record biblionumber {} does not exist".format(bibnb)
    #         else:
    #             return False, "Generic exception"
    #     else:
    #         self.logger.debug(("{} :: {} ({}_biblio) :: Record updated".format(str(id), self.service, action)))
    #         return True, r.content.decode('utf-8')
