import xml.etree.ElementTree as ET
import Koha_SRU as ksru
from dotenv import load_dotenv
import os

load_dotenv()

sru = ksru.Koha_SRU(os.getenv("KOHA_SRU_URL"), ksru.SRU_Version.V1_1)

# --------------- Explain ---------------
res = None
print("\n\n--------------- Explain ---------------")
res = sru.explain()
print("URL :", res.url)

# --------------- Search Retrieve ---------------
res = None
print("\n\n--------------- Search Retrieve 1 ---------------")
res = sru.search("dc.title=renard")
print("URL :", res.url)
print("Query :", res.query)
print("Record Schema :", res.record_schema)
print("Maximum Records :", res.maximum_records)
print("Start Record :", res.start_record)
print("Records id : ", str(res.records_id))

res = None
print("\n\n--------------- Search Retrieve 2 ---------------")
res = sru.search(sru.generate_query(["dc.author=jean", " and dc.title=ans égypte", " and dc.date=1997"]))
print("URL :", res.url)
print("Query :", res.query)
print("Record Schema :", res.record_schema)
print("Maximum Records :", res.maximum_records)
print("Start Record :", res.start_record)
print("Records id : ", str(res.records_id))

res = None
print("\n\n--------------- Search Retrieve 3 ---------------")
res = sru.search(sru.generate_query([
        ksru.Part_Of_Query(ksru.SRU_Indexes.KOHA_AUTHOR, ksru.SRU_Relations.EQUALS, "alice", ksru.SRU_Boolean_Operators.AND),
        ksru.Part_Of_Query(ksru.SRU_Indexes.DC_TITLE, ksru.SRU_Relations.EQUALS, "paysage", ksru.SRU_Boolean_Operators.AND),
        ksru.Part_Of_Query(ksru.SRU_Indexes.DATE, ksru.SRU_Relations.EQUALS, "2014", ksru.SRU_Boolean_Operators.AND),
        ksru.Part_Of_Query(ksru.SRU_Indexes.KOHA_IDENTIFIER_STANDART, ksru.SRU_Relations.EQUALS, "181712253", ksru.SRU_Boolean_Operators.NOT),
    ]),
    record_schema=ksru.SRU_Record_Schemas.MARCXML,
    start_record=2,
    maximum_records=10
)
print("URL :", res.url)
print("Query :", res.query)
print("Record Schema :", res.record_schema)
print("Maximum Records :", res.maximum_records)
print("Start Record :", res.start_record)
print("Records id : ", str(res.records_id))
