#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y build-essential python3-dev

# Print Python version
python --version

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements.txt

# Create uploads directory
echo "Creating uploads directory..."
mkdir -p uploads

# Install spaCy model
echo "Installing spaCy model..."
python -m spacy download en_core_web_sm

# Verify spaCy model installation
echo "Verifying spaCy model..."
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('SpaCy model loaded successfully!')"

# Print directory structure
echo "Current directory structure:"
ls -la

echo "Build completed successfully!" 