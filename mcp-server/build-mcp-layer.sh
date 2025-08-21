#!/bin/bash
set -e

echo "Building MCP Lambda layer for dependencies..."

# Create temporary directory for layer
LAYER_DIR="mcp-layer-build"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python

# Install MCP dependencies to the layer directory
echo "Installing MCP dependencies..."
pip install -r requirements.txt -t $LAYER_DIR/python/ --no-cache-dir

# Create the layer zip
echo "Creating MCP layer zip..."
cd $LAYER_DIR
zip -r ../mcp-dependencies-layer.zip python/
cd ..

# Cleanup
rm -rf $LAYER_DIR

echo "MCP layer built successfully: mcp-dependencies-layer.zip"
echo "Size: $(du -h mcp-dependencies-layer.zip | cut -f1)"