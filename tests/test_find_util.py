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

import pytest
from discord.utils import find


def is_even(x):
    return x % 2 == 0


@pytest.mark.parametrize(
    ("seq", "predicate", "expected"),
    [
        ([], lambda x: True, None),
        ([1, 2, 3], lambda x: x > 3, None),
        ([1, 2, 3], lambda x: x == 1, 1),
        ([1, 2, 3], lambda x: x == 2, 2),
        ("abc", lambda c: c == "b", "b"),
        ((10, 20, 30), lambda x: x == 30, 30),
        ([None, False, 0], lambda x: x is None, None),
        ([1, 2, 3, 4], is_even, 2),
    ],
)
def test_find_basic_parametrized(seq, predicate, expected):
    assert find(predicate, seq) is expected


def test_find_with_truthy_non_boolean_predicate():
    seq = [2, 4, 5, 6]
    result = find(lambda x: x % 2, seq)
    assert result == 5


def test_find_on_generator_and_stop_early():
    def bad_gen():
        yield "first"
        raise RuntimeError("should not be reached")

    assert find(lambda x: x == "first", bad_gen()) == "first"


def test_find_does_not_evaluate_rest():
    calls = []

    def predicate(x):
        calls.append(x)
        return x == "stop"

    seq = ["go", "stop", "later"]
    result = find(predicate, seq)
    assert result == "stop"
    assert calls == ["go", "stop"]


def test_find_with_set_returns_first_iterated_element():
    data = {"a", "b", "c"}
    result = find(lambda x: x in data, data)
    assert result in data


def test_find_none_predicate():
    seq = [42, 43, 44]
    result = find(lambda x: True, seq)
    assert result == 42
