#!/bin/bash

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

check "Test structure"
if [ -d "tests/unit" ] && [ -d "tests/integration" ] && [ -d "tests/mock_ssh_server" ]; then
    pass
else
    fail
fi

check "Documentation"
if [ -f "README.md" ] && [ -f "README.ja.md" ] && \
   [ -f "QUICKSTART.md" ] && [ -f "CONTRIBUTING.md" ]; then
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
if pip list | grep -q fastapi; then
    pass
else
    warn
    echo "  Run: cd backend && pip install -r requirements.txt"
fi

# Run linting if tools are available
if command -v black &> /dev/null; then
    check "Code formatting (black)"
    cd backend
    if black --check app/ ../tests/ &> /dev/null; then
        pass
    else
        fail
        echo "  Run: cd backend && black app/ ../tests/"
    fi
    cd ..
else
    warn "  black not installed, skipping"
fi

if command -v flake8 &> /dev/null; then
    check "Code linting (flake8)"
    cd backend
    if flake8 app/ ../tests/ --max-line-length=120 --extend-ignore=E203,W503 &> /dev/null; then
        pass
    else
        fail
        echo "  Run: cd backend && flake8 app/ ../tests/"
    fi
    cd ..
else
    warn "  flake8 not installed, skipping"
fi

# Run tests if pytest is available
if command -v pytest &> /dev/null; then
    check "Unit tests"
    if pytest tests/unit -v &> /dev/null; then
        pass
    else
        fail
        echo "  Run: pytest tests/unit -v"
    fi
else
    warn "  pytest not installed, skipping"
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
    echo "1. Install dependencies: cd backend && pip install -r requirements.txt"
    echo "2. Run tests: pytest tests/unit -v"
    echo "3. Start application: ./start.sh"
    echo "4. Access frontend: http://localhost:3000"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo "Please fix the issues above before proceeding"
    exit 1
fi
