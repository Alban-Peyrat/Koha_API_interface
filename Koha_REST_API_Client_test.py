# -*- coding: utf-8 -*- 

import os
from dotenv import load_dotenv
from Koha_REST_API_Client import KohaRESTAPIClient, Content_Type

load_dotenv()

koha = KohaRESTAPIClient(os.getenv("KOHA_TEST_URL"), os.getenv("KOHA_TEST_CLIENT_ID"), os.getenv("KOHA_TEST_CLIENT_SECRET"))

record = koha.get_biblio("116741", format=Content_Type.MARCXML)
print(record)
