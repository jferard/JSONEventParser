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
from io import StringIO

from json_event_parser import JSONLexer, LexerToken, JSONLexError


class TestJSONLexer(unittest.TestCase):
    def test_string(self):
        source = StringIO('"abc"')
        self.assertEqual([(LexerToken.STRING, "abc")], list(JSONLexer(source)))

    def test_unicode(self):
        source = StringIO('"a\\u0062c"')
        self.assertEqual([(LexerToken.STRING, "abc")], list(JSONLexer(source)))

    def test_unicode_high_surrogate(self):
        source = StringIO('"\\ud83c"')
        self.assertEqual([(LexerToken.STRING, '�')], list(JSONLexer(source)))

    def test_unicode_low_surrogate(self):
        source = StringIO('"\\udf09"')
        self.assertEqual([(LexerToken.STRING, '�')], list(JSONLexer(source)))

    def test_unicode_surrogates(self):
        source = StringIO('"\\ud83c\\udf09"')
        self.assertEqual([(LexerToken.STRING, '🌉')], list(JSONLexer(source)))

    def test_escape(self):
        source = StringIO('"\\t\\r\\n\\b\\f"')
        self.assertEqual([(LexerToken.STRING, "\t\r\n\b\f")],
                         list(JSONLexer(source)))

    def test_wrong_escape(self):
        source = StringIO('"\\x"')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Unknown escaped char: `x` at 0:3",
                         str(e.exception))

    def test_zero_number(self):
        source = StringIO('01')
        self.assertEqual(
            [(LexerToken.INT_VALUE, "0"), (LexerToken.INT_VALUE, "1")],
            list(JSONLexer(source)))

    def test_missing_decimals(self):
        source = StringIO('0.')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Missing decimals `0.` at 0:2",
                         str(e.exception))

    def test_missing_exp(self):
        source = StringIO('0.1e')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Missing exp `0.1e` at 0:4",
                         str(e.exception))

    def test_0_exp(self):
        source = StringIO('[-0e10]')
        self.assertEqual([(LexerToken.BEGIN_ARRAY, None),
                          (LexerToken.FLOAT_VALUE, '-0e10'),
                          (LexerToken.END_ARRAY, None)], list(JSONLexer(source)))

    def test_wrong_token(self):
        source = StringIO('Wrong')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Unexpected char `W` at 0:1",
                         str(e.exception))

    def test_spaces(self):
        source = StringIO('"a b c"')
        self.assertEqual([(LexerToken.STRING, "a b c")],
                         list(JSONLexer(source)))

    def test_lex_error(self):
        self.assertEqual("LexError: err at 1:2", str(JSONLexError("err", 1, 2)))

    def test_end_0(self):
        source = StringIO(
            '{"a": 0')
        self.assertEqual([(LexerToken.BEGIN_OBJECT, None),
                          (LexerToken.STRING, 'a'),
                          (LexerToken.NAME_SEPARATOR, None),
                          (LexerToken.INT_VALUE, '0')], list(JSONLexer(source)))

    def test_end_10(self):
        source = StringIO(
            '{"a": 10')
        self.assertEqual([(LexerToken.BEGIN_OBJECT, None),
                          (LexerToken.STRING, 'a'),
                          (LexerToken.NAME_SEPARATOR, None),
                          (LexerToken.INT_VALUE, '10')],
                         list(JSONLexer(source)))

    def test_end_10_dot_5(self):
        source = StringIO(
            '{"a": 10.5')
        self.assertEqual([(LexerToken.BEGIN_OBJECT, None),
                          (LexerToken.STRING, 'a'),
                          (LexerToken.NAME_SEPARATOR, None),
                          (LexerToken.FLOAT_VALUE, '10.5')],
                         list(JSONLexer(source)))

    def test_end_10_dot_accolade(self):
        for number, msg in [
            ('[10.]', "LexError: Missing decimals `10.` at 0:5"),
            ('[10e]', "LexError: Missing exp `10e` at 0:5"),
            ('[10.1e]', "LexError: Missing exp `10.1e` at 0:7"),
            ('[10.1e-]', "LexError: Missing exp `10.1e-` at 0:8"),
        ]:
            source = StringIO(number)
            with self.assertRaises(JSONLexError) as e:
                list(JSONLexer(source))

            self.assertEqual(msg, str(e.exception))

    def test_end_10_dot_5_e_3(self):
        source = StringIO(
            '{"a": 10.5e3')
        self.assertEqual([(LexerToken.BEGIN_OBJECT, None),
                          (LexerToken.STRING, 'a'),
                          (LexerToken.NAME_SEPARATOR, None),
                          (LexerToken.FLOAT_VALUE, '10.5e3')],
                         list(JSONLexer(source)))

    def test_10_53(self):
        source = StringIO(
            '[10.53]')
        self.assertEqual([(LexerToken.BEGIN_ARRAY, None),
                          (LexerToken.FLOAT_VALUE, '10.53'),
                          (LexerToken.END_ARRAY, None)],
                         list(JSONLexer(source)))

    def test_10_e_53(self):
        source = StringIO(
            '[10e-53]')
        self.assertEqual([(LexerToken.BEGIN_ARRAY, None),
                          (LexerToken.FLOAT_VALUE, '10e-53'),
                          (LexerToken.END_ARRAY, None)],
                         list(JSONLexer(source)))

    def test_10_dot_5_e_minus_3(self):
        source = StringIO(
            '10.5e-3')
        self.assertEqual([(LexerToken.FLOAT_VALUE, '10.5e-3')],
                         list(JSONLexer(source)))

    def test_neg_err(self):
        for number, msg in [
            ('-a', "LexError: Expected digit, got `a` at 0:2"),
        ]:
            source = StringIO(number)
            with self.assertRaises(JSONLexError) as e:
                list(JSONLexer(source))

            self.assertEqual(msg, str(e.exception))

    def test_float_errs(self):
        for number, msg in [
            ('10.5e-3.8', "LexError: Unexpected char `.` at 0:9"),
            ('10.5e-', "LexError: Missing exp `10.5e-` at 0:6"),
            ('10.5e', "LexError: Missing exp `10.5e` at 0:5")
        ]:
            source = StringIO(number)
            with self.assertRaises(JSONLexError) as e:
                list(JSONLexer(source))

            self.assertEqual(msg, str(e.exception))

    def test_unifinished_string(self):
        source = StringIO('"foo')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Missing end quote `foo` at 0:4",
                         str(e.exception))

    def test_unifinished_neg_number(self):
        source = StringIO('-')
        with self.assertRaises(JSONLexError) as e:
            list(JSONLexer(source))

        self.assertEqual("LexError: Missing digits `-` at 0:1",
                         str(e.exception))

    def test_word_errs(self):
        for word, msg in [
            ("foo", "LexError: Expected `false` at 0:1"),
            ("too", "LexError: Expected `true` at 0:1"),
            ("noo", "LexError: Expected `null` at 0:1"),
            ("zoo", "LexError: Unexpected char `z` at 0:1")
        ]:
            source = StringIO(word)
            with self.assertRaises(JSONLexError) as e:
                list(JSONLexer(source))

            self.assertEqual(msg, str(e.exception))

    def test_other_escape(self):
        source = StringIO('"\\\"\\\\"')
        self.assertEqual([(LexerToken.STRING, '"\\')],
                         list(JSONLexer(source)))

    def test_lex(self):
        source = StringIO(
            '{"a": [-1, 2.0, {"b": -0.7e10, "column":["x", "y"]}]}')
        self.assertEqual([
            (LexerToken.BEGIN_OBJECT, None),
            (LexerToken.STRING, 'a'),
            (LexerToken.NAME_SEPARATOR, None),
            (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.INT_VALUE, '-1'),
            (LexerToken.VALUE_SEPARATOR, None),
            (LexerToken.FLOAT_VALUE, '2.0'),
            (LexerToken.VALUE_SEPARATOR, None),
            (LexerToken.BEGIN_OBJECT, None),
            (LexerToken.STRING, 'b'),
            (LexerToken.NAME_SEPARATOR, None),
            (LexerToken.FLOAT_VALUE, '-0.7e10'),
            (LexerToken.VALUE_SEPARATOR, None),
            (LexerToken.STRING, 'column'),
            (LexerToken.NAME_SEPARATOR, None),
            (LexerToken.BEGIN_ARRAY, None),
            (LexerToken.STRING, 'x'),
            (LexerToken.VALUE_SEPARATOR, None),
            (LexerToken.STRING, 'y'),
            (LexerToken.END_ARRAY, None),
            (LexerToken.END_OBJECT, None),
            (LexerToken.END_ARRAY, None),
            (LexerToken.END_OBJECT, None)], list(JSONLexer(source)))

    def test_example1(self):
        with open(
                os.path.join(os.path.dirname(__file__), "files/example1.json"),
                "r", encoding="utf-8") as source:
            self.assertEqual([
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'glossary'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'title'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'example glossary'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossDiv'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'title'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'S'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossList'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'GlossEntry'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'ID'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'SGML'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'SortAs'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'SGML'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossTerm'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING,
                 'Standard Generalized Markup Language'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'Acronym'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'SGML'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'Abbrev'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'ISO 8879:1986'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossDef'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_OBJECT, None),
                (LexerToken.STRING, 'para'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING,
                 'A meta-markup language, used to create markup languages such as DocBook.'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossSeeAlso'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.BEGIN_ARRAY, None),
                (LexerToken.STRING, 'GML'),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'XML'),
                (LexerToken.END_ARRAY, None),
                (LexerToken.END_OBJECT, None),
                (LexerToken.VALUE_SEPARATOR, None),
                (LexerToken.STRING, 'GlossSee'),
                (LexerToken.NAME_SEPARATOR, None),
                (LexerToken.STRING, 'markup'),
                (LexerToken.END_OBJECT, None),
                (LexerToken.END_OBJECT, None),
                (LexerToken.END_OBJECT, None),
                (LexerToken.END_OBJECT, None),
                (LexerToken.END_OBJECT, None)],
                list(JSONLexer(source)))


if __name__ == "__main__":
    unittest.main()
