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

import unittest
from io import StringIO

from json_event_parser import JSONParser, LexerToken, ParserToken, \
    JSONParseError


class TestJSONParser(unittest.TestCase):
    def test_parse(self):
        source = StringIO(
            '{"a": [-1, 2.0, {"b": -0.7e10, "column":["x", "y"]}]}')
        self.assertEqual([
            (LexerToken.BEGIN_OBJECT, None),
            (ParserToken.KEY, 'a'),
            (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.INT_VALUE, '-1'),
            (LexerToken.FLOAT_VALUE, '2.0'),
            (LexerToken.BEGIN_OBJECT, None),
            (ParserToken.KEY, 'b'),
            (LexerToken.FLOAT_VALUE, '-0.7e10'),
            (ParserToken.KEY, 'column'),
            (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.STRING, 'x'),
            (LexerToken.STRING, 'y'),
            (LexerToken.END_ARRAY, None),
            (LexerToken.END_OBJECT, None),
            (LexerToken.END_ARRAY, None),
            (LexerToken.END_OBJECT, None)], list(JSONParser(source)))

    def test_parse_array(self):
        source = StringIO(
            '[-1, 2.0]')
        self.assertEqual([
            (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.INT_VALUE, '-1'),
            (LexerToken.FLOAT_VALUE, '2.0'),
            (LexerToken.END_ARRAY, None)
        ], list(JSONParser(source)))

    def test_parse_number(self):
        source = StringIO(
            '-1')
        self.assertEqual([
            (LexerToken.INT_VALUE, '-1')
        ], list(JSONParser(source)))

    def test_empty_array(self):
        source = StringIO(
            '[ ]')
        self.assertEqual([
            (LexerToken.BEGIN_ARRAY, None), (LexerToken.END_ARRAY, None)
        ], list(JSONParser(source)))

    def test_empty_object(self):
        source = StringIO(
            '{ }')
        self.assertEqual([
            (LexerToken.BEGIN_OBJECT, None), (LexerToken.END_OBJECT, None)
        ], list(JSONParser(source)))

    def test_array_in_array(self):
        source = StringIO(
            '[[true]]')
        self.assertEqual([
            (LexerToken.BEGIN_ARRAY, None), (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.BOOLEAN_VALUE, True),
            (LexerToken.END_ARRAY, None), (LexerToken.END_ARRAY, None)
        ], list(JSONParser(source)))

    def test_parse_error(self):
        self.assertEqual("ParseError: err at 1:2",
                         str(JSONParseError("err", 1, 2)))

    def test_array_colon(self):
        source = StringIO(
            '[:]')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.NAME_SEPARATOR: 20>, None)` as array element at 2:0",
            str(e.exception))

    def test_int_member(self):
        source = StringIO(
            '{1:2}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.INT_VALUE: 4>, '1')` as object member at 3:0",
            str(e.exception))

    def test_missing_comma(self):
        source = StringIO(
            '[3 4]')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.INT_VALUE: 4>, '4')` in array, expected `LexerToken.VALUE_SEPARATOR` at 6:0",
            str(e.exception))

    def test_missing_sep(self):
        source = StringIO(
            '{"a" 4}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.INT_VALUE: 4>, '4')`, expected LexerToken.NAME_SEPARATOR at 7:0",
            str(e.exception))

    def test_missing_value(self):
        source = StringIO(
            '{"a":}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.END_OBJECT: 11>, None)` as member value at 6:0",
            str(e.exception))

    def test_missing_sep(self):
        source = StringIO(
            '{"a": 1 "b": 2}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.STRING: 3>, 'b')` in object at 12:0",
            str(e.exception))

    def test_missing_sep2(self):
        source = StringIO(
            '{"a" 1}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.INT_VALUE: 4>, '1')`, expected LexerToken.NAME_SEPARATOR at 7:0",
            str(e.exception))

    def test_close(self):
        source = StringIO(
            '}')
        with self.assertRaises(JSONParseError) as e:
            list(JSONParser(source))

        self.assertEqual(
            "ParseError: Unexpected token `(<LexerToken.END_OBJECT: 11>, None)` at 1:0",
            str(e.exception))

if __name__ == "__main__":
    unittest.main()
