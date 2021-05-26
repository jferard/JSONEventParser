# coding: utf-8
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

import re
import sys
from enum import Enum

# https://datatracker.ietf.org/doc/html/rfc8259

#########
# LEXER #
#########
from io import TextIOBase
from typing import Any


class JSONLexError(ValueError):
    """
    A lex error
    """

    def __init__(self, msg: Any, line: int, column: int):
        self.msg = msg
        self.line = line
        self.column = column

    def __repr__(self):
        return "{} at {}:{}".format(self.msg, self.line, self.column)


WHITE_SPACES = " \t\r\n"
BEGIN_NUMBER = "-0123456789"


class LexerState(Enum):
    """
    The lexer is a DFA. This is the state of the lexer.
    """
    NONE = 0

    NUMBER = 4
    STRING = 5

    NEG_NUMBER = 10
    ZERO_NUMBER = 11
    OTHER_NUMBER = 12
    NUMBER_FRAC = 21
    NUMBER_FRAC_EXP = 22

    ESCAPE = 50
    UNICODE = 51


class LexerToken(Enum):
    """
    Lexer tokens (opcodes)
    """
    BOOLEAN_VALUE = 1
    NULL_VALUE = 2
    STRING = 3
    INT_VALUE = 4
    FLOAT_VALUE = 5

    BEGIN_OBJECT = 10
    END_OBJECT = 11
    BEGIN_ARRAY = 12
    END_ARRAY = 13

    NAME_SEPARATOR = 20
    VALUE_SEPARATOR = 21


class JSONLexer:
    """
    A JSONLexer. Uses a `state` and a `sub_state`.
    """

    def __init__(self, source: TextIOBase):
        self._source = source
        self.line = 0
        self.column = 0

    def __iter__(self):
        state = LexerState.NONE
        sub_state = None
        buf = None
        sub_buf = None
        unget = None  # a one place buffer to `unget` char
        while True:
            if unget:
                next_char = unget
                unget = None
            else:
                next_char = self._source.read(1)
            if not next_char:  # end of the source
                if state == LexerState.NUMBER:  # finish our number if possible
                    if sub_state == LexerState.ZERO_NUMBER:
                        yield LexerToken.INT_VALUE, "0"
                    elif sub_state == LexerState.OTHER_NUMBER:
                        yield LexerToken.INT_VALUE, buf
                    elif sub_state == LexerState.OTHER_NUMBER:
                        yield LexerToken.INT_VALUE, buf
                    elif sub_state == LexerState.NUMBER_FRAC:
                        if buf[-1] == ".":
                            self._lex_error("Missing decimals {}", buf)
                        yield LexerToken.FLOAT_VALUE, buf
                    elif sub_state == LexerState.NUMBER_FRAC_EXP:
                        if buf[-1] == "e":
                            self._lex_error("Missing exp {}", buf)
                        else:
                            yield LexerToken.FLOAT_VALUE, buf

                return

            self.column += 1
            if next_char == "\n":
                self.line += 1
                self.column = 0
            elif state == LexerState.NONE:  # out of objects and arrays
                if next_char in WHITE_SPACES:
                    pass
                elif next_char == "f":  # value : false
                    if self._source.read(4) != "alse":
                        self._lex_error("Expected `false`")
                    yield LexerToken.BOOLEAN_VALUE, False
                elif next_char == "t":  # value : true
                    if self._source.read(3) != "rue":
                        self._lex_error("Expected `true`")
                    yield LexerToken.BOOLEAN_VALUE, True
                elif next_char == "n":  # value : null
                    if self._source.read(3) != "ull":
                        self._lex_error("Expected `null`")
                    yield LexerToken.NULL_VALUE, None
                elif next_char == "{":  # begin-object
                    yield LexerToken.BEGIN_OBJECT, None
                elif next_char == "}":  # end-object
                    yield LexerToken.END_OBJECT, None
                elif next_char == "[":  # begin-array
                    yield LexerToken.BEGIN_ARRAY, None
                elif next_char == "]":  # end-array
                    yield LexerToken.END_ARRAY, None
                elif next_char == ":":  # name-separator
                    yield LexerToken.NAME_SEPARATOR, None
                elif next_char == ",":  # value-separator
                    yield LexerToken.VALUE_SEPARATOR, None
                elif next_char in "-":  # number (negative)
                    state = LexerState.NUMBER
                    sub_state = LexerState.NEG_NUMBER
                    buf = "-"
                elif next_char == "0":  # number (0 or 0.)
                    state = LexerState.NUMBER
                    sub_state = LexerState.ZERO_NUMBER
                    buf = "0"
                elif next_char in "123456789":  # other number
                    state = LexerState.NUMBER
                    sub_state = LexerState.OTHER_NUMBER
                    buf = next_char
                elif next_char == '"':  # begin string
                    state = LexerState.STRING
                    sub_state = LexerState.NONE
                    buf = ""
                else:
                    self._lex_error("Unexpected char {}", next_char)
            elif state == LexerState.NUMBER:  # 6. Numbers
                if sub_state == LexerState.NEG_NUMBER:
                    if next_char == "0":
                        sub_state = LexerState.ZERO_NUMBER
                        buf += "0"
                    elif next_char in "123456789":
                        buf += next_char
                        sub_state = LexerState.OTHER_NUMBER
                elif sub_state == LexerState.ZERO_NUMBER:  # -0 or 0
                    if next_char == ".":
                        sub_state = LexerState.NUMBER_FRAC
                        buf += "."
                    else:
                        yield LexerToken.INT_VALUE, "0"
                        buf = None
                        unget = next_char
                        state = LexerState.NONE
                        sub_state = LexerState.NONE
                elif sub_state == LexerState.OTHER_NUMBER:  # -[1-9] or [1-9]
                    if next_char in "0123456789":
                        buf += next_char
                    elif next_char == ".":
                        sub_state = LexerState.NUMBER_FRAC
                        buf += "."
                    else:
                        yield LexerToken.INT_VALUE, buf
                        buf = None
                        unget = next_char
                        state = LexerState.NONE
                        sub_state = LexerState.NONE
                elif sub_state == LexerState.NUMBER_FRAC:
                    if next_char in "0123456789":
                        buf += next_char
                    elif next_char == "e" or next_char == "E":
                        sub_state = LexerState.NUMBER_FRAC_EXP
                        buf += "e"
                    else:
                        yield LexerToken.FLOAT_VALUE, buf
                        buf = None
                        unget = next_char
                        state = LexerState.NONE
                        sub_state = LexerState.NONE
                elif sub_state == LexerState.NUMBER_FRAC_EXP:
                    if next_char in "0123456789":
                        buf += next_char
                    else:
                        yield LexerToken.FLOAT_VALUE, buf
                        buf = None
                        unget = next_char
                        state = LexerState.NONE
                        sub_state = LexerState.NONE
            elif state == LexerState.STRING:  # 7. Strings
                if sub_state == LexerState.ESCAPE:  # TODO: unicode
                    if next_char in "\"\\":
                        buf += next_char
                        sub_state = LexerState.NONE
                    elif next_char == "b":
                        buf += "\b"
                        sub_state = LexerState.NONE
                    elif next_char == "f":
                        buf += "\f"
                        sub_state = LexerState.NONE
                    elif next_char == "n":
                        buf += "\n"
                        sub_state = LexerState.NONE
                    elif next_char == "r":
                        buf += "\r"
                        sub_state = LexerState.NONE
                    elif next_char == "t":
                        buf += "\t"
                        sub_state = LexerState.NONE
                    elif next_char == "u":
                        sub_state = LexerState.UNICODE
                        sub_buf = []
                    else:
                        self._lex_error("Escaped char: {}", next_char)
                elif sub_state == LexerState.UNICODE:
                    sub_buf += next_char
                    if len(sub_buf) == 4:
                        buf += chr(int("".join(sub_buf), 16))
                        sub_buf = None
                        sub_state = LexerState.NONE
                elif next_char == '\\':
                    sub_state = LexerState.ESCAPE
                elif next_char == '"':
                    state = LexerState.NONE
                    yield LexerToken.STRING, buf
                    buf = ""
                else:  # unescaped
                    buf += next_char

    def _lex_error(self, msg, *parameters):
        if parameters:
            msg = msg.format(*parameters)
        raise JSONLexError(msg, self.line, self.column)


##########
# PARSER #
##########


class JSONParseError(ValueError):
    def __init__(self, msg, line, column):
        self.line = line
        self.column = column
        self.msg = msg

    def __repr__(self):
        return "{} at {}:{}".format(self.msg, self.line, self.column)


class ParserState(Enum):
    NONE = 0
    EXPECTED_KEY = 1
    IN_ARRAY = 10
    IN_ARRAY_SEP = 11
    IN_OBJECT = 12
    IN_OBJECT_MEMBER = 13
    IN_OBJECT_MEMBER_SEP = 14
    IN_OBJECT_SEP = 15


class ParserToken(Enum):
    KEY = 100


class JSONParser:
    def __init__(self, source: TextIOBase):
        self._lex_json = JSONLexer(source)

    def __iter__(self):
        state = ParserState.NONE
        states = []
        for t in self._lex_json:
            if state == ParserState.NONE:
                yield t
                if t[0] == LexerToken.BEGIN_ARRAY:
                    states.append(state)
                    state = ParserState.IN_ARRAY
                elif t[0] == LexerToken.BEGIN_OBJECT:
                    states.append(state)
                    state = ParserState.IN_OBJECT
                elif t[0] in (LexerToken.BOOLEAN_VALUE, LexerToken.NULL_VALUE,
                              LexerToken.INT_VALUE, LexerToken.FLOAT_VALUE,
                              LexerToken.STRING):
                    yield t
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_ARRAY:
                if t[0] == LexerToken.END_ARRAY:
                    yield t
                    state = states.pop()
                elif t[0] in (LexerToken.BOOLEAN_VALUE, LexerToken.NULL_VALUE,
                              LexerToken.INT_VALUE, LexerToken.FLOAT_VALUE,
                              LexerToken.STRING):
                    yield t
                    state = ParserState.IN_ARRAY_SEP
                elif t[0] == LexerToken.BEGIN_ARRAY:
                    yield t
                    states.append(ParserState.IN_ARRAY_SEP)
                    state = ParserState.IN_ARRAY
                elif t[0] == LexerToken.BEGIN_OBJECT:
                    yield t
                    states.append(ParserState.IN_ARRAY_SEP)
                    state = ParserState.IN_OBJECT
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_ARRAY_SEP:
                if t[0] == LexerToken.END_ARRAY:
                    yield t
                    state = states.pop()
                elif t[0] == LexerToken.VALUE_SEPARATOR:
                    state = ParserState.IN_ARRAY
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_OBJECT:
                if t[0] == LexerToken.END_OBJECT:
                    yield t
                    state = states.pop()
                elif t[0] == LexerToken.STRING:
                    yield ParserToken.KEY, t[1]
                    state = ParserState.IN_OBJECT_MEMBER
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_OBJECT_MEMBER:
                if t[0] == LexerToken.NAME_SEPARATOR:
                    state = ParserState.IN_OBJECT_MEMBER_SEP
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_OBJECT_MEMBER_SEP:
                if t[0] in (LexerToken.BOOLEAN_VALUE, LexerToken.NULL_VALUE,
                            LexerToken.INT_VALUE, LexerToken.FLOAT_VALUE,
                            LexerToken.STRING):
                    yield t
                    state = ParserState.IN_OBJECT_SEP
                elif t[0] == LexerToken.BEGIN_ARRAY:
                    yield t
                    states.append(ParserState.IN_OBJECT_SEP)
                    state = ParserState.IN_ARRAY
                elif t[0] == LexerToken.BEGIN_OBJECT:
                    yield t
                    states.append(ParserState.IN_OBJECT_SEP)
                    state = ParserState.IN_OBJECT
                else:
                    self._parse_error(t)
            elif state == ParserState.IN_OBJECT_SEP:
                if t[0] == LexerToken.END_OBJECT:
                    yield t
                    state = states.pop()
                elif t[0] == LexerToken.VALUE_SEPARATOR:
                    state = ParserState.IN_OBJECT
                else:
                    self._parse_error(t)

    def _parse_error(self, msg: Any):
        raise JSONParseError(msg, self._lex_json.column,
                             self._lex_json.line)


#######
# XML #
#######


_XML_HEADER = """<?xml version="1.0" encoding="utf-8"?>"""


def _escape_value(value):
    """
    Use CDATA.

    >>> _escape_value("test")
    'test'
    >>> _escape_value("te&t")
    '<![CDATA[te&t]]>'

    :param value: the value
    :return: the escaped value
    """
    if re.search(r"[<>&\"']", value):
        if ']]>' in value:
            value = value.replace(']]>', ']]]]><![CDATA[>')
        return "<![CDATA[" + value + "]]>"
    else:
        return value


def _escape_tag(key):
    """
    >>> _escape_tag("abc")
    'abc'
    >>> _escape_tag("a(c")
    'a_c'

    https://www.w3.org/TR/2008/REC-xml-20081126/#NT-NameChar

    :param value:
    :return:
    """
    if not key:
        return "_"

    c = key[0]
    if (c in ":_" or 'A' <= c <= 'Z' or 'a' <= c <= 'z'
            or '\xC0' <= c <= '\xD6' or '\xD8' <= c <= '\xF6'
            or '\xF8' <= c <= '\u02FF' or '\u0370' <= c <= '\u037D'
            or '\u037F' <= c <= '\u1FFF' or '\u200C' <= c <= '\u200D'
            or '\u2070' <= c <= '\u218F' or '\u2C00' <= c <= '\u2FEF'
            or '\u3001' <= c <= '\uD7FF' or '\uF900' <= c <= '\uFDCF'
            or '\uFDF0' <= c <= '\uFFFD'):
        new_chars = None
    else:
        new_chars = list(key)
        new_chars[0] = "_"

    for i in range(1, len(key)):
        c = key[i]
        if not (c in ":_-.\xB7" or '0' <= c <= '9' or 'A' <= c <= 'Z'
                or 'a' <= c <= 'z' or '\xC0' <= c <= '\xD6'
                or '\xD8' <= c <= '\xF6' or '\xF8' <= c <= '\u036F'
                or '\u0370' <= c <= '\u037D' or '\u037F' <= c <= '\u1FFF'
                or '\u200C' <= c <= '\u200D' or '\u203F' <= c <= '\u2040'
                or '\u2070' <= c <= '\u218F' or '\u2C00' <= c <= '\u2FEF'
                or '\u3001' <= c <= '\uD7FF' or '\uF900' <= c <= '\uFDCF'
                or '\uFDF0' <= c <= '\uFFFD'):
            if new_chars is None:
                new_chars = list(key)
            new_chars[i] = "_"

    if new_chars is None:
        return key
    else:
        return "".join(new_chars)


class JSONAsXML:
    def __init__(self, source, header: str = _XML_HEADER,
                 root_tag: str = "root", list_element: str = "list_element",
                 typed: bool = False, formatted: bool = False):
        self._source = source
        self._root_tag = root_tag
        self._list_element = list_element
        self._typed = typed
        self._header = header + "\n"
        if formatted:
            self._start_tag = "{0}<{1}>\n"
            self._end_tag = "{0}</{1}>\n"
            self._typed_text = """{0}<{1} type="{2}">{3}</{1}>\n"""
            self._typed_empty = """{0}<{1} type="{2}"/>\n"""
            self._text = "{0}<{1}>{2}</{1}>\n"
            self._empty = "{0}<{1}/>\n"
            self._tabs = [i * "    " for i in range(10)]
        else:
            self._start_tag = "<{1}>"
            self._end_tag = "</{1}>"
            self._typed_text = """<{1} type="{2}">{3}</{1}>"""
            self._typed_empty = """<{1} type="{2}"/>"""
            self._text = "<{1}>{2}</{1}>"
            self._empty = "<{1}/>"
            self._tabs = [None] * 10

    def __iter__(self):
        yield self._header
        tab_count = 0
        spaces = ""
        yield self._start_tag.format("", self._root_tag)
        states_stack = []
        keys_stack = []
        for t in JSONParser(self._source):
            token_type = t[0]
            if (token_type == LexerToken.BEGIN_OBJECT
                    or token_type == LexerToken.BEGIN_ARRAY):
                if states_stack:  # we have to open parent tag
                    cur_state = states_stack[-1]
                    if cur_state == LexerToken.BEGIN_ARRAY:
                        keys_stack.append(self._list_element)
                        # if cur_state == LexerToken.BEGIN_OBJECT, was added
                        # by key
                    cur_key = keys_stack[-1]
                    yield self._start_tag.format(spaces, cur_key)
                tab_count += 1
                lt = len(self._tabs)
                if tab_count == lt:
                    if self._tabs[0] is None:
                        self._tabs.extend(self._tabs)
                    else:
                        self._tabs.extend(
                            [i * "    " for i in range(lt, 2 * lt)])
                spaces = self._tabs[tab_count]
                states_stack.append(token_type)
            elif (token_type == LexerToken.END_OBJECT
                  or token_type == LexerToken.END_ARRAY):
                states_stack.pop()
                if states_stack:  # we have to close parent tag
                    previous_key = keys_stack.pop()
                    tab_count -= 1
                    spaces = self._tabs[tab_count]
                    yield self._end_tag.format(spaces, previous_key)
            elif token_type == ParserToken.KEY:
                assert states_stack[-1] == LexerToken.BEGIN_OBJECT
                key = _escape_tag(t[1])
                keys_stack.append(key)
            else:  # a value
                cur_state = states_stack[-1]
                if cur_state == LexerToken.BEGIN_ARRAY:
                    keys_stack.append(self._list_element)
                    # if cur_state == LexerToken.BEGIN_OBJECT, was added
                    # by key
                cur_key = keys_stack.pop()
                value = t[1]
                if token_type == LexerToken.STRING:
                    if self._typed:
                        value_type = "string"
                        if value:
                            value = _escape_value(value)
                            yield self._typed_text.format(
                                spaces, cur_key, value_type, value)
                        else:
                            yield self._typed_empty.format(
                                spaces, cur_key, value_type)
                    else:
                        if value:
                            value = _escape_value(value)
                            yield self._text.format(spaces, cur_key, value)
                        else:
                            yield self._empty.format(spaces, cur_key)
                else:
                    if self._typed:
                        if token_type == LexerToken.INT_VALUE:
                            value_type = "float"
                        elif token_type == LexerToken.FLOAT_VALUE:
                            value_type = "float"
                        elif token_type == LexerToken.BOOLEAN_VALUE:
                            value_type = "boolean"
                        elif token_type == LexerToken.NULL_VALUE:
                            value_type = "null"
                        else:
                            raise Exception("Token type " + token_type)
                        yield self._typed_text.format(
                            spaces, cur_key, value_type, value)
                    else:
                        yield self._text.format(spaces, cur_key, value)

        yield self._end_tag.format("", self._root_tag)


def json2xml(source, dest, **kwargs):
    """
    Convert JSON to XML
    :param source:
    :param dest:
    :param kwargs:
    :return:
    """
    if kwargs.get("formatted", False):
        for line in JSONAsXML(source, **kwargs):
            try:
                dest.write(line + "\n")
            except UnicodeError:
                dest.write("**\n")
    else:
        it = iter(JSONAsXML(source, **kwargs))
        dest.write(next(it) + "\n")
        for line in it:
            try:
                dest.write(line)
            except UnicodeError:
                dest.write("**")


if __name__ == "__main__":
    # TODO: improve me
    with open(sys.argv[1], "r", encoding="utf-8") as source, \
        open(sys.argv[2], "w", encoding="utf-8") as dest:
        json2xml(source, dest)
