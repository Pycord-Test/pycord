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

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import override

from ..enums import ComponentType
from ..types.component_types import FileUpload as FileUploadPayload
from .component import Component, ModalComponentMixin

if TYPE_CHECKING:
    from typing_extensions import Self


class FileUpload(ModalComponentMixin[FileUploadPayload], Component[FileUploadPayload]):
    """Represents a File Upload Component.

    This component displays a file upload box in a :class:`Modal`.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.file_upload`]
        The type of component.
    custom_id: :class:`str`
        The custom ID of the file upload component that gets received during an interaction.
    min_values: :class:`int`
        The minimum number of files that must be uploaded.
    max_values: :class:`int`
        The maximum number of files that can be uploaded.
    required: :class:`bool`
        Whether the file upload is required to submit the modal.
    id: :class:`int` | :data:`None`
        The section's ID.

    Parameters
    ----------
    id:
        The component's ID. If not provided by the user, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = (
        "file",
        "spoiler",
        "name",
        "size",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.file_upload] = ComponentType.file_upload  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        custom_id: str,
        id: int | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = True,
    ) -> None:
        self.custom_id: str = custom_id
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.required: bool = required
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: FileUploadPayload) -> Self:
        return cls(
            custom_id=payload["custom_id"],
            id=payload["id"],
            min_values=payload.get("min_values", 1),
            max_values=payload.get("max_values", 1),
            required=payload.get("required", True),
        )

    @override
    def to_dict(self, modal: bool = True) -> FileUploadPayload:
        payload: FileUploadPayload = {
            "type": int(self.type),
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "required": self.required,
            "id": self.id,
        }
        return payload
