"""Scene management operations"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from .yaml_parser import UnityDocument, UnityObject
from .project import UnityProject
from ..utils.guid import generate_guid, generate_file_id, read_guid_from_meta
from ..utils.meta import create_scene_meta, delete_meta


class SceneManager:
    """Manages scene creation, editing, and object management"""

    def __init__(self, project: UnityProject):
        self.project = project

    def create(self, name: str, path: str = 'Assets/00_Scenes/') -> Path:
        """
        Create a new empty scene.

        Args:
            name: Scene name (without .unity extension)
            path: Directory path (default: Assets/00_Scenes/)

        Returns:
            Path to created scene
        """
        # Resolve path
        target_dir = self.project.resolve_path(path)
        target_dir.mkdir(parents=True, exist_ok=True)

        scene_path = target_dir / f'{name}.unity'

        if scene_path.exists():
            raise FileExistsError(f'Scene already exists: {scene_path}')

        # Create minimal scene with required headers
        content = _create_empty_scene_template()

        # Write file
        with open(scene_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Create .meta file
        create_scene_meta(str(scene_path))

        return scene_path

    def show(self, scene_path: str) -> Dict[str, Any]:
        """
        Display information about a scene.

        Args:
            scene_path: Path to scene file

        Returns:
            Dictionary with scene information
        """
        path = Path(scene_path)
        if not path.exists():
            raise FileNotFoundError(f'Scene not found: {scene_path}')

        doc = UnityDocument.load(str(path))

        info = {
            'name': path.stem,
            'gameobjects': [],
            'prefab_instances': [],
            'path': str(self.project.relative_path(path)),
        }

        # Collect GameObjects
        for obj in doc.find_by_type(1):  # class_id 1 = GameObject
            name = obj.get_property('m_Name')
            if name:
                info['gameobjects'].append(name)

        # Collect PrefabInstances
        for obj in doc.find_by_type(1001):  # class_id 1001 = PrefabInstance
            prefab = obj.get_property('m_Name') or 'Unknown'
            info['prefab_instances'].append(prefab)

        return info

    def add_object(
        self, scene_path: str, obj_name: str, components: Optional[List[str]] = None
    ) -> None:
        """
        Add a new GameObject to a scene.

        Args:
            scene_path: Path to scene file
            obj_name: Name of the new GameObject
            components: List of component types to add (optional)
        """
        path = Path(scene_path)
        if not path.exists():
            raise FileNotFoundError(f'Scene not found: {scene_path}')

        doc = UnityDocument.load(str(path))

        # Create GameObject
        gameobject_id = generate_file_id()
        transform_id = generate_file_id()

        gameobject_obj = UnityObject(
            class_id=1,
            file_id=gameobject_id,
            is_stripped=False,
            type_name='GameObject',
            raw_lines=_create_gameobject_template(obj_name, gameobject_id, transform_id),
        )

        transform_obj = UnityObject(
            class_id=4,
            file_id=transform_id,
            is_stripped=False,
            type_name='Transform',
            raw_lines=_create_transform_template(transform_id, gameobject_id),
        )

        doc.objects.append(gameobject_obj)
        doc.objects.append(transform_obj)

        # Add components if specified
        if components:
            for comp in components:
                comp_id = generate_file_id()
                comp_obj = UnityObject(
                    class_id=114,  # MonoBehaviour
                    file_id=comp_id,
                    is_stripped=False,
                    type_name=comp,
                    raw_lines=_create_component_template(comp, comp_id, gameobject_id),
                )
                doc.objects.append(comp_obj)
                _add_component_reference_to_gameobject(gameobject_obj, comp_id)

        doc.save(str(path))

    def add_prefab(
        self,
        scene_path: str,
        prefab_path: str,
        position: Tuple[float, float, float] = (0, 0, 0),
        obj_name: Optional[str] = None,
    ) -> None:
        """
        Add a prefab instance to a scene.

        Args:
            scene_path: Path to scene file
            prefab_path: Path to prefab file
            position: Position as (x, y, z) tuple
            obj_name: Optional custom name for the instance
        """
        scene_file = Path(scene_path)
        if not scene_file.exists():
            raise FileNotFoundError(f'Scene not found: {scene_path}')

        prefab_file = Path(prefab_path)
        if not prefab_file.exists():
            raise FileNotFoundError(f'Prefab not found: {prefab_path}')

        # Get prefab GUID
        meta_path = str(prefab_file) + '.meta'
        prefab_guid = read_guid_from_meta(meta_path)
        if not prefab_guid:
            raise ValueError(f'Could not find GUID for prefab: {prefab_path}')

        doc = UnityDocument.load(str(scene_file))

        # Create PrefabInstance
        instance_id = generate_file_id()

        prefab_instance = UnityObject(
            class_id=1001,
            file_id=instance_id,
            is_stripped=False,
            type_name='PrefabInstance',
            raw_lines=_create_prefab_instance_template(
                instance_id, prefab_guid, position, obj_name
            ),
        )

        doc.objects.append(prefab_instance)
        doc.save(str(scene_file))

    def remove_object(self, scene_path: str, obj_name: str) -> None:
        """
        Remove a GameObject or PrefabInstance from a scene.

        Args:
            scene_path: Path to scene file
            obj_name: Name of the object to remove
        """
        path = Path(scene_path)
        if not path.exists():
            raise FileNotFoundError(f'Scene not found: {scene_path}')

        doc = UnityDocument.load(str(path))

        # Find and remove object
        to_remove = []
        for obj in doc.objects:
            if obj.get_property('m_Name') == obj_name:
                to_remove.append(obj)

        if not to_remove:
            raise ValueError(f'Object not found in scene: {obj_name}')

        for obj in to_remove:
            doc.objects.remove(obj)

        doc.save(str(path))

    def set_property(
        self,
        scene_path: str,
        obj_name: str,
        component: str,
        field: str,
        value: str,
    ) -> None:
        """
        Set a property on an object's component.

        Args:
            scene_path: Path to scene file
            obj_name: Name of the GameObject
            component: Component type name
            field: Field name
            value: New value
        """
        path = Path(scene_path)
        if not path.exists():
            raise FileNotFoundError(f'Scene not found: {scene_path}')

        doc = UnityDocument.load(str(path))

        # Find object
        gameobject = None
        for obj in doc.objects:
            if obj.class_id == 1 and obj.get_property('m_Name') == obj_name:
                gameobject = obj
                break

        if not gameobject:
            raise ValueError(f'GameObject not found: {obj_name}')

        # Find component
        component_obj = None
        for obj in doc.objects:
            if obj.type_name == component:
                # Check if this component belongs to our gameobject
                if obj.get_property('m_GameObject') and str(gameobject.file_id) in obj.get_property('m_GameObject'):
                    component_obj = obj
                    break

        if not component_obj:
            raise ValueError(f'Component not found: {component}')

        if not component_obj.set_property(field, value):
            raise ValueError(f'Property not found: {field}')

        doc.save(str(path))

    def list_all(self, path: str = '') -> List[str]:
        """
        List all scenes in a directory.

        Args:
            path: Relative path to search (default: entire project)

        Returns:
            List of scene paths
        """
        if path:
            search_dir = self.project.resolve_path(path)
        else:
            search_dir = self.project.root / 'Assets'

        scenes = []
        if search_dir.exists():
            for scene in search_dir.rglob('*.unity'):
                rel_path = self.project.relative_path(scene)
                scenes.append(rel_path)

        return sorted(scenes)


def _create_empty_scene_template() -> str:
    """Create a minimal scene YAML content with required headers"""
    return """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {fileID: 0}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 9
  m_Fog: 0
  m_FogColor: {r: 0.5, g: 0.5, b: 0.5, a: 1}
  m_FogMode: 0
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {r: 0.212, g: 0.227, b: 0.259, a: 1}
  m_AmbientEquatorColor: {r: 0.114, g: 0.125, b: 0.133, a: 1}
  m_AmbientGroundColor: {r: 0.047, g: 0.043, b: 0.035, a: 1}
  m_AmbientIntensity: 1
  m_AmbientMode: 0
  m_SubtractiveShadowColor: {r: 0.42, g: 0.478, b: 0.627, a: 1}
  m_SkyboxMaterial: {fileID: 0}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {fileID: 0}
  m_SpotCookie: {fileID: 0}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {fileID: 0}
  m_Sun: {fileID: 0}
  m_IndirectSpecularColor: {r: 0, g: 0, b: 0, a: 1}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 12
  m_GIWorkflowMode: 1
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 1
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 1
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAmbientOcclusion: 0
    m_Padding: 2
    m_LightmapParameters: {fileID: 0}
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_FinalGather: 0
    m_FinalGatherFiltering: 1
    m_FinalGatherRayCount: 256
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 500
    m_PVRBounces: 2
    m_PVREnvironmentSampleCount: 500
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 2
    m_PVRDenoiserTypeDirect: 0
    m_PVRDenoiserTypeIndirect: 0
    m_PVRDenoiserTypeAO: 0
    m_PVRFilterTypeDirect: 0
    m_PVRFilterTypeIndirect: 0
    m_PVRFilterTypeAO: 0
    m_PVREnvironmentMIS: 0
    m_PVRCulling: 1
    m_PVRFilteringGaussRadiusDirect: 1
    m_PVRFilteringGaussRadiusIndirect: 5
    m_PVRFilteringGaussRadiusAO: 2
    m_PVRFilteringAtrousPositionSigmaDirect: 0.5
    m_PVRFilteringAtrousPositionSigmaIndirect: 2
    m_PVRFilteringAtrousPositionSigmaAO: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {fileID: 0}
  m_LightingSettings: {fileID: 0}
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 2
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    accuratePlacement: 0
    maxJobWorkers: 0
    preserveTilesOutsideBounds: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {fileID: 0}
"""


def _create_gameobject_template(name: str, gameobject_id: int, transform_id: int) -> list:
    """Create template lines for a GameObject"""
    return [
        'GameObject:',
        '  m_ObjectHideFlags: 0',
        '  m_CorrespondingSourceObject: {fileID: 0}',
        '  m_PrefabInstance: {fileID: 0}',
        '  m_PrefabAsset: {fileID: 0}',
        '  serializedVersion: 6',
        '  m_Component:',
        f'  - component: {{fileID: {transform_id}}}',
        '  m_Layer: 0',
        f'  m_Name: {name}',
        '  m_TagString: Untagged',
        '  m_Icon: {fileID: 0}',
        '  m_NavMeshLayer: 0',
        '  m_StaticEditorFlags: 0',
        '  m_IsActive: 1',
    ]


def _create_transform_template(transform_id: int, gameobject_id: int) -> list:
    """Create template lines for a Transform"""
    return [
        'Transform:',
        '  m_ObjectHideFlags: 0',
        '  m_CorrespondingSourceObject: {fileID: 0}',
        '  m_PrefabInstance: {fileID: 0}',
        '  m_PrefabAsset: {fileID: 0}',
        f'  m_GameObject: {{fileID: {gameobject_id}}}',
        '  m_Enabled: 1',
        '  m_EditorHideFlags: 0',
        '  m_RotationOrder: 4',
        '  m_LocalRotation:',
        '    serializedVersion: 2',
        '    x: 0',
        '    y: 0',
        '    z: 0',
        '    w: 1',
        '  m_LocalPosition:',
        '    x: 0',
        '    y: 0',
        '    z: 0',
        '  m_LocalScale:',
        '    x: 1',
        '    y: 1',
        '    z: 1',
        '  m_ConstrainProportionsScale: 0',
        '  m_Children: []',
        '  m_Father: {fileID: 0}',
        '  m_RootOrder: 0',
        '  m_LocalEulerAnglesHint:',
        '    x: 0',
        '    y: 0',
        '    z: 0',
    ]


def _create_component_template(comp: str, comp_id: int, gameobject_id: int) -> list:
    """Create template lines for a component"""
    return [
        f'{comp}:',
        '  m_ObjectHideFlags: 0',
        '  m_CorrespondingSourceObject: {fileID: 0}',
        '  m_PrefabInstance: {fileID: 0}',
        '  m_PrefabAsset: {fileID: 0}',
        f'  m_GameObject: {{fileID: {gameobject_id}}}',
        '  m_Enabled: 1',
    ]


def _create_prefab_instance_template(
    instance_id: int, prefab_guid: str, position: Tuple[float, float, float], obj_name: Optional[str]
) -> list:
    """Create template lines for a PrefabInstance"""
    lines = [
        'PrefabInstance:',
        '  m_ObjectHideFlags: 0',
        '  serializedVersion: 2',
        '  m_Modification:',
        '    serializedVersion: 3',
        '    m_TransformParent: {fileID: 0}',
        '    m_Modifications: []',
        '    m_RemovedComponents: []',
        '    m_RemovedGameObjects: []',
        '    m_AddedGameObjects: []',
        '    m_AddedComponents: []',
        f'  m_SourcePrefab: {{fileID: 100100000, guid: {prefab_guid}, type: 3}}',
    ]
    return lines


def _add_component_reference_to_gameobject(gameobject: UnityObject, component_id: int) -> None:
    """Add a component reference to GameObject's m_Component list"""
    for i, line in enumerate(gameobject.raw_lines):
        if line.strip().startswith('m_Component:'):
            # Find the place to insert
            j = i + 1
            while j < len(gameobject.raw_lines) and gameobject.raw_lines[j].strip().startswith('- component:'):
                j += 1
            gameobject.raw_lines.insert(j, f'  - component: {{fileID: {component_id}}}')
            return
