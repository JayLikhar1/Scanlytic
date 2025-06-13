#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Download spaCy model
python -m spacy download en_core_web_sm 