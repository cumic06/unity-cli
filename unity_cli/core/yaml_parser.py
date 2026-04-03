"""
Unity YAML file parser and writer.

Handles Unity's custom YAML format with !u! tags and multiple documents.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class UnityObject:
    """Represents a single object in a Unity YAML document"""

    class_id: int  # !u! number (1=GameObject, 4=Transform, 114=MonoBehaviour, etc.)
    file_id: int  # & number (64-bit signed integer)
    is_stripped: bool  # Has 'stripped' keyword
    type_name: str  # First line type (GameObject, Transform, etc.)
    raw_lines: List[str]  # Original lines for modification

    def get_property(self, prop_name: str) -> Optional[str]:
        """Get a property value from this object"""
        pattern = rf'^\s+{re.escape(prop_name)}:\s*(.+)$'
        for line in self.raw_lines:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        return None

    def set_property(self, prop_name: str, value: str) -> bool:
        """Set a property value. Returns True if modified."""
        pattern = rf'^(\s+){re.escape(prop_name)}:\s*(.+)$'
        for i, line in enumerate(self.raw_lines):
            match = re.match(pattern, line)
            if match:
                indent = match.group(1)
                self.raw_lines[i] = f'{indent}{prop_name}: {value}'
                return True
        return False


class UnityDocument:
    """Represents a complete Unity YAML file (multiple documents)"""

    def __init__(self, objects: List[UnityObject]):
        self.objects = objects

    @classmethod
    def load(cls, filepath: str) -> 'UnityDocument':
        """
        Load and parse a Unity YAML file.

        Args:
            filepath: Path to .prefab, .unity, or other Unity YAML file

        Returns:
            UnityDocument instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.splitlines()
        objects = []

        # Pattern: --- !u!<ClassID> &<FileID> [stripped]
        doc_pattern = re.compile(
            r'^---\s+!u!(\d+)\s+&(-?\d+)(\s+stripped)?'
        )

        current_header = None
        current_lines = []

        for line in lines:
            match = doc_pattern.match(line)
            if match:
                # Save previous object
                if current_header:
                    obj = _build_unity_object(current_header, current_lines)
                    objects.append(obj)

                # Start new object
                current_header = match
                current_lines = []
            elif current_header is not None:
                current_lines.append(line)

        # Don't forget the last object
        if current_header:
            obj = _build_unity_object(current_header, current_lines)
            objects.append(obj)

        return cls(objects)

    def save(self, filepath: str) -> None:
        """
        Save the document back to a Unity YAML file.

        Args:
            filepath: Path to save to
        """
        lines = []

        # Header must be exactly this format
        lines.append('%YAML 1.1')
        lines.append('%TAG !u! tag:unity3d.com,2011:')

        for obj in self.objects:
            stripped = ' stripped' if obj.is_stripped else ''
            lines.append(
                f'--- !u!{obj.class_id} &{obj.file_id}{stripped}'
            )
            lines.extend(obj.raw_lines)

        # Unity uses LF line endings and UTF-8 without BOM
        content = '\n'.join(lines) + '\n'

        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    def find_by_type(self, class_id: int) -> List[UnityObject]:
        """Find all objects with a specific class ID"""
        return [obj for obj in self.objects if obj.class_id == class_id]

    def find_by_file_id(self, file_id: int) -> Optional[UnityObject]:
        """Find a single object by file ID"""
        for obj in self.objects:
            if obj.file_id == file_id:
                return obj
        return None

    def find_by_type_name(self, type_name: str) -> List[UnityObject]:
        """Find all objects with a specific type name"""
        return [obj for obj in self.objects if obj.type_name == type_name]

    def find_component_by_script(self, guid: str) -> Optional[UnityObject]:
        """Find MonoBehaviour component by script GUID"""
        for obj in self.find_by_type(114):  # 114 = MonoBehaviour
            for line in obj.raw_lines:
                if f'guid: {guid}' in line:
                    return obj
        return None


def _build_unity_object(
    header_match: re.Match, lines: List[str]
) -> UnityObject:
    """Build a UnityObject from a header match and content lines"""
    class_id = int(header_match.group(1))
    file_id = int(header_match.group(2))
    is_stripped = bool(header_match.group(3))

    # Type name is the first non-empty line (without trailing colon)
    type_name = ''
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            type_name = stripped.rstrip(':')
            break

    return UnityObject(
        class_id=class_id,
        file_id=file_id,
        is_stripped=is_stripped,
        type_name=type_name,
        raw_lines=lines,
    )


def extract_references(text: str) -> tuple[List[int], List[tuple[int, str, int]]]:
    """
    Extract local and external references from text.

    Returns:
        (local_file_ids, external_refs_list)
        external_refs_list items: (fileID, guid, type)
    """
    local_pattern = re.compile(r'\{fileID:\s*(-?\d+)\}')
    external_pattern = re.compile(
        r'\{fileID:\s*(-?\d+),\s*guid:\s*([0-9a-f]{32}),\s*type:\s*(\d+)\}'
    )

    local_refs = [int(m.group(1)) for m in local_pattern.finditer(text)]
    external_refs = [
        (int(m.group(1)), m.group(2), int(m.group(3)))
        for m in external_pattern.finditer(text)
    ]

    return local_refs, external_refs
