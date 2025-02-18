# -*- coding: utf-8 -*- 

import os
from dotenv import load_dotenv
from Koha_REST_API_Client import KohaRESTAPIClient, Content_Type, Record_Schema
import pymarc
from datetime import datetime
import xml.etree.ElementTree as ET
import json

load_dotenv()
NS = {"marc":"http://www.loc.gov/MARC21/slim"}
now = datetime.now()
now_as_str = now.strftime("%d/%m/%Y %H:%M:%S")

koha = KohaRESTAPIClient(os.getenv("KOHA_URL"), os.getenv("KOHA_CLIENT_ID"), os.getenv("KOHA_CLIENT_SECRET"))

# authority_list = koha.list_auth(format=Content_Type.JSON, nb_res=50, auth_type="A610")

# -------------------- PUT / POST biblios --------------------
# Update from raw MARC, using pymarc to edit record
PUT_RAWMARC_bibnb = "577114"
PUT_RAWMARC_record_raw = koha.get_biblio(PUT_RAWMARC_bibnb, format=Content_Type.RAW_MARC)
PUT_RAWMARC_record = pymarc.record.Record(data=PUT_RAWMARC_record_raw, to_unicode=True, force_utf8=True)
u200a = f"[PUT API RAWMARC {now_as_str}] " + PUT_RAWMARC_record.get("200").get("a")
PUT_RAWMARC_record.get("200").delete_subfield("a")
PUT_RAWMARC_record.get("200").add_subfield("a", u200a, pos=0)
PUT_RAWMARC_api_response = koha.update_biblio(PUT_RAWMARC_bibnb, record=PUT_RAWMARC_record.as_marc(), format=Content_Type.RAW_MARC, record_schema=Record_Schema.UNIMARC)
print(PUT_RAWMARC_api_response)

# Post from MARCXML, based on a MARCXML export of Koha, using ET to edit record
POST_MARCXML_record_root = ET.parse("files/POST_API_MARCXML.marcxml")
title = POST_MARCXML_record_root.find("marc:datafield[@tag='200']/marc:subfield[@code='a']", NS)
title.text = f"[POST API MARCXML {now_as_str}] " + title.text
POST_MARCXML_api_response = koha.add_biblio(record=ET.tostring(POST_MARCXML_record_root.getroot()), format=Content_Type.MARCXML, record_schema=Record_Schema.UNIMARC, framework_id="ART")
print(POST_MARCXML_api_response)

# Update from MARC in JSON, using local file for update
PUT_MARCJSON_bibnb = "577115"
# PUT_MARCJSON_record_raw = koha.get_biblio(PUT_MARCJSON_bibnb, format=Content_Type.MARC_IN_JSON)
# PUT_MARCJSON_record = json.dumps(PUT_MARCJSON_record_raw.decode())
PUT_MARCJSON_record = None
with open("files/PUT_API_MARCJSON.json", mode="r", encoding="utf-8") as f:
    PUT_MARCJSON_record = json.load(f)
for field in PUT_MARCJSON_record["fields"]:
    if "200" in field:
        for subf in field["200"]["subfields"]:
            if "a" in subf:
                subf["a"] = f"[PUT API MARCJSON {now_as_str}] " + subf["a"]
PUT_MARCJSON_api_response = koha.update_biblio(PUT_MARCJSON_bibnb, record=json.dumps(PUT_MARCJSON_record), format=Content_Type.MARC_IN_JSON, record_schema=Record_Schema.UNIMARC)
print(PUT_MARCJSON_api_response)


print("Rose")
