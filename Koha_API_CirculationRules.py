# -*- coding: utf-8 -*- 

# Created for Koha 20.11

# external imports
import logging
import requests
import xml.etree.ElementTree as ET
import json
import re

# Internal import
from Koha_API_InitOAuth2Session import Koha_OAuth2Session

NS = {
    'marc': 'http://www.loc.gov/MARC21/slim'
    }

class Koha_API_CirculationRules(object):
    """Koha_API_CirculationRules
    =======
    PAS A JOUR
    USES KOHA OAuth2
    A set of function wich handle data returned by Koha API 'getBiblioPublic' 
    https://api.koha-community.org/20.11.html#operation/getBiblioPublic
    On init take as arguments :
    - biblionumber (Koha identifier)
    - Koha server URL
    - [optional] : format (the response format) :
        - "application/marcxml+xml" (default)
        - "application/marc-in-json"
        - "application/marc"
        - "text/plain"
"""

    def __init__(self, Koha_OAuth2Session, kohaUrl, service='Koha_API_CirculationRules'):
        self.logger = logging.getLogger(service)
        self.endpoint = str(kohaUrl) + "/api/v1/circulation-rules/kinds"
        self.url = self.endpoint
        self.service = service
        self.payload = {
            
            }
        self.headers = {
            "accept":"application/json"
            }
        
        try:
            r = Koha_OAuth2Session.request(method= "GET", url=self.url, headers=self.headers, params=self.payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.status = 'Error'
            self.logger.error("{} :: Koha_API_PublicBiblio_Init :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format("NULL", r.status_code, r.request.method, r.url, r.text))
            self.error_msg = "Biblionumber inconnu ou service indisponible"
        except requests.exceptions.RequestException as generic_error:
            self.status = 'Error'
            self.logger.error("{} :: Koha_API_PublicBiblio_Init :: Generic exception || URL: {} || {}".format("NULL", self.url, generic_error))
            self.error_msg = "Exception générique, voir les logs pour plus de détails"
        else:
            self.record = r.content.decode('utf-8')
            self.status = 'Success'
            self.logger.debug("{} :: Koha_API_PublicBiblio :: Notice trouvée".format("NULL"))

    def get_record(self):
            """Return the entire record as a string of the specified format."""
            return self.record

    def get_init_status(self):
        """Return the init status as a string."""
        return self.status

    def get_error_msg(self):
        """Return the error message as a string."""
        if hasattr(self, "error_msg"):
            return self.error_msg
        else:
            return "Pas de message d'erreur"  
        
# Unfinished