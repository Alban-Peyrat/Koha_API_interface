# Koha interface

[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)

https://doc.biblibre.com/koha/autour_de_koha/webservices

## Koha_API_Biblios_Intranet_Liblime

### POST biblios with items

* If the itemnumber already exists, update the item
  * If the itemnumber is attached to another biblio, updates the item and attaches it to this biblio
* On an update, if no existing itemnumber is provided, throw 500 Internal Server Error
* On creation, if :
  * an already existing itemnumber (or smaller than the last itemnumber) or a existing barcode is provided, throw 500 Internal Server Error
  * a non-existent itemnumber (and bigger than the last itemnumber) is provided, add an item with this itemnumber
  * else, create a new item
* __Does not delete already existing items__

### Post biblio with a value in 001

* The value in 001 will be ignored