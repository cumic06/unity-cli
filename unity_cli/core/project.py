"""Unity project discovery and path resolution"""

from pathlib import Path
from typing import Optional, List
from ..utils.guid import read_guid_from_meta


class UnityProject:
    """Represents a Unity project and provides path utilities"""

    def __init__(self, root: Path):
        """
        Initialize a UnityProject.

        Args:
            root: Project root directory (parent of Assets/)
        """
        if not (root / 'Assets').exists():
            raise ValueError(f'No Assets folder found in {root}')

        self.root = root

    @classmethod
    def find(cls, start_path: str = '.') -> 'UnityProject':
        """
        Discover a Unity project by searching upward for Assets/ folder.

        Args:
            start_path: Starting directory for search (default: current directory)

        Returns:
            UnityProject instance

        Raises:
            RuntimeError: If no Unity project found
        """
        current = Path(start_path).resolve()

        while True:
            if (current / 'Assets').exists():
                return cls(current)

            parent = current.parent
            if parent == current:
                # Reached root directory
                raise RuntimeError(
                    f'No Unity project found from {start_path}. '
                    'Make sure you are in a Unity project directory.'
                )
            current = parent

    def resolve_path(self, partial: str) -> Path:
        """
        Resolve a partial path to an absolute path within the project.

        Args:
            partial: Partial path (e.g., "Prefabs/Monster" or "Assets/Resources/Prefabs/Monster")

        Returns:
            Absolute Path object
        """
        # Remove 'Assets/' prefix if present
        if partial.startswith('Assets/') or partial.startswith('Assets\\'):
            partial = partial[7:]

        # Normalize path separators
        partial = partial.replace('\\', '/')

        return self.root / 'Assets' / partial

    def list_prefabs(self, pattern: str = '**/*.prefab') -> List[Path]:
        """
        List all prefab files in the project.

        Args:
            pattern: Glob pattern (default: all prefabs)

        Returns:
            List of prefab paths
        """
        assets = self.root / 'Assets'
        if not assets.exists():
            return []
        return list(assets.glob(pattern))

    def list_scenes(self, pattern: str = '**/*.unity') -> List[Path]:
        """
        List all scene files in the project.

        Args:
            pattern: Glob pattern (default: all scenes)

        Returns:
            List of scene paths
        """
        assets = self.root / 'Assets'
        if not assets.exists():
            return []
        return list(assets.glob(pattern))

    def get_script_guid(self, script_name: str) -> Optional[str]:
        """
        Find a C# script by name and return its GUID.

        Args:
            script_name: Script name (with or without .cs extension)

        Returns:
            GUID string if found, None otherwise
        """
        if not script_name.endswith('.cs'):
            script_name += '.cs'

        assets = self.root / 'Assets'
        for cs_file in assets.rglob(script_name):
            meta_path = str(cs_file) + '.meta'
            guid = read_guid_from_meta(meta_path)
            if guid:
                return guid

        return None

    def get_prefab_guid(self, prefab_name: str) -> Optional[str]:
        """
        Find a prefab by name and return its GUID.

        Args:
            prefab_name: Prefab name (with or without .prefab extension)

        Returns:
            GUID string if found, None otherwise
        """
        if not prefab_name.endswith('.prefab'):
            prefab_name += '.prefab'

        assets = self.root / 'Assets'
        for prefab in assets.rglob(prefab_name):
            meta_path = str(prefab) + '.meta'
            guid = read_guid_from_meta(meta_path)
            if guid:
                return guid

        return None

    def relative_path(self, absolute_path: Path) -> str:
        """
        Convert an absolute path to a relative path from project root.

        Args:
            absolute_path: Absolute path

        Returns:
            Relative path string (starting with Assets/)
        """
        try:
            return str(absolute_path.relative_to(self.root))
        except ValueError:
            return str(absolute_path)
