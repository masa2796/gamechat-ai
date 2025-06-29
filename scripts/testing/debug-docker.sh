# Docker Build Debug Script
#!/bin/bash

echo "=== Docker Build Context Debug ==="
echo "Current directory: $(pwd)"
echo ""

echo "=== Listing root directory ==="
ls -la

echo ""
echo "=== Checking data directory ==="
if [ -d "data" ]; then
    echo "✅ data/ directory exists"
    ls -la data/
else
    echo "❌ data/ directory does not exist"
fi

echo ""
echo "=== Checking backend directory ==="
if [ -d "backend" ]; then
    echo "✅ backend/ directory exists"
    ls -la backend/
else
    echo "❌ backend/ directory does not exist"
fi

echo ""
echo "=== Checking .dockerignore ==="
if [ -f ".dockerignore" ]; then
    echo "✅ .dockerignore exists"
    echo "Contents:"
    cat .dockerignore | grep -E "(data|^data)"
else
    echo "❌ .dockerignore does not exist"
fi

echo ""
echo "=== Testing Docker build context ==="
docker build --no-cache --progress=plain -f backend/Dockerfile -t test-build . 2>&1 | head -50
