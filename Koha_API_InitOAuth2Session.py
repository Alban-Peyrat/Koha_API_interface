# -*- coding: utf-8 -*- 

# Created for Koha 20.11

# external imports
import requests
import json
from requests_oauthlib import OAuth2Session

def Koha_OAuth2Session(koha_url, client_id, client_secret):
    """Return a OAuth2Session object for Koha.
    If it failed, returns the error value of the response.

    Takes as argument :
        - koha_url {str} (including trailing /)
        - client_id {str}
        - client_secret {str}"""
    r_token = requests.request(method="POST", url=koha_url + "api/v1/oauth/token",
                            data={
                                "grant_type": "client_credentials",
                                "client_id": client_id,
                                "client_secret": client_secret
                            }
    )

    token = json.loads(r_token.content)

    if "error" in token:
        return token["error"]
    
    return OAuth2Session(client_id, token=token)