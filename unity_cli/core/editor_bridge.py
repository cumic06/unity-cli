"""Bridge to communicate with Unity Editor via batch mode."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

# Location of the C# Editor script bundled with this package
_EDITOR_SCRIPT = Path(__file__).resolve().parent.parent / 'editor' / 'UnityCLICapture.cs'


def find_unity_editor() -> Optional[str]:
    """
    Find the Unity Editor executable.

    Search order:
      1. UNITY_EDITOR_PATH environment variable
      2. Unity Hub default install locations (Windows / macOS)
      3. PATH
    """
    import os

    # 1. Environment variable
    env_path = os.environ.get('UNITY_EDITOR_PATH')
    if env_path and Path(env_path).exists():
        return env_path

    # 2. Common install locations
    candidates = []

    if os.name == 'nt':
        # Windows — Unity Hub default
        program_files = Path(os.environ.get('ProgramFiles', r'C:\Program Files'))
        hub_editors = program_files / 'Unity' / 'Hub' / 'Editor'
        if hub_editors.exists():
            # Pick the newest version
            versions = sorted(hub_editors.iterdir(), reverse=True)
            for v in versions:
                exe = v / 'Editor' / 'Unity.exe'
                if exe.exists():
                    candidates.append(str(exe))
    else:
        # macOS
        hub_editors = Path('/Applications/Unity/Hub/Editor')
        if hub_editors.exists():
            versions = sorted(hub_editors.iterdir(), reverse=True)
            for v in versions:
                app = v / 'Unity.app' / 'Contents' / 'MacOS' / 'Unity'
                if app.exists():
                    candidates.append(str(app))

    if candidates:
        return candidates[0]

    # 3. PATH
    unity_in_path = shutil.which('Unity') or shutil.which('Unity.exe')
    if unity_in_path:
        return unity_in_path

    return None


def install_editor_script(project_root: Path) -> Path:
    """
    Install the UnityCLICapture.cs Editor script into the Unity project.

    Copies to: Assets/Editor/UnityCLI/UnityCLICapture.cs

    Returns:
        Path to the installed script
    """
    target_dir = project_root / 'Assets' / 'Editor' / 'UnityCLI'
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / 'UnityCLICapture.cs'
    shutil.copy2(str(_EDITOR_SCRIPT), str(target))

    return target


def capture_screenshot(
    project_root: Path,
    scene_path: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    unity_path: Optional[str] = None,
) -> str:
    """
    Capture a screenshot of a scene via Unity Editor batch mode.

    Args:
        project_root: Unity project root directory
        scene_path: Path to the .unity scene file (relative to project root, e.g. Assets/Scenes/Main.unity)
        output_path: Where to save the PNG screenshot
        width: Screenshot width in pixels
        height: Screenshot height in pixels
        unity_path: Path to Unity Editor executable (auto-detected if None)

    Returns:
        Absolute path to the saved screenshot

    Raises:
        FileNotFoundError: If Unity Editor not found
        RuntimeError: If capture fails
    """
    # Find Unity
    editor = unity_path or find_unity_editor()
    if not editor:
        raise FileNotFoundError(
            'Unity Editor not found. Set UNITY_EDITOR_PATH environment variable '
            'or install Unity via Unity Hub.'
        )

    # Ensure the Editor script is installed
    install_editor_script(project_root)

    # Resolve output path
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [
        editor,
        '-batchmode',
        '-nographics',
        '-projectPath', str(project_root),
        '-executeMethod', 'UnityCLI.Capture.CaptureScreenshot',
        '-logFile', '-',
        '-scenePath', scene_path,
        '-outputPath', str(output),
        '-width', str(width),
        '-height', str(height),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError('Unity Editor timed out (120s). Is the project very large?')

    if result.returncode != 0:
        # Extract useful error from Unity log
        error_lines = [
            line for line in result.stdout.splitlines()
            if '[UnityCLI]' in line or 'error' in line.lower()
        ]
        error_msg = '\n'.join(error_lines[-5:]) if error_lines else result.stdout[-500:]
        raise RuntimeError(f'Screenshot capture failed (exit {result.returncode}):\n{error_msg}')

    if not output.exists():
        raise RuntimeError(f'Screenshot file not created: {output}')

    return str(output)
