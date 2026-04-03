"""GUID and fileID utilities for Unity assets"""

import uuid
import random
from typing import Optional


def generate_guid() -> str:
    """
    Generate a Unity-compatible GUID (32-char lowercase hex).

    Returns:
        str: 32-character lowercase hexadecimal string
        Example: '73d744cee73d2f54f9d8b51c2b5b1acf'
    """
    return uuid.uuid4().hex


def generate_file_id() -> int:
    """
    Generate a Unity-compatible fileID (64-bit signed integer).

    fileID can be positive or negative. This generates positive values.

    Returns:
        int: Random 64-bit positive integer
    """
    return random.randint(10_000_000_000_000_000, 9_223_372_036_854_775_807)


def read_guid_from_meta(meta_path: str) -> Optional[str]:
    """
    Extract GUID from a .meta file.

    Args:
        meta_path: Path to .meta file

    Returns:
        GUID string if found, None otherwise
    """
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('guid:'):
                    return line.split(':')[1].strip()
    except (FileNotFoundError, IOError):
        return None
    return None
