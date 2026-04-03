# Unity CLI

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

A powerful command-line tool to manage Unity prefabs and scenes programmatically. Perfect for automation, CI/CD pipelines, and batch operations on your Unity projects.

## ✨ Features

- **Prefab Management**: Create, edit, delete, copy, and rename prefabs with ease
- **Component Management**: Add/remove components to/from prefabs programmatically
- **Scene Management**: Create scenes, add/remove GameObjects and prefab instances
- **Property Editing**: Set component properties via command line
- **Auto-discovery**: Automatically finds Unity projects in current directory
- **Zero Dependencies**: Uses only Python standard library
- **GUID Management**: Automatically handles Unity asset GUIDs and meta files

## 📦 Installation

### From GitHub (Latest)

```bash
pip install git+https://github.com/cumic06/unity-cli.git
```

### Local Development

```bash
git clone https://github.com/cumic06/unity-cli.git
cd unity-cli
pip install -e .
```

## 🚀 Quick Start

### Prefab Commands

```bash
# List all prefabs
unity-cli prefab list

# Show prefab details
unity-cli prefab show BaseMonster

# Create new prefab
unity-cli prefab create MyPrefab --path Assets/Resources/Prefabs/

# Add component to prefab
unity-cli prefab add-component MyPrefab Rigidbody2D

# Remove component from prefab
unity-cli prefab remove-component MyPrefab BoxCollider2D

# Set component property
unity-cli prefab set MyPrefab Transform.m_LocalScale.x=2

# Copy prefab (creates new GUID)
unity-cli prefab copy OldPrefab NewPrefab

# Rename prefab (keeps GUID)
unity-cli prefab rename OldName NewName

# Delete prefab
unity-cli prefab delete MyPrefab
```

### Scene Commands

```bash
# List all scenes
unity-cli scene list

# Show scene details
unity-cli scene show MyScene

# Create new scene
unity-cli scene create MyScene --path Assets/00_Scenes/

# Add GameObject to scene
unity-cli scene add-object MyScene Player --component Transform BoxCollider2D

# Add prefab instance to scene
unity-cli scene add-prefab MyScene MyPrefab --pos 1,2,3 --name CustomName

# Remove GameObject from scene
unity-cli scene remove-object MyScene Player

# Set object property in scene
unity-cli scene set MyScene Player Transform.m_LocalScale.x=2
```

### Options

- `--project PATH`: Specify Unity project root (auto-detected if omitted)
- `--help`: Show help message

## 💻 Usage Examples

### Example 1: Create a custom prefab

```bash
unity-cli prefab create EnemyBase --path Assets/Resources/Prefabs/Enemies/
unity-cli prefab add-component EnemyBase Rigidbody2D
unity-cli prefab add-component EnemyBase SpriteRenderer
unity-cli prefab add-component EnemyBase Animator
unity-cli prefab set EnemyBase Rigidbody2D.m_GravityScale=0
```

### Example 2: Setup a game scene

```bash
unity-cli scene create Level1 --path Assets/Scenes/
unity-cli scene add-object Level1 Player --component BoxCollider2D
unity-cli scene add-prefab Level1 EnemyBase --pos 5,2,0 --name Enemy1
unity-cli scene add-prefab Level1 EnemyBase --pos 10,2,0 --name Enemy2
```

### Example 3: Run from a subdirectory

```bash
cd Assets/Resources/Prefabs/Monsters/
unity-cli prefab list  # Works! Searches upward for Assets/ folder
```

## 🏗️ Project Structure

```
unity-cli/
├── unity_cli/
│   ├── core/
│   │   ├── prefab_manager.py    # Prefab operations
│   │   ├── scene_manager.py     # Scene operations
│   │   ├── project.py           # Project discovery
│   │   └── yaml_parser.py       # Unity YAML parser
│   ├── utils/
│   │   ├── guid.py              # GUID/fileID utilities
│   │   └── meta.py              # .meta file management
│   └── cli.py                   # Command-line interface
├── tests/                       # (Future) Test suite
├── LICENSE
├── README.md
├── CONTRIBUTING.md
└── pyproject.toml
```

## 🔍 How It Works

The tool parses Unity YAML files using text-based parsing (regex) instead of standard YAML libraries, since Unity uses custom tags (`!u!`) that aren't compatible with PyYAML.

### Key Technical Features

- **No External Dependencies**: Uses only Python standard library for maximum compatibility
- **GUID Management**: Automatically generates and manages GUIDs for new assets
- **Meta File Handling**: Creates and manages .meta files alongside assets
- **Path Resolution**: Auto-converts partial paths to absolute paths within the project
- **Regex-based Parsing**: Handles Unity's custom YAML format reliably
- **Reference Tracking**: Maintains proper fileID and guid references

## ⚙️ Requirements

- **Python**: 3.8 or higher
- **Unity Project**: Must have an `Assets/` folder structure

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📖 Additional Resources

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Issues](https://github.com/cumic06/unity-cli/issues)

## ⚠️ Note

This is a personal project maintained by [@cumic06](https://github.com/cumic06). While bug reports and feature requests are appreciated, only the maintainer can merge PRs and make release decisions.

---

**Made with ❤️ for the Unity community**
