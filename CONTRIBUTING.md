# Contributing to Antares Web

Thank you for your interest in contributing to Antares Web! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

### Prerequisites

Before contributing, make sure you have the following installed:

- Python 3.11.x
- Node.js 22.13.0
- Git

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AntaREST.git
   cd AntaREST
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/AntaresSimulatorTeam/AntaREST.git
   ```

4. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   python3 -m pip install --upgrade pip
   pip install -e .
   pip install -r requirements-dev.txt
   ```

6. **Install frontend dependencies**:
   ```bash
   cd webapp
   npm install
   cd ..
   ```
   
## Development Workflow

### Branching Strategy

This project follows the **[git-flow](https://nvie.com/posts/a-successful-git-branching-model/)** branching model:

- `dev`: Main development branch (default branch)
- `master`: Stable release branch
- Feature branches: `feat/your-feature-name`
- Bug fixes: `fix/bug-description`
- Documentation: `docs/what-you-document`

### Creating a Feature Branch

```bash
# Make sure you're on dev and up to date
git checkout dev
git pull upstream dev

# Create your feature branch
git checkout -b feat/your-feature-name
```

### Making Changes

1. Make your changes in your feature branch
2. Write or update tests as needed
3. Ensure all tests pass
4. Ensure code quality checks pass

## Coding Standards

### Python Code Style

We use **Ruff** for linting and formatting Python code:

```bash
# Check for style issues and auto-fix them
ruff check antarest/ tests/ --fix

# Format code
ruff format antarest/ tests/
```

### Type Checking

We use **mypy** for static type checking:

```bash
mypy
```

All Python code should include type hints. Configuration is in `pyproject.toml`.

### Code Quality Guidelines

- **Write clear, self-documenting code**: Use descriptive variable and function names
- **Keep functions focused**: Each function should do one thing well
- **Add docstrings**: Document all public modules, functions, classes, and methods
- **Handle errors gracefully**: Use appropriate exception handling
- **Avoid code duplication**: Extract common logic into reusable functions

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

For **breaking changes**, add `!` after the type/scope:
```
<type>(<scope>)!: <subject>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add endpoint for study export

Implements a new REST endpoint that allows users to export
studies in various formats.

Closes #123
```

```
fix(ui): correct table pagination behavior

The pagination was not resetting when filters were applied.
This commit ensures the page resets to 1 when filters change.
```

```
feat(study)!: breaking change

BREAKING CHANGE: something breaks
```

## Testing

### Running Tests

```bash
# Run all tests in parallel
pytest -n auto
```

### Writing Tests

- Write unit tests for all new functionality
- Ensure integration tests cover end-to-end workflows
- Aim for high code coverage (target: 80%+)
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern

**Test file structure:**
```python
def test_function_name_should_do_something():
    # Arrange: Set up test data and dependencies
    study = create_test_study()

    # Act: Execute the function being tested
    result = process_study(study)

    # Assert: Verify the expected outcome
    assert result.status == "success"
    assert len(result.warnings) == 0
```

## Submitting Changes

### Before Submitting

Ensure your changes meet all requirements:

- [ ] All tests pass
- [ ] Code is properly formatted (ruff)
- [ ] Type checking passes (mypy)
- [ ] Commit messages follow conventional commits
- [ ] Branch is rebased on latest upstream/dev

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Create a Pull Request** on GitHub from your fork to the upstream `dev` branch

3. **Fill in the PR template** with:
   - Clear description of changes
   - Related issue numbers (e.g., "Closes #123")
   - Screenshots (if UI changes)
   - Testing steps

4. **Wait for review** - maintainers will review your PR and may request changes

### PR Review Process

- At least one maintainer approval is required
- All CI checks must pass
- Address any review comments
- Keep the PR focused - avoid mixing unrelated changes

## Reporting Issues

### Before Creating an Issue

- Search existing issues to avoid duplicates
- Check if the issue is already fixed in the latest version
- Gather relevant information (OS, Python version, etc.)

### Creating a Good Issue Report

Include:

1. **Clear title** describing the issue
2. **Environment details**:
   - OS and version
   - Python version
   - AntaREST version
3. **Steps to reproduce** the issue
4. **Expected behavior**
5. **Actual behavior**
6. **Error messages or logs**
7. **Screenshots** (if applicable)

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed

## Getting Help

If you need help with contributing:

- Check the [documentation](https://antares-web.readthedocs.io/)
- Ask in [GitHub Discussions](https://github.com/AntaresSimulatorTeam/AntaREST/discussions)
- Open an issue with the `question` label
- Contact the maintainers: andrea.sgattoni@rte-france.com

---

**Questions?** Feel free to reach out to the maintainers or open a discussion on GitHub.