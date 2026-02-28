#!/bin/bash
#
# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.

# Verification script for Network Device Configuration Manager
# This script verifies that all components are working correctly

echo "======================================"
echo "Network Device Configuration Manager"
echo "Verification Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

check() {
    echo -n "Checking $1... "
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}"
    FAILED=$((FAILED + 1))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}"
}

# Check Python version
check "Python version"
if python3 --version | grep -q "Python 3.1[2-9]"; then
    pass
else
    warn
    echo "  Python 3.12+ recommended but not required for verification"
fi

# Check file structure
check "Backend structure"
if [ -f "backend/app/main.py" ] && [ -f "backend/app/models.py" ] && \
   [ -f "backend/app/ssh_executor.py" ] && [ -f "backend/app/job_manager.py" ] && \
   [ -f "backend/app/ws.py" ]; then
    pass
else
    fail
fi

check "Frontend structure"
if [ -f "frontend/public/index.html" ] && [ -f "frontend/public/app.js" ]; then
    pass
else
    fail
fi

check "Backend v2 structure"
if [ -f "backend_v2/app/api/main.py" ] && [ -f "backend_v2/app/application/execution_engine.py" ] && \
   [ -f "backend_v2/app/domain/state_machine.py" ] && [ -f "backend_v2/app/infrastructure/in_memory_job_store.py" ]; then
    pass
else
    fail
fi

check "Frontend v2 structure"
if [ -f "frontend_v2/public/index.html" ] && [ -f "frontend_v2/public/app.js" ]; then
    pass
else
    fail
fi

check "Test structure"
if [ -d "tests/unit" ] && [ -d "tests/integration" ] && [ -d "tests/mock_ssh_server" ]; then
    pass
else
    fail
fi

check "Documentation"
if [ -f "README.md" ] && [ -f "README.ja.md" ] && \
   [ -f "docs/QUICKSTART.md" ] && [ -f "docs/CONTRIBUTING.md" ]; then
    pass
else
    fail
fi

check "CI/CD configuration"
if [ -f ".github/workflows/ci.yml" ]; then
    pass
else
    fail
fi

check "Docker configuration"
if [ -f "Dockerfile" ] && [ -f "docker-compose.yml" ]; then
    pass
else
    fail
fi

# Check if dependencies are installed
check "Backend dependencies"
if python3 -c "import fastapi" &> /dev/null; then
    pass
else
    warn
    echo "  Run: python3 -m pip install -r backend/requirements.txt"
fi

# Run linting if tools are available
if python3 -c "import black" &> /dev/null; then
    check "Code formatting (black)"
    if python3 -m black --check backend/app backend_v2/app tests backend_v2/tests &> /dev/null; then
        pass
    else
        fail
        echo "  Run: python3 -m black backend/app backend_v2/app tests backend_v2/tests"
    fi
else
    warn "  black not installed, skipping"
fi

if python3 -c "import flake8" &> /dev/null; then
    check "Code linting (flake8)"
    if python3 -m flake8 backend/app backend_v2/app tests backend_v2/tests --max-line-length=120 --extend-ignore=E203,W503 &> /dev/null; then
        pass
    else
        fail
        echo "  Run: python3 -m flake8 backend/app backend_v2/app tests backend_v2/tests --max-line-length=120 --extend-ignore=E203,W503"
    fi
else
    warn "  flake8 not installed, skipping"
fi

if python3 -c "import mypy" &> /dev/null; then
    check "Type checking (mypy backend_v2)"
    if python3 -m mypy --explicit-package-bases backend_v2/app &> /dev/null; then
        pass
    else
        fail
        echo "  Run: python3 -m mypy --explicit-package-bases backend_v2/app"
    fi
else
    warn "  mypy not installed, skipping"
fi

if python3 -c "import pre_commit" &> /dev/null; then
    check "Pre-commit hooks"
    if PRE_COMMIT_HOME="${PRE_COMMIT_HOME:-.pre-commit-cache}" python3 -m pre_commit run --all-files &> /dev/null; then
        pass
    else
        fail
        echo "  Run: PRE_COMMIT_HOME=.pre-commit-cache python3 -m pre_commit run --all-files"
    fi
else
    warn "  pre-commit not installed, skipping"
fi

# Run tests if pytest is available
if python3 -c "import pytest" &> /dev/null; then
    check "Unit tests"
    if python3 -m pytest tests/unit backend_v2/tests/unit -v &> /dev/null; then
        pass
    else
        fail
        echo "  Run: python3 -m pytest tests/unit backend_v2/tests/unit -v"
    fi
else
    warn "  pytest not installed, skipping"
fi

if python3 -c "import pytest" &> /dev/null; then
    check "Integration test discovery"
    if python3 -m pytest --collect-only tests/integration backend_v2/tests/integration -q &> /dev/null; then
        pass
    else
        fail
        echo "  Run: python3 -m pytest --collect-only tests/integration backend_v2/tests/integration -q"
    fi
fi

# Check sample files
check "Sample files"
if [ -f "sample_devices.csv" ] && [ -f "sample_commands.txt" ]; then
    pass
else
    fail
fi

echo ""
echo "======================================"
echo "Verification Summary"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Install dependencies: python3 -m pip install -r backend/requirements-dev.txt"
    echo "2. Run tests: python3 -m pytest tests/unit backend_v2/tests/unit -v"
    echo "3. Start v1 application: ./start.sh"
    echo "4. Start v2 application: ./start_v2.sh"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo "Please fix the issues above before proceeding"
    exit 1
fi
