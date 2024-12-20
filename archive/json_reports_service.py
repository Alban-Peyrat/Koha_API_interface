# -*- coding: utf-8 -*- 

# external imports
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
    - params {list of str, dict or list} : parameters for the SQL query (in order)
"""

# Clef du dict = nom affiché dans Koha /!\ UTILISER QUE DE L'ASCII DEDANS

    def __init__(self, id:str, kohaUrl:str, userid:str, password:str, asDict:bool=False, params=[]):
        self.endpoint = kohaUrl + "/cgi-bin/koha/svc/report?id="
        self.id = str(id).strip()
        if not re.match(r"^\d+$", self.id):
            self.status = "Error"
            self.error_msg = "Invalid report ID"
        else:
            self.url = f"{self.endpoint}{self.id}&userid={userid}&password={password}"
            for param in params:
                if type(params) is dict: # doesn't work
                    self.url += "&param_name={}&sql_params={}".format(param, params[param])
                elif type(param) is list:
                    self.url += "&sql_params=" + "%0D%0A".join(param)
                else:
                    self.url += "&sql_params=" + param
            if asDict:
                self.url += "&annotated=1"
            self.headers = {
                "accept":"application/json"
                }
            try:
                r = requests.get(self.url, headers=self.headers)
                r.raise_for_status()  
            except requests.exceptions.HTTPError:
                self.status = "Error"
                self.error_msg = "Unknown report or unavailable service"
            except requests.exceptions.RequestException as generic_error:
                self.status = "Error"
                self.error_msg = f"Genereic error : {generic_error}"
            else:
                self.response = r.content.decode('utf-8')
                self.status = "Success"
                self.data = json.loads(self.response)

    def is_dict(self):
        """Returns True if the results are dictionnaries."""
        if len(self.data) > 0:
            return type(self.data[0]) is dict
    
    def nb_results(self):
        """Returns the number of results"""
        return len(self.data)