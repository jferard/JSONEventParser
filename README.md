JSON Event Parser - a pure python JSON event based parser.

Copyright (C) 2021 J. Férard <https://github.com/jferard>

License: GPLv3

# Summary
JSON Event Parser is a toy project written to convert JSON files to XML without
the need to load the whole JSON object into memory. It relies on three elements :
* a straightforward lexer, based on the [RFC 8259](
  https://datatracker.ietf.org/doc/html/rfc8259) ;
* a straightforward parser, based on the lexer above and the same [RFC 8259](
  https://datatracker.ietf.org/doc/html/rfc8259) ;
* a simple converter from JSON to XML.

Each of these elements is a generator which can be used in a simple `for` loop.
The lexer provides tokens, the parser provides other tokens, and 
the converter provides lines of an XML file.

JSON Event Parser is really slow but does not require any dependency.

If you want to use a full iterative parser, have a look at 
[ijson](https://pypi.org/project/ijson) that relies on [YAJIL](
http://lloyd.github.com/yajl/) (there is also a pure Python backend). 

# Usage

Print the XML counterpart of a JSON file

    with open("path/to/json/file", "r", encoding="utf-8") as source:
        print("\n".join(JSONAsXML(source, typed=True)))

Parse a JSON file

    with open("path/to/json/file", "r", encoding="utf-8") as source:
        for token, value in JSONParser(source):
            print(token, value)

# Tests

    $ python3.8 -m pytest --cov-report term-missing --cov=json_event_parser \
      && python3.8 -m pytest --cov-report term-missing --cov-append --doctest-modules json_event_parser.py --cov=json_event_parser \
      && flake8 json_event_parser.py

