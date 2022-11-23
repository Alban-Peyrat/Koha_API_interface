# -*- coding: utf-8 -*- 

# external imports
import logging
import requests
import json
import re

class Koha_JSON_reports_service(object):
    """Koha_JSON_reports_service
    =======
    A set of function wich handle data returned by Koha JSON reports service 
    On init take as arguments :
    - id : the reprot ID
    - kohaUrl : Koha server URL
    - userid : account userid
    - password : account password
    - [optionnal] asDict {bool}: returns the results as Dict instead of lists
    - params {list of str} : parameters for the SQL query (in order)
"""

# Clef du dict = nom affiché dans Koha /!\ UTILISER QUE DE L'ASCII DEDANS

    def __init__(self,id,kohaUrl, userid, password, asDict=False, params=[], service='Koha_JSON_reports_service'):
        # self.logger = logging.getLogger(service)
        self.endpoint = kohaUrl + "/cgi-bin/koha/svc/report?id="
        self.service = service
        self.id = str(id)
        if re.sub("\D", "", self.id) != self.id: # |||revoir cette conditin
            self.status = "Error"
            # self.logger.error("{} :: Koha_API_PublicBiblio :: Biblionumber invalide".format(bibnb))
            self.error_msg = "Numéro de rapport invalide"
        else:
            self.url = "{}{}&userid={}&password={}".format(self.endpoint, self.id, userid, password)
            for param in params:
                if type(params) is dict: # doesn't work
                    self.url += "&param_name={}&sql_params={}".format(param, params[param])
                else:
                    self.url += "&sql_params=" + param
            if asDict:
                self.url += "&annotated=1"
            self.headers = {
                "accept":"application/json"
                }
            r = requests.get(self.url, headers=self.headers)
            try:
                r.raise_for_status()  
            except requests.exceptions.HTTPError:
                self.status = 'Error'
                # self.logger.error("{} :: Koha_API_PublicBiblio_Init :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(bibnb, r.status_code, r.request.method, r.url, r.text))
                self.error_msg = "Rapport inconnu ou service indisponible"
            else:
                self.response = r.content.decode('utf-8')
                self.status = 'Success'
                self.data = json.loads(self.response)
                # self.logger.debug("{} :: Koha_API_PublicBiblio :: Notice trouvée".format(bibnb))

    def is_dict(self):
        """Returns True if the results are dictionnaries."""
        if len(self.data) > 0:
            return type(self.data[0]) is dict
    
    def nb_results(self):
        """Returns the number of results"""
        return len(self.data)