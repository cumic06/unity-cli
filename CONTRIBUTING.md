# Contributing to unity-cli

Thank you for your interest in contributing to unity-cli!

## Important Note

This is a personal project maintained by [@cumic06](https://github.com/cumic06). While we appreciate bug reports and feature requests, **only the maintainer can merge pull requests and make release decisions**.

## How to Contribute

### 1. Reporting Bugs

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Your environment (Python version, OS, Unity version)

### 2. Feature Requests

Have an idea? Open an issue with:
- Description of the feature
- Use case and why it would be useful
- Example usage

### 3. Code Contributions

While code contributions are welcome, please note:
- All PRs should be targeted at the `main` branch
- The maintainer will review and decide whether to merge
- Code should follow PEP 8 style guidelines
- Add tests for new features when possible

### 4. Development Setup

```bash
# Clone the repository
git clone https://github.com/cumic06/unity-cli.git
cd unity-cli

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Test your changes
unity-cli --help
```

## Code Style

- Follow PEP 8
- Use 4-space indentation
- Write docstrings for public functions
- Keep lines under 100 characters when possible

## Testing Your Changes

Before submitting a PR:
1. Test with real Unity projects
2. Verify all commands work as expected
3. Check for edge cases (empty projects, special characters in names, etc.)

## PR Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit with clear messages
5. Push to your fork
6. Open a pull request with a clear description

The maintainer will review your PR and may:
- Request changes
- Ask questions
- Merge it
- Close it with feedback

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue with the `question` label!
