<!--
Copyright 2026 icecake0141
SPDX-License-Identifier: Apache-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Please review for correctness and security.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# Contributing to Network Device Configuration Manager

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/icecake0141/nw-edit.git
   cd nw-edit
   ```

2. **Install development dependencies**
   ```bash
   cd backend
   pip install -r requirements-dev.txt
   ```

3. **Run tests**
   ```bash
   # Unit tests
   pytest tests/unit -v
   
   # With coverage
   pytest tests/unit -v --cov=backend/app --cov-report=html
   ```

## Code Standards

### Python

- **Formatting**: Use `black` for code formatting
  ```bash
  cd backend
  black app/ ../tests/
  ```

- **Linting**: Code must pass `flake8` checks
  ```bash
  cd backend
  flake8 app/ ../tests/ --max-line-length=120 --extend-ignore=E203,W503
  ```

- **Type Hints**: Use type hints where appropriate
- **Docstrings**: Add docstrings to all public functions and classes

### Testing

- Write unit tests for all new features
- Ensure all tests pass before submitting PR
- Maintain or improve code coverage
- Use mocks for external dependencies (Netmiko, SSH connections)

## Commit Guidelines

Use conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `ci:` - CI/CD changes
- `refactor:` - Code refactoring
- `style:` - Code style changes (formatting, etc.)

Example:
```
feat: Add support for Juniper devices
fix: Handle connection timeout properly
docs: Update API documentation
```

## Pull Request Process

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes** following the code standards

3. **Run tests and linting**
   ```bash
   cd backend
   black app/ ../tests/
   flake8 app/ ../tests/ --max-line-length=120 --extend-ignore=E203,W503
   pytest tests/unit -v
   ```

4. **Commit your changes** with clear commit messages

5. **Push to your fork** and create a Pull Request

6. **Describe your changes** in the PR description:
   - What does this PR do?
   - Why is this change needed?
   - How was it tested?
   - Any breaking changes?

## Code Review

All submissions require code review. We use GitHub pull requests for this purpose.

## Questions?

Feel free to open an issue for questions or discussions.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
