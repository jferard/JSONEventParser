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
import io
import os
import unittest
from argparse import Namespace

from json_event_parser import _get_parser


class TestParser(unittest.TestCase):
    def test(self):
        parser = _get_parser()
        args = parser.parse_args(["-t", self._get_path("example1.json")])
        self.assertFalse(args.formatted)
        self.assertTrue(args.typed)
        self.assertEqual('<?xml version="1.0" encoding="utf-8"?>', args.header)
        self.assertEqual('li', args.list_item)
        self.assertEqual('root', args.root)

    def _get_path(self, fname):
        return os.path.join(os.path.dirname(__file__), "files", fname)

if __name__ == '__main__':
    unittest.main()
