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

from json_event_parser import JSONParser, LexerToken, ParserToken


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


if __name__ == "__main__":
    unittest.main()
