"""Command-line interface for Unity CLI tool"""

import argparse
import sys
from pathlib import Path
from .core.project import UnityProject
from .core.prefab_manager import PrefabManager
from .core.scene_manager import SceneManager


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser"""
    parser = argparse.ArgumentParser(
        prog='unity-cli',
        description='Unity CLI tool to manage prefabs and scenes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all prefabs
  unity-cli prefab list

  # Show prefab details
  unity-cli prefab show BaseMonster

  # Create new prefab
  unity-cli prefab create MyPrefab --path Assets/Resources/Prefabs/

  # Add component to prefab
  unity-cli prefab add-component MyPrefab Rigidbody2D

  # Set component property
  unity-cli prefab set MyPrefab Transform.m_LocalScale.x=2

  # List all scenes
  unity-cli scene list

  # Create new scene
  unity-cli scene create MyScene

  # Add GameObject to scene
  unity-cli scene add-object MyScene Player --component Transform BoxCollider2D
        """,
    )

    parser.add_argument(
        '--project',
        type=str,
        help='Unity project root path (auto-detected if not specified)',
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Prefab commands
    prefab_parser = subparsers.add_parser('prefab', help='Manage prefabs')
    prefab_sub = prefab_parser.add_subparsers(dest='subcommand', help='Prefab action')

    # prefab list
    list_parser = prefab_sub.add_parser('list', help='List all prefabs')
    list_parser.add_argument(
        '--path', type=str, default='', help='Directory path (default: entire project)'
    )

    # prefab show
    show_parser = prefab_sub.add_parser('show', help='Show prefab details')
    show_parser.add_argument('name', help='Prefab name or path')

    # prefab create
    create_parser = prefab_sub.add_parser('create', help='Create new prefab')
    create_parser.add_argument('name', help='Prefab name')
    create_parser.add_argument(
        '--path',
        type=str,
        default='Assets/Resources/Prefabs/',
        help='Target directory',
    )

    # prefab delete
    delete_parser = prefab_sub.add_parser('delete', help='Delete prefab')
    delete_parser.add_argument('name', help='Prefab name or path')

    # prefab copy
    copy_parser = prefab_sub.add_parser('copy', help='Copy prefab')
    copy_parser.add_argument('src', help='Source prefab path')
    copy_parser.add_argument('dst', help='Destination prefab path')

    # prefab rename
    rename_parser = prefab_sub.add_parser('rename', help='Rename prefab')
    rename_parser.add_argument('name', help='Prefab name')
    rename_parser.add_argument('new_name', help='New prefab name')

    # prefab add-component
    add_comp_parser = prefab_sub.add_parser('add-component', help='Add component to prefab')
    add_comp_parser.add_argument('name', help='Prefab name')
    add_comp_parser.add_argument('component', help='Component type (e.g., Rigidbody2D)')

    # prefab remove-component
    rm_comp_parser = prefab_sub.add_parser('remove-component', help='Remove component from prefab')
    rm_comp_parser.add_argument('name', help='Prefab name')
    rm_comp_parser.add_argument('component', help='Component type')

    # prefab set
    set_parser = prefab_sub.add_parser('set', help='Set component property')
    set_parser.add_argument('name', help='Prefab name')
    set_parser.add_argument('property', help='Property (format: Component.field=value)')

    # Scene commands
    scene_parser = subparsers.add_parser('scene', help='Manage scenes')
    scene_sub = scene_parser.add_subparsers(dest='subcommand', help='Scene action')

    # scene list
    scene_list_parser = scene_sub.add_parser('list', help='List all scenes')
    scene_list_parser.add_argument(
        '--path', type=str, default='', help='Directory path (default: entire project)'
    )

    # scene show
    scene_show_parser = scene_sub.add_parser('show', help='Show scene details')
    scene_show_parser.add_argument('name', help='Scene name or path')

    # scene create
    scene_create_parser = scene_sub.add_parser('create', help='Create new scene')
    scene_create_parser.add_argument('name', help='Scene name')
    scene_create_parser.add_argument(
        '--path',
        type=str,
        default='Assets/00_Scenes/',
        help='Target directory',
    )

    # scene add-object
    add_obj_parser = scene_sub.add_parser('add-object', help='Add GameObject to scene')
    add_obj_parser.add_argument('scene', help='Scene name or path')
    add_obj_parser.add_argument('name', help='GameObject name')
    add_obj_parser.add_argument(
        '--component',
        type=str,
        nargs='*',
        default=[],
        help='Components to add',
    )

    # scene add-prefab
    add_prefab_parser = scene_sub.add_parser('add-prefab', help='Add prefab instance to scene')
    add_prefab_parser.add_argument('scene', help='Scene name or path')
    add_prefab_parser.add_argument('prefab', help='Prefab name or path')
    add_prefab_parser.add_argument(
        '--pos',
        type=str,
        default='0,0,0',
        help='Position as x,y,z (default: 0,0,0)',
    )
    add_prefab_parser.add_argument(
        '--name',
        type=str,
        help='Custom instance name',
    )

    # scene remove-object
    rm_obj_parser = scene_sub.add_parser('remove-object', help='Remove GameObject from scene')
    rm_obj_parser.add_argument('scene', help='Scene name or path')
    rm_obj_parser.add_argument('name', help='GameObject name')

    # scene set
    scene_set_parser = scene_sub.add_parser('set', help='Set object property')
    scene_set_parser.add_argument('scene', help='Scene name or path')
    scene_set_parser.add_argument('target', help='Target (format: ObjectName.Component.field)')
    scene_set_parser.add_argument('value', help='New value')

    return parser


def find_asset_file(project: UnityProject, name: str, suffix: str) -> str:
    """Find an asset file by name"""
    assets_dir = project.root / 'Assets'

    # Try exact match first
    for asset in assets_dir.rglob(f'{name}{suffix}'):
        return str(asset)

    # Try partial match
    for asset in assets_dir.rglob(f'*{name}*{suffix}'):
        return str(asset)

    raise FileNotFoundError(f'{suffix[1:].capitalize()} not found: {name}')


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Find project
        if args.project:
            project = UnityProject(Path(args.project))
        else:
            project = UnityProject.find('.')

        # Prefab commands
        if args.command == 'prefab':
            manager = PrefabManager(project)

            if args.subcommand == 'list':
                prefabs = manager.list_all(args.path)
                if prefabs:
                    print('Prefabs:')
                    for prefab in prefabs:
                        print(f'  {prefab}')
                else:
                    print('No prefabs found')

            elif args.subcommand == 'show':
                prefab_path = find_asset_file(project, args.name, '.prefab')
                info = manager.show(prefab_path)
                print(f"\nPrefab: {info.get('name')}")
                print(f"Path: {info.get('path')}")
                print(f"Components: {', '.join(info.get('components', []))}")

            elif args.subcommand == 'create':
                result = manager.create(args.name, args.path)
                print(f'Created prefab: {project.relative_path(result)}')

            elif args.subcommand == 'delete':
                prefab_path = find_asset_file(project, args.name, '.prefab')
                manager.delete(prefab_path)
                print(f'Deleted prefab: {args.name}')

            elif args.subcommand == 'copy':
                src_path = find_asset_file(project, args.src, '.prefab')
                result = manager.copy(src_path, args.dst)
                print(f'Copied to: {project.relative_path(result)}')

            elif args.subcommand == 'rename':
                src_path = find_asset_file(project, args.name, '.prefab')
                result = manager.rename(src_path, args.new_name)
                print(f'Renamed to: {project.relative_path(result)}')

            elif args.subcommand == 'add-component':
                prefab_path = find_asset_file(project, args.name, '.prefab')
                manager.add_component(prefab_path, args.component)
                print(f'Added component {args.component} to {args.name}')

            elif args.subcommand == 'remove-component':
                prefab_path = find_asset_file(project, args.name, '.prefab')
                manager.remove_component(prefab_path, args.component)
                print(f'Removed component {args.component} from {args.name}')

            elif args.subcommand == 'set':
                prefab_path = find_asset_file(project, args.name, '.prefab')
                # Parse property: Component.field=value
                parts = args.property.split('=', 1)
                if len(parts) != 2:
                    print('Error: property format should be Component.field=value')
                    return
                prop_path, value = parts
                comp_parts = prop_path.split('.', 1)
                if len(comp_parts) != 2:
                    print('Error: property format should be Component.field=value')
                    return
                component, field = comp_parts
                manager.set_property(prefab_path, component, field, value)
                print(f'Set {component}.{field} = {value}')

        # Scene commands
        elif args.command == 'scene':
            manager = SceneManager(project)

            if args.subcommand == 'list':
                scenes = manager.list_all(args.path)
                if scenes:
                    print('Scenes:')
                    for scene in scenes:
                        print(f'  {scene}')
                else:
                    print('No scenes found')

            elif args.subcommand == 'show':
                scene_path = find_asset_file(project, args.name, '.unity')
                info = manager.show(scene_path)
                print(f"\nScene: {info.get('name')}")
                print(f"Path: {info.get('path')}")
                if info.get('gameobjects'):
                    print(f"GameObjects: {', '.join(info.get('gameobjects', []))}")
                if info.get('prefab_instances'):
                    print(f"Prefab Instances: {', '.join(info.get('prefab_instances', []))}")

            elif args.subcommand == 'create':
                result = manager.create(args.name, args.path)
                print(f'Created scene: {project.relative_path(result)}')

            elif args.subcommand == 'add-object':
                scene_path = find_asset_file(project, args.scene, '.unity')
                manager.add_object(scene_path, args.name, args.component if args.component else None)
                print(f'Added GameObject {args.name} to scene')

            elif args.subcommand == 'add-prefab':
                scene_path = find_asset_file(project, args.scene, '.unity')
                prefab_path = find_asset_file(project, args.prefab, '.prefab')

                # Parse position
                pos_parts = args.pos.split(',')
                if len(pos_parts) != 3:
                    print('Error: position format should be x,y,z')
                    return
                position = tuple(float(p.strip()) for p in pos_parts)

                manager.add_prefab(scene_path, prefab_path, position, args.name)
                print(f'Added prefab {args.prefab} to scene')

            elif args.subcommand == 'remove-object':
                scene_path = find_asset_file(project, args.scene, '.unity')
                manager.remove_object(scene_path, args.name)
                print(f'Removed GameObject {args.name} from scene')

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
