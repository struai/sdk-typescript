"""Shared upload helpers for multipart PDF endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

Uploadable = Union[str, Path, bytes, BinaryIO]
PreparedUpload = Tuple[dict, Optional[BinaryIO]]


def _prepare_file(file: Uploadable) -> PreparedUpload:
    if isinstance(file, (str, Path)):
        path = Path(file)
        handle = open(path, "rb")
        return {"file": (path.name, handle, "application/pdf")}, handle
    if isinstance(file, bytes):
        return {"file": ("document.pdf", file, "application/pdf")}, None

    name = getattr(file, "name", "document.pdf")
    if hasattr(name, "split"):
        name = Path(name).name
    return {"file": (name, file, "application/pdf")}, None
