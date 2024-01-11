# Koha_SRU documentation

_[`Koha_SRU_test.py`](../Koha_SRU_test.py) shows some code examples._

This documentation is organized as a _How to use_ :

1. Instantiate the main class
2. Send a request
3. Additional information to help sending the request / using the response

## Instantiate the main class (`Koha_SRU`)

Start by importing the file classes and instantiating a `Koha_SRU`, providing :

* The SRU server URL
* _Optional_ The version (`SRU_Version` entry or directly `1.1` / `1.2` / `1.3` as a string), defaults to `1.1`

``` Python
import Koha_SRU as ksru

sru = ksru.Koha_SRU(os.getenv("KOHA_SRU_URL"), ksru.SRU_Version.V1_1)
```

This will define constants for requests (the `endpoint` and `version`) and give you acces to the 5 functions of the class :

* [`explain()`](#request-an-explain-koha_sruexplain)
* [`search()`](#request-a-search-retrieve-koha_srusearch)
* [`generate_query()`](#generate-a-query-koha_srugenerate_query)

## Request an explain (`Koha_SRU.explain()`)

Explain requests do not take any arguments and return a [`SRU_Result_Explain` instance](#sru_result_explain-instances-properties).

``` Python
res = sru.explain()
```

### `SRU_Result_Explain` instances properties

* `operation` _string_ : supposedly always `explain`
* `status` _string_ : if the request was a success or not, see _Enum_ `Status` for possible values. The same value can be obtained calling the `get_status()` method
* `error` _string_ or _None_ : `None` if no error occurred, else, see the _Enum_ `Errors` for possible values. The same value can be obtained calling the `get_error_msg()` method
* `url` _string_ : the requested URL

Properties that do not get set on error :

* `result_as_string` _string_ : the decoded content of the response to the request
* `result` _xml.etree.ElementTree.ElementTree instance_ : the response parsed. The same value can be obtained calling the `get_result()` method

## Request a search retrieve (`Koha_SRU.search()`)

Search retrieve requests take [a mandatory argument and 3 optional arguments](#koha_srusearch-parameters) and return a [`SRU_Result_Search` instance](#sru_result_search-instances-properties).

``` Python
# Simple
res = sru.search("dc.title=renard")

# More complex
res = sru.search(sru.generate_query(["dc.author=jean", " and dc.title=ans égypte", " and dc.date=1997"]))

# With every parameters
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
```

### `Koha_SRU.search()` parameters

* `query` _mandatory, string_ : the query. The `Koha_SRU.sru_request()` handles the encoding, so it is not necessary to encode it beforehand
* `record_schema` *optional, SRU_Record_Schema or string* : the record schema wanted
  * A string can be use if the value is correct (ex: `marcxml`)
  * Defaults to `marcxml`, any value not in the value list of _Enum_ `SRU_Record_Schema` will be replaced by this value
  * `marcxml` is the only one working in my isntance, so it's also the only entry in `SRU_Record_Schema`
* `maximum_records` _optional, integer_ : the number of returned records for this page
  * Value must be between `1` and `1000` : any value lower than `1` will be readjusted to `10`, any value greater than `1000` will be readjusted to `1000`
  * Defaults to `100`, any non integer value will be replaced by this value (except if the value can be converted  through `int(value)`)
* `start_record` _optional, integer_ : the position of the first result of returned records in the query result list
  * Value must be greater than `0` : any value lower than `1` will be readjusted to `1`
  * Defaults to `1`, any non integer value will be replaced by this value (except if the value can be converted  through `int(value)`)

### `SRU_Result_Search` instances properties

* `operation` _string_ : supposedly always `searchRetrieve`
* `status` _string_ : if the request was a success or not, see _Enum_ `Status` for possible values. The same value can be obtained calling the `get_status()` method
* `error` _string_ or _None_ : `None` if no error occurred, else, see the _Enum_ `Errors` for possible values. The same value can be obtained calling the `get_error_msg()` method
* `url` _string_ : the requested URL

Properties that do not get set on error :

* `result_as_string` _string_ : the decoded content of the response to the request
* `result_as_parsed_xml` _xml.etree.ElementTree.ElementTree instance_ : the response parsed
* `result` _xml.etree.ElementTree.ElementTree instance_ : `result_as_parsed_xml`. The same value can be obtained calling the `get_result()` method
* `record_schema` _string_ : the record schema used in the request
* `maximum_records` _integer_ : the maximum records par page used in the request
* `start_record` _integer_ : the start record number used in the request
* `query` _string_ : the query used in the request (encoded)
* `nb_results` _integer_ : the number of results for the query (`zs{version}:numberofRedcords`). The same value can be obtained calling the `get_nb_results()` method
* `records` _list of xml.etree.ElementTree.ElementTree instances or strings_ : all records of the request, the type depends on the chosen record packing. The same value can be obtained calling the `get_records()` method
* `records_id` _list of strings_ : all the unique identifier (biblionumbers) of the records. The same value can be obtained calling the `get_records_id()` method

## Generate a query (`Koha_SRU.generate_query()`)

Takes [a mandatory argument](#koha_srugenerate_query-parameter) and returns a string.

``` Python
# Combine two elements
query = sru.generate_query([
        ksru.Part_Of_Query(ksru.SRU_Indexes.KOHA_AUTHOR, ksru.SRU_Relations.EQUALS, "alice", ksru.SRU_Boolean_Operators.AND),
        ksru.Part_Of_Query(ksru.SRU_Indexes.DC_TITLE, ksru.SRU_Relations.EQUALS, "paysage", ksru.SRU_Boolean_Operators.AND)])

# Combines Part_Of_Query and strings
query = sru.generate_query([
        ksru.Part_Of_Query(ksru.SRU_Indexes.KOHA_AUTHOR, ksru.SRU_Relations.EQUALS, "alice", ksru.SRU_Boolean_Operators.AND),
        ksru.Part_Of_Query(ksru.SRU_Indexes.DC_TITLE, ksru.SRU_Relations.EQUALS, "paysage", ksru.SRU_Boolean_Operators.AND),
        " and dc.date=2014",
        ksru.Part_Of_Query(ksru.SRU_Indexes.KOHA_IDENTIFIER_STANDART, ksru.SRU_Relations.EQUALS, "181712253", ksru.SRU_Boolean_Operators.NOT),
    ]
```

### `Koha_SRU.generate_query()` parameter

* `list` *mandatory, list of [Part_Of_Query instances](#part_of_query-class) or strings* : the different parts of the query. The `Koha_SRU.sru_request()` handles the encoding, so it is not necessary to encode it beforehand (encoding `-` in the publication date filter (`APU`) __will__ crash the execution)

## `Part_Of_Query` class

`Part_Of_Query` is a class that represents a part of a query, storing each information individually.
On initialization, take [3 mandatory arguments and an optional argument](#part_of_query-initialization-parameters).
__Every parameter has to be provided as the right data type__.

``` Python
# Without specifying the operator
part_one = ksru.Part_Of_Query(
        ksru.SRU_Indexes.KOHA_TITLE,
        ksru.SRU_Relations.EQUALS,
        "renard"))

# Specifying the operator
part_two = ksru.Part_Of_Query(
        ksru.SRU_Indexes.TITLE,
        ksru.SRU_Relations.EQUALS,
        "bordeaux",
        bool_operator=ksru.SRU_Boolean_Operators.OR))
```

### `Part_Of_Query` initialization parameters

* `index` *mandatory, SRU_Indexes* : the index to use
  * If the provided value is not a *SRU_Indexes*, the property `invalid` will be set to `True`
* `relation` *mandatory, SRU_Relations* : the relation to use
  * If the provided relation is not of *SRU_Relations* type, the property `invalid` will be set to `True`
* `value` *mandatory, string or integer* : the value to search in the index
* `bool_operator` *optional, SRU_Boolean_Operators* : the boolean operator to use
  * If the provided operator is not of *SRU_Boolean_Operators* type, the property `invalid` will be set to `True`
  * Defaults to `and`

### `Part_Of_Query` instances properties

* `bool_operator` *SRU_Boolean_Operators* : the boolean operator provided on initilization
* `index` *SRU_Indexes* : the index provided on initilization
* `relation` *SRU_Relations* : the relation provided on initilization
* `value` *string or integer* : the value provided on initilization
* `invalid` *boolean* : is this instance invalid
* `as_string_with_operator` _string_ : the query as a string, including the boolean operator (`{bool_operator.value}{index.value}{relation.value}{value}`). The same value can be obtained calling the `to_string(True)` method
* `as_string_without_operator` _string_ : the query as a string, excluding the boolean operator (`{index.value}{relation.value}{value}`). The same value can be obtained calling the `to_string(False)` method
