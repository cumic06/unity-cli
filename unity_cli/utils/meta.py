"""Utilities for managing Unity .meta files"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from .guid import generate_guid


def create_prefab_meta(prefab_path: str) -> str:
    """
    Create a .meta file for a prefab and return the GUID.

    Args:
        prefab_path: Path to the prefab file

    Returns:
        Generated GUID
    """
    meta_path = Path(prefab_path).with_suffix(prefab_path.suffix + '.meta')
    new_guid = generate_guid()

    meta_content = f"""fileFormatVersion: 2
guid: {new_guid}
PrefabImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""

    with open(meta_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(meta_content)

    return new_guid


def create_scene_meta(scene_path: str) -> str:
    """
    Create a .meta file for a scene and return the GUID.

    Args:
        scene_path: Path to the scene file

    Returns:
        Generated GUID
    """
    meta_path = Path(scene_path).with_suffix('.unity.meta')
    new_guid = generate_guid()

    meta_content = f"""fileFormatVersion: 2
guid: {new_guid}
DefaultImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""

    with open(meta_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(meta_content)

    return new_guid


def read_meta(filepath: str) -> Dict[str, Any]:
    """
    Parse a .meta file and return its contents as a dict.

    Args:
        filepath: Path to .meta file

    Returns:
        Dictionary with 'guid' and other metadata
    """
    result = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
    except (FileNotFoundError, IOError):
        return {}

    return result


def delete_meta(filepath: str) -> bool:
    """
    Delete a .meta file associated with an asset.

    Args:
        filepath: Path to the asset file (not the .meta file)

    Returns:
        True if deleted successfully, False otherwise
    """
    meta_path = Path(filepath).with_suffix(Path(filepath).suffix + '.meta')
    try:
        if meta_path.exists():
            meta_path.unlink()
            return True
    except (OSError, IOError):
        return False
    return False
