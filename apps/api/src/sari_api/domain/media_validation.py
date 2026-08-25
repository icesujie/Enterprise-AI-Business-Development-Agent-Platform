from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


class InvalidMediaError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidatedImage:
    mime_type: str
    extension: str
    width: int
    height: int


ALLOWED_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def validate_image(content: bytes, filename: str, declared_mime: str) -> ValidatedImage:
    extension = Path(filename).suffix.lower()
    expected_mime = ALLOWED_EXTENSIONS.get(extension)
    if expected_mime is None or declared_mime != expected_mime:
        raise InvalidMediaError("File extension and declared image type do not match.")
    if declared_mime == "image/png":
        width, height = _png_dimensions(content)
    elif declared_mime == "image/jpeg":
        width, height = _jpeg_dimensions(content)
    else:
        width, height = _webp_dimensions(content)
    if width <= 0 or height <= 0 or width > 50_000 or height > 50_000:
        raise InvalidMediaError("Image dimensions are invalid or exceed the safe limit.")
    return ValidatedImage(declared_mime, extension, width, height)


def _png_dimensions(content: bytes) -> tuple[int, int]:
    if (
        len(content) < 33
        or content[:8] != b"\x89PNG\r\n\x1a\n"
        or content[8:12] != b"\x00\x00\x00\x0d"
        or content[12:16] != b"IHDR"
    ):
        raise InvalidMediaError("The uploaded file is not a valid PNG image.")
    return struct.unpack(">II", content[16:24])


def _jpeg_dimensions(content: bytes) -> tuple[int, int]:
    if len(content) < 4 or content[:2] != b"\xff\xd8":
        raise InvalidMediaError("The uploaded file is not a valid JPEG image.")
    position = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while position + 4 <= len(content):
        if content[position] != 0xFF:
            position += 1
            continue
        marker = content[position + 1]
        position += 2
        if marker in {0xD8, 0xD9}:
            continue
        if position + 2 > len(content):
            break
        length = int.from_bytes(content[position : position + 2], "big")
        if length < 2 or position + length > len(content):
            break
        if marker in sof_markers and length >= 7:
            height = int.from_bytes(content[position + 3 : position + 5], "big")
            width = int.from_bytes(content[position + 5 : position + 7], "big")
            return width, height
        position += length
    raise InvalidMediaError("JPEG dimensions could not be validated.")


def _webp_dimensions(content: bytes) -> tuple[int, int]:
    if len(content) < 30 or content[:4] != b"RIFF" or content[8:12] != b"WEBP":
        raise InvalidMediaError("The uploaded file is not a valid WebP image.")
    chunk = content[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(content[24:27], "little")
        height = 1 + int.from_bytes(content[27:30], "little")
        return width, height
    if chunk == b"VP8L" and len(content) >= 25 and content[20] == 0x2F:
        bits = int.from_bytes(content[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8 " and len(content) >= 30 and content[23:26] == b"\x9d\x01\x2a":
        return (
            int.from_bytes(content[26:28], "little") & 0x3FFF,
            int.from_bytes(content[28:30], "little") & 0x3FFF,
        )
    raise InvalidMediaError("WebP dimensions could not be validated.")
