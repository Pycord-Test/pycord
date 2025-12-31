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

import random
import string
from typing import Any

import pytest

import discord
from discord import components

random.seed(42)


def random_string(
    min_len, max_len, spaces: bool = True, punctuation: bool = True, separators: tuple[str, ...] = ("-", "_")
):
    chars = string.ascii_letters + string.digits
    if spaces:
        chars += " "
    if punctuation:
        chars += string.punctuation
    if separators:
        chars += "".join(separators)
    return "".join(random.choices(chars, k=random.randint(min_len, max_len)))


def generate_test_user_select_modal(
    *,
    modal_title: str,
    modal_custom_id: str,
    label_title: str,
    label_description: str,
    select_default_user_id: int,
    select_custom_id: str,
):
    MODAL: components.Modal = components.Modal(
        components.Label(
            components.UserSelect(
                default_values=[components.DefaultSelectOption(id=select_default_user_id, type="user")],
                custom_id=select_custom_id,
            ),
            label=label_title,
            description=label_description,
        ),
        title=modal_title,
        custom_id=modal_custom_id,
    )
    EXPECTED_PAYLOAD = {
        "title": modal_title,  # 1-45 characters
        "custom_id": modal_custom_id,  # 1-100 characters
        "components": [
            {
                "type": 18,
                "label": label_title,  # 1-45 characters
                "description": label_description,  # 1-100 characters
                "id": None,
                "component": {
                    "type": 5,
                    "custom_id": select_custom_id,  # int64
                    "default_values": [
                        {
                            "id": select_default_user_id,  # int64
                            "type": "user",
                        }
                    ],
                    "id": None,
                    "max_values": 1,
                    "min_values": 1,
                },
            }
        ],
    }

    return MODAL, EXPECTED_PAYLOAD


USER_SELECT_MODAL_CASES = [
    generate_test_user_select_modal(
        modal_title=random_string(1, 45),
        modal_custom_id=random_string(1, 100),
        label_title=random_string(1, 45),
        label_description=random_string(1, 100),
        select_default_user_id=random.randint(100000000000000000, 999999999999999999),
        select_custom_id=random_string(1, 100),
    )
    for _ in range(10)
]


@pytest.mark.parametrize(
    ("modal", "payload"),
    USER_SELECT_MODAL_CASES,
)
def test_user_select_modal_to_dict(
    modal: components.Modal,
    payload: dict[Any, Any],
):
    # Test that the modal generates the expected payload
    assert modal.to_dict() == payload


def generate_test_text_input_modal(
    *,
    modal_title: str,
    modal_custom_id: str,
    label_title: str,
    label_description: str,
    text_input_custom_id: str,
    text_input_value: str,
    text_input_placeholder: str,
    text_input_min_length: int,
    text_input_max_length: int,
    text_input_required: bool,
    text_input_multiline: bool,
):
    MODAL: components.Modal = components.Modal(
        components.Label(
            components.TextInput(
                custom_id=text_input_custom_id,
                value=text_input_value,
                placeholder=text_input_placeholder,
                min_length=text_input_min_length,
                max_length=text_input_max_length,
                required=text_input_required,
                style=discord.TextInputStyle.paragraph if text_input_multiline else discord.TextInputStyle.short,
            ),
            label=label_title,
            description=label_description,
        ),
        title=modal_title,
        custom_id=modal_custom_id,
    )
    EXPECTED_PAYLOAD = {
        "title": modal_title,  # 1-45 characters
        "custom_id": modal_custom_id,  # 1-100 characters
        "components": [
            {
                "type": 18,
                "label": label_title,  # 1-45 characters
                "description": label_description,  # 1-100 characters
                "id": None,
                "component": {
                    "type": 4,
                    "custom_id": text_input_custom_id,  # 1-100 characters
                    "value": text_input_value,  # 0-4000 characters
                    "placeholder": text_input_placeholder,  # 0-100 characters
                    "min_length": text_input_min_length,  # 0-4000
                    "max_length": text_input_max_length,  # 1-4000
                    "style": 2 if text_input_multiline else 1,
                    "id": None,
                },
            }
        ],
    }
    if not text_input_required:
        EXPECTED_PAYLOAD["components"][0]["component"]["required"] = False  # pyright: ignore[reportArgumentType]

    return MODAL, EXPECTED_PAYLOAD


TEXT_INPUT_MODAL_CASES = [
    generate_test_text_input_modal(
        modal_title=random_string(1, 45),
        modal_custom_id=random_string(1, 100),
        label_title=random_string(1, 45),
        label_description=random_string(1, 100),
        text_input_custom_id=random_string(1, 100),
        text_input_value=random_string(1, 4000),
        text_input_placeholder=random_string(1, 100),
        text_input_min_length=random.randint(0, 4000),
        text_input_max_length=random.randint(1, 4000),
        text_input_required=random.choice([True, False]),
        text_input_multiline=random.choice([True, False]),
    )
    for _ in range(10)
]


@pytest.mark.parametrize(
    ("modal", "payload"),
    TEXT_INPUT_MODAL_CASES,
)
def test_text_input_modal_to_dict(
    modal: components.Modal,
    payload: dict[Any, Any],
):
    # Test that the modal generates the expected payload
    assert modal.to_dict() == payload
