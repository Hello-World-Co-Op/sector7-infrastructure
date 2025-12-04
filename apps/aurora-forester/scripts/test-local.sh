#!/bin/bash
# Aurora Forester Local Test Script
# Tests Aurora without deploying to cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Aurora Forester Local Test"
echo "=========================================="

cd "$PROJECT_DIR"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run test
echo ""
echo "Running Aurora test..."
python main.py test

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "To run CLI mode:"
echo "  source venv/bin/activate"
echo "  python main.py cli"
echo ""
