"""Prefab management operations"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from .yaml_parser import UnityDocument, UnityObject
from .project import UnityProject
from ..utils.guid import generate_guid, generate_file_id
from ..utils.meta import create_prefab_meta, delete_meta


# Component class IDs in Unity
COMPONENT_CLASS_IDS = {
    'Transform': 4,
    'RectTransform': 224,
    'Rigidbody': 54,
    'Rigidbody2D': 50,
    'BoxCollider': 65,
    'BoxCollider2D': 61,
    'SpriteRenderer': 212,
    'Animator': 95,
    'AudioSource': 82,
    'ParticleSystem': 198,
    'Canvas': 223,
    'GraphicRaycaster': 120,
    'CanvasGroup': 225,
    'Image': 225,
    'Text': 114,  # MonoBehaviour with specific script
}


class PrefabManager:
    """Manages prefab creation, editing, and deletion"""

    def __init__(self, project: UnityProject):
        self.project = project

    def create(self, name: str, path: str = 'Assets/Resources/Prefabs/') -> Path:
        """
        Create a new empty prefab with GameObject and Transform.

        Args:
            name: Prefab name (without .prefab extension)
            path: Directory path (default: Assets/Resources/Prefabs/)

        Returns:
            Path to created prefab
        """
        # Resolve path
        target_dir = self.project.resolve_path(path)
        target_dir.mkdir(parents=True, exist_ok=True)

        prefab_path = target_dir / f'{name}.prefab'

        if prefab_path.exists():
            raise FileExistsError(f'Prefab already exists: {prefab_path}')

        # Generate IDs
        gameobject_id = generate_file_id()
        transform_id = generate_file_id()

        # Create prefab content
        content = _create_empty_prefab_template(name, gameobject_id, transform_id)

        # Write file
        with open(prefab_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Create .meta file
        create_prefab_meta(str(prefab_path))

        return prefab_path

    def show(self, prefab_path: str) -> Dict[str, Any]:
        """
        Display information about a prefab.

        Args:
            prefab_path: Path to prefab file

        Returns:
            Dictionary with prefab information
        """
        path = Path(prefab_path)
        if not path.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        doc = UnityDocument.load(str(path))

        # Find main GameObject
        gameobjects = doc.find_by_type(1)  # class_id 1 = GameObject
        if not gameobjects:
            return {'name': 'Unknown', 'components': []}

        info = {
            'name': gameobjects[0].get_property('m_Name'),
            'components': [],
            'children': [],
            'path': str(self.project.relative_path(path)),
        }

        # List components attached to main GameObject
        for obj in doc.objects:
            if not obj.is_stripped:
                # Simple type detection
                if obj.class_id in [4, 224]:  # Transform types
                    info['components'].append(obj.type_name)
                elif obj.class_id in [50, 61, 212, 95]:  # Common components
                    info['components'].append(obj.type_name)
                elif obj.class_id == 114:  # MonoBehaviour
                    info['components'].append('MonoBehaviour')

        return info

    def add_component(
        self, prefab_path: str, component: str, properties: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Add a component to a prefab.

        Args:
            prefab_path: Path to prefab file
            component: Component type name (e.g., 'Rigidbody2D')
            properties: Optional component properties to set
        """
        path = Path(prefab_path)
        if not path.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        doc = UnityDocument.load(str(path))

        # Get the GameObject (first object, class_id=1)
        gameobject = doc.find_by_type(1)[0]

        # Create new component
        component_id = generate_file_id()
        class_id = COMPONENT_CLASS_IDS.get(component, 114)

        # Create component object
        comp_lines = _create_component_template(component, component_id, gameobject.file_id)
        comp_obj = UnityObject(
            class_id=class_id,
            file_id=component_id,
            is_stripped=False,
            type_name=component,
            raw_lines=comp_lines,
        )

        doc.objects.append(comp_obj)

        # Add reference to GameObject's m_Component list
        _add_component_reference_to_gameobject(
            gameobject, component_id, class_id
        )

        doc.save(str(path))

    def remove_component(self, prefab_path: str, component: str) -> None:
        """
        Remove a component from a prefab.

        Args:
            prefab_path: Path to prefab file
            component: Component type name
        """
        path = Path(prefab_path)
        if not path.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        doc = UnityDocument.load(str(path))

        # Find and remove component object
        to_remove = [obj for obj in doc.objects if obj.type_name == component and not obj.is_stripped]

        if not to_remove:
            raise ValueError(f'Component not found: {component}')

        for comp in to_remove:
            doc.objects.remove(comp)

        # Remove references from GameObject
        gameobject = doc.find_by_type(1)[0]
        for comp in to_remove:
            _remove_component_reference_from_gameobject(gameobject, comp.file_id)

        doc.save(str(path))

    def set_property(
        self, prefab_path: str, component: str, field: str, value: str
    ) -> None:
        """
        Set a property on a component.

        Args:
            prefab_path: Path to prefab file
            component: Component type name
            field: Field name (may include nested properties like 'x' for Vector3.x)
            value: New value
        """
        path = Path(prefab_path)
        if not path.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        doc = UnityDocument.load(str(path))

        # Find component
        components = [obj for obj in doc.objects if obj.type_name == component]
        if not components:
            raise ValueError(f'Component not found: {component}')

        component_obj = components[0]
        if not component_obj.set_property(field, value):
            raise ValueError(f'Property not found: {field}')

        doc.save(str(path))

    def delete(self, prefab_path: str) -> None:
        """
        Delete a prefab and its .meta file.

        Args:
            prefab_path: Path to prefab file
        """
        path = Path(prefab_path)
        if not path.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        path.unlink()
        delete_meta(str(path))

    def copy(self, src: str, dst: str) -> Path:
        """
        Copy a prefab with a new GUID.

        Args:
            src: Source prefab path
            dst: Destination prefab path

        Returns:
            Path to copied prefab
        """
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f'Source prefab not found: {src}')

        dst_path = Path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy content
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()

        with open(dst_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Create new .meta file with new GUID
        create_prefab_meta(str(dst_path))

        return dst_path

    def rename(self, src: str, new_name: str) -> Path:
        """
        Rename a prefab (keeping its GUID).

        Args:
            src: Source prefab path
            new_name: New prefab name (without extension)

        Returns:
            Path to renamed prefab
        """
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f'Prefab not found: {src}')

        dst_path = src_path.parent / f'{new_name}.prefab'

        # Move file
        src_path.rename(dst_path)

        # Move .meta file (preserving GUID)
        meta_src = Path(str(src_path) + '.meta')
        meta_dst = Path(str(dst_path) + '.meta')
        if meta_src.exists():
            meta_src.rename(meta_dst)

        # Update GameObject name in the prefab
        doc = UnityDocument.load(str(dst_path))
        gameobject = doc.find_by_type(1)[0]
        gameobject.set_property('m_Name', new_name)
        doc.save(str(dst_path))

        return dst_path

    def list_all(self, path: str = '') -> List[str]:
        """
        List all prefabs in a directory.

        Args:
            path: Relative path to search (default: entire project)

        Returns:
            List of prefab paths
        """
        if path:
            search_dir = self.project.resolve_path(path)
        else:
            search_dir = self.project.root / 'Assets'

        prefabs = []
        if search_dir.exists():
            for prefab in search_dir.rglob('*.prefab'):
                rel_path = self.project.relative_path(prefab)
                prefabs.append(rel_path)

        return sorted(prefabs)


def _create_empty_prefab_template(
    name: str, gameobject_id: int, transform_id: int
) -> str:
    """Create a minimal prefab YAML content"""
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &{gameobject_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {transform_id}}}
  m_Layer: 0
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{transform_id}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gameobject_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_RotationOrder: 4
  m_LocalRotation:
    serializedVersion: 2
    x: 0
    y: 0
    z: 0
    w: 1
  m_LocalPosition:
    x: 0
    y: 0
    z: 0
  m_LocalScale:
    x: 1
    y: 1
    z: 1
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_RootOrder: 0
  m_LocalEulerAnglesHint:
    x: 0
    y: 0
    z: 0
"""


def _create_component_template(
    component: str, component_id: int, gameobject_id: int
) -> list:
    """Create template lines for a component"""
    lines = [
        f'{component}:',
        '  m_ObjectHideFlags: 0',
        '  m_CorrespondingSourceObject: {fileID: 0}',
        '  m_PrefabInstance: {fileID: 0}',
        '  m_PrefabAsset: {fileID: 0}',
        f'  m_GameObject: {{fileID: {gameobject_id}}}',
        '  m_Enabled: 1',
    ]
    return lines


def _add_component_reference_to_gameobject(
    gameobject: UnityObject, component_id: int, class_id: int
) -> None:
    """Add a component reference to GameObject's m_Component list"""
    # Find or create m_Component list
    found = False
    for i, line in enumerate(gameobject.raw_lines):
        if line.strip().startswith('m_Component:'):
            found = True
            # Insert after this line
            if i + 1 < len(gameobject.raw_lines) and gameobject.raw_lines[i + 1].strip().startswith('- component:'):
                # Already has components, insert after last one
                j = i + 1
                while j < len(gameobject.raw_lines) and gameobject.raw_lines[j].strip().startswith('- component:'):
                    j += 1
                gameobject.raw_lines.insert(j, f'- component: {{fileID: {component_id}}}')
            else:
                # Empty list, add first component
                gameobject.raw_lines.insert(i + 1, f'- component: {{fileID: {component_id}}}')
            break

    if not found:
        # No m_Component list, need to add it (shouldn't happen in valid prefab)
        gameobject.raw_lines.append('  m_Component:')
        gameobject.raw_lines.append(f'  - component: {{fileID: {component_id}}}')


def _remove_component_reference_from_gameobject(
    gameobject: UnityObject, component_id: int
) -> None:
    """Remove a component reference from GameObject's m_Component list"""
    gameobject.raw_lines = [
        line for line in gameobject.raw_lines
        if f'fileID: {component_id}' not in line
    ]
