#!/bin/bash

# Read versions from JSON
versions=$(python -c "import json; print(' '.join(json.load(open('supported_python_versions.json'))))")

echo "🚀 Starting Test Matrix..."

# Variable to track if any test failed
FAILED=0

for v in $versions; do
    echo "----------------------------------------"
    echo "🐍 Testing with Python $v"
    
    # Run the test, but allow it to fail without stopping the script
    if ! uv run --python "$v" --all-groups pytest tests/; then
        echo "❌ FAILED on Python $v"
        FAILED=1
    else
        echo "✅ PASSED on Python $v"
    fi
done

echo "----------------------------------------"
if [ $FAILED -ne 0 ]; then
    echo "💥 Some tests failed."
    exit 1
else
    echo "🎉 All tests passed!"
    exit 0
fi
