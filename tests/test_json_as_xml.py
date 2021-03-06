#  JSON Event Parser - a pure python JSON event based parser.
#
#     Copyright (C) 2021 J. Férard <https://github.com/jferard>
#
#  This file is part of JSON Event Parser.
#
#  JSON Event Parser is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  JSON Event Parser is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
from io import StringIO, BytesIO, TextIOWrapper

from json_event_parser import JSONAsXML, _escape_value, _escape_tag, json2xml


class TestJSONAsXML(unittest.TestCase):
    def test_xml(self):
        source = StringIO(
            '{"a": [-1, 2.0, {"b": -0.7e10, "column":["x", "y"]}], "x": 12, "y": true, "z": null}')
        actual = "".join(JSONAsXML(source, list_item="list_item"))
        self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<root><a><list_item>-1</list_item><list_item>2.0</list_item><list_item><b>-0.7e10</b><column><list_item>x</list_item><list_item>y</list_item></column></list_item></a><x>12</x><y>true</y><z>null</z></root>""",
                         actual)

    def test_example1(self):
        self._compare("example1.json", "example1.xml")

    def test_example2(self):
        self._compare("example2.json", "example2.xml")

    def test_example3(self):
        self._compare("example3.json", "example3.xml")

    def test_example4(self):
        self._compare("example4.json", "example4.xml")

    def test_example5(self):
        self._compare("example5.json", "example5.xml")

    def _compare(self, json, xml):
        self.maxDiff = None
        with open(self._get_path(json), "r", encoding="utf-8") as source, \
                open(self._get_path(xml), "r", encoding="utf-8") as expected:
            self.assertEqual(expected.read(),
                             "".join(JSONAsXML(source,
                                               typed=True, formatted=True)))

    def test_escape_value(self):
        for value, escaped_value in [
            ("test", 'test'),
            ("te&t", '<![CDATA[te&t]]>'),
            ("te']]>t", "<![CDATA[te']]]]><![CDATA[>t]]>")
        ]:
            self.assertEqual(escaped_value, _escape_value(value))

    def test_escape_tag(self):
        for tag, escaped_tag in [
            ("", '_'),
            ("&tag", "_tag"),
            ("ta&g", "ta_g")
        ]:
            self.assertEqual(escaped_tag, _escape_tag(tag))

    def _get_path(self, fname):
        return os.path.join(os.path.dirname(__file__), "files", fname)

    def test_tabs(self):
        source = StringIO(
            '{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":1}}}}}}}}}}}}}}}')
        dest = StringIO()
        json2xml(source, dest, formatted=True)
        self.assertEqual(
            "                                                            <a>1</a>",
            max(dest.getvalue().split("\n"), key=len))

    def test_tab_None(self):
        source = StringIO(
            '{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":1}}}}}}}}}}}}}}}')
        dest = StringIO()
        json2xml(source, dest, formatted=False)
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n<root><a><a><a><a><a><a><a><a><a><a><a><a><a><a><a>1</a></a></a></a></a></a></a></a></a></a></a></a></a></a></a></root>',
            dest.getvalue())

    def test_empty_value(self):
        source = StringIO(
            '{"a":""}')
        dest = StringIO()
        json2xml(source, dest, formatted=False)
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n<root><a/></root>',
            dest.getvalue())

    def test_int_value(self):
        source = StringIO(
            '{"a":1}')
        dest = StringIO()
        json2xml(source, dest, formatted=False, typed=True)
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n<root><a type="int">1</a></root>',
            dest.getvalue())

    def test_float_value(self):
        source = StringIO(
            '{"a":1.5}')
        dest = StringIO()
        json2xml(source, dest, formatted=False, typed=True)
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n<root><a type="float">1.5</a></root>',
            dest.getvalue())

    def test_unicode(self):
        source = StringIO('{"a":"\\ud83d"}')
        dest = StringIO()
        json2xml(source, dest)


if __name__ == '__main__':
    unittest.main()
