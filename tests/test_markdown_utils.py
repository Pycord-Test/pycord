"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from discord.utils import (
    escape_mentions,
    raw_channel_mentions,
    raw_mentions,
    raw_role_mentions,
)


def test_raw_role_mentions_valid_input():
    text = "<@&123456789012345678> <@&987654321098765432>"
    result = raw_role_mentions(text)
    assert result == [123456789012345678, 987654321098765432]


def test_raw_role_mentions_no_mentions():
    text = "This text has no role mentions."
    result = raw_role_mentions(text)
    assert result == []


def test_raw_role_mentions_mixed_mentions():
    text = "<@123456789012345678> <@&987654321098765432> <#123456789012345678>"
    result = raw_role_mentions(text)
    assert result == [987654321098765432]


def test_raw_role_mentions_invalid_format():
    text = "<@&invalid123> <@&123abc456>"
    result = raw_role_mentions(text)
    assert result == []


def test_raw_role_mentions_empty_string():
    text = ""
    result = raw_role_mentions(text)
    assert result == []


def test_raw_channel_mentions_valid_input():
    text = "<#123456789012345678> <#987654321098765432>"
    result = raw_channel_mentions(text)
    assert result == [123456789012345678, 987654321098765432]


def test_raw_channel_mentions_no_mentions():
    text = "This text has no channel mentions."
    result = raw_channel_mentions(text)
    assert result == []


def test_raw_channel_mentions_mixed_mentions():
    text = "<@123456789012345678> <#987654321098765432> <@&123456789012345678>"
    result = raw_channel_mentions(text)
    assert result == [987654321098765432]


def test_raw_channel_mentions_invalid_format():
    text = "<#invalid123> <#123abc456>"
    result = raw_channel_mentions(text)
    assert result == []


def test_raw_channel_mentions_empty_string():
    text = ""
    result = raw_channel_mentions(text)
    assert result == []


def test_raw_mentions_valid_input():
    text = "<@123456789012345678> <@!987654321098765432>"
    result = raw_mentions(text)
    assert result == [123456789012345678, 987654321098765432]


def test_raw_mentions_no_mentions():
    text = "This text has no user mentions."
    result = raw_mentions(text)
    assert result == []


def test_raw_mentions_mixed_mentions():
    text = "<@123456789012345678> <#987654321098765432> <@&123456789012345678>"
    result = raw_mentions(text)
    assert result == [123456789012345678]


def test_raw_mentions_invalid_format():
    text = "<@invalid123> <@!123abc456>"
    result = raw_mentions(text)
    assert result == []


def test_raw_mentions_empty_string():
    text = ""
    result = raw_mentions(text)
    assert result == []


def test_escape_mentions_removes_everyone_and_here():
    text = "@everyone @here"
    result = escape_mentions(text)
    assert result == "@\u200beveryone @\u200bhere"


def test_escape_mentions_ignores_channel_mentions():
    text = "<#123456789012345678>"
    result = escape_mentions(text)
    assert result == "<#123456789012345678>"


def test_escape_mentions_empty_string():
    text = ""
    result = escape_mentions(text)
    assert result == ""


def test_escape_mentions_removes_user_and_role_mentions():
    text = "<@123456789012345678> <@!987654321098765432> <@&123456789012345678>"
    result = escape_mentions(text)
    assert result == "<@\u200b123456789012345678> <@\u200b!987654321098765432> <@\u200b&123456789012345678>"


def test_escape_mentions_handles_mixed_mentions():
    text = "@everyone <@123456789012345678> @here <#987654321098765432>"
    result = escape_mentions(text)
    assert result == "@\u200beveryone <@\u200b123456789012345678> @\u200bhere <#987654321098765432>"
