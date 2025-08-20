#!/bin/bash
set -e

echo "Building Lambda layer for dependencies..."

# Create temporary directory for layer
LAYER_DIR="layer-build"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python

# Install dependencies to the layer directory
echo "Installing dependencies..."
pip install -r requirements.txt -t $LAYER_DIR/python/ --no-deps

# Create the layer zip
echo "Creating layer zip..."
cd $LAYER_DIR
zip -r ../dependencies-layer.zip python/
cd ..

# Cleanup
rm -rf $LAYER_DIR

echo "Layer built successfully: dependencies-layer.zip"
echo "Size: $(du -h dependencies-layer.zip | cut -f1)"