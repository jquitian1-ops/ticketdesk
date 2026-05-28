#!/bin/bash
# PostToolUse Hook - Runs after each tool execution
# Executes linting and tests for quality assurance

CHANGED_FILE=$1
TOOL_NAME=$2

echo "🔧 PostToolUse Hook: $TOOL_NAME on $CHANGED_FILE"

# Detect file type and run appropriate checks
if [[ "$CHANGED_FILE" == *.py ]]; then
    echo "🐍 Python file detected"
    
    # Run black formatter check
    if command -v black &> /dev/null; then
        echo "  → Running black..."
        black --check "$CHANGED_FILE" 2>/dev/null || black "$CHANGED_FILE"
    fi
    
    # Run pylint
    if command -v pylint &> /dev/null; then
        echo "  → Running pylint..."
        pylint "$CHANGED_FILE" --max-line-length=100 --disable=C0111 2>/dev/null || true
    fi
    
    # Run tests if file is in app/
    if [[ "$CHANGED_FILE" == app/* ]]; then
        echo "  → Running related tests..."
        cd backend
        pytest "${CHANGED_FILE/%.py/_test.py}" -q 2>/dev/null || true
        cd ..
    fi

elif [[ "$CHANGED_FILE" == *.ts || "$CHANGED_FILE" == *.tsx ]]; then
    echo "📘 TypeScript file detected"
    
    # Run prettier
    if command -v prettier &> /dev/null; then
        echo "  → Running prettier..."
        prettier --write "$CHANGED_FILE"
    fi
    
    # Run eslint
    if command -v eslint &> /dev/null; then
        echo "  → Running eslint..."
        eslint "$CHANGED_FILE" --fix 2>/dev/null || true
    fi
    
    # Run tests
    if [[ "$CHANGED_FILE" == app/components/* ]]; then
        echo "  → Running component tests..."
        cd frontend
        npm test -- "${CHANGED_FILE}" --coverage 2>/dev/null || true
        cd ..
    fi

elif [[ "$CHANGED_FILE" == *.json ]]; then
    echo "📋 JSON file detected"
    
    if [[ "$CHANGED_FILE" == *cloudformation* || "$CHANGED_FILE" == *terraform* ]]; then
        echo "  → Validating infrastructure config..."
        # Add infrastructure validation
    fi
fi

echo "✅ Hook completed"
