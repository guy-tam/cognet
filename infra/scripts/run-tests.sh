#!/bin/bash
set -e

echo "=== COGNET LDI Engine — Test Runner ==="

export PYTHONPATH="$(pwd)/apps/api:$(pwd)/services:$(pwd)"

# הרצת בדיקות יחידה
echo "→ Running unit tests..."
pytest tests/unit/ -v --tb=short

# הרצת בדיקות אינטגרציה
echo "→ Running integration tests..."
pytest tests/integration/ -v --tb=short

# הרצת בדיקות API
echo "→ Running API tests..."
pytest apps/api/app/tests/ -v --tb=short

echo "✓ All tests complete"
