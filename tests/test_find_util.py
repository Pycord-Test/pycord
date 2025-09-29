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

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import Any

import pytest
from discord.utils import find


def is_even(x: int) -> bool:
    return x % 2 == 0


def always_true(_: object) -> bool:
    return True


def greater_than_3(x: int) -> bool:
    return x > 3


def equals_1(x: int) -> bool:
    return x == 1


def equals_2(x: int) -> bool:
    return x == 2


def equals_b(c: str) -> bool:
    return c == "b"


def equals_30(x: int) -> bool:
    return x == 30


def is_none_pred(x: object) -> bool:
    return x is None


@pytest.mark.parametrize(
    ("seq", "predicate", "expected"),
    [
        ([], always_true, None),
        ([1, 2, 3], greater_than_3, None),
        ([1, 2, 3], equals_1, 1),
        ([1, 2, 3], equals_2, 2),
        ("abc", equals_b, "b"),
        ((10, 20, 30), equals_30, 30),
        ([None, False, 0], is_none_pred, None),
        ([1, 2, 3, 4], is_even, 2),
    ],
)
def test_find_basic_parametrized(
    seq: Iterable[Any],
    predicate: Callable[[Any], object],
    expected: Any | None,
) -> None:
    result = find(predicate, seq)
    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_find_with_truthy_non_boolean_predicate() -> None:
    seq: list[int] = [2, 4, 5, 6]
    result = find(lambda x: x % 2, seq)
    assert result == 5


def test_find_on_generator_and_stop_early() -> None:
    def bad_gen() -> Iterator[str]:
        yield "first"
        raise RuntimeError("should not be reached")

    assert find(lambda x: x == "first", bad_gen()) == "first"


def test_find_does_not_evaluate_rest() -> None:
    calls: list[str] = []

    def predicate(x: str) -> bool:
        calls.append(x)
        return x == "stop"

    seq: list[str] = ["go", "stop", "later"]
    result = find(predicate, seq)
    assert result == "stop"
    assert calls == ["go", "stop"]


def test_find_with_set_returns_first_iterated_element() -> None:
    data: set[str] = {"a", "b", "c"}
    result = find(lambda x: x in data, data)
    assert result in data


def test_find_none_predicate() -> None:
    seq: list[int] = [42, 43, 44]
    result = find(lambda x: True, seq)
    assert result == 42
