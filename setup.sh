#!/bin/bash
# Setup script for Continuous Regulatory Intelligence

set -e

echo "Setting up Continuous Regulatory Intelligence..."
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your settings"
else
    echo ".env file already exists"
fi

# Create data directory
echo "Creating data directory..."
mkdir -p data/documents

# Initialize database
echo "Initializing database..."
python -m src.init_db

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit .env with your settings"
echo "3. Run tests: pytest tests/"
echo "4. Process a document: python run_one_doc.py path/to/doc.pdf --isin LU1234567890"
