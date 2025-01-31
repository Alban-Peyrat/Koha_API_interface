# -*- coding: utf-8 -*- 

import os
from dotenv import load_dotenv
from Koha_REST_API_Client import KohaRESTAPIClient, Content_Type

load_dotenv()

koha = KohaRESTAPIClient(os.getenv("KOHA_URL"), os.getenv("KOHA_CLIENT_ID"), os.getenv("KOHA_CLIENT_SECRET"))

record = koha.get_biblio("116741", format="application/marcxml+xml")
authority_list = koha.list_auth(format=Content_Type.JSON, nb_res=50, auth_type="A610")
print(record)
