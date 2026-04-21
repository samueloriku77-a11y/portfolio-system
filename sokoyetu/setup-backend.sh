#!/bin/bash
# Backend Setup Script for SokoYetu
# This script sets up the development environment with all dependencies

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         SokoYetu Backend - Development Environment Setup       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/6]${NC} Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment
echo -e "${YELLOW}[2/6]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}[3/6]${NC} Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo -e "${GREEN}✅ Virtual environment activated (Windows)${NC}"
fi
echo ""

# Install dependencies
echo -e "${YELLOW}[4/6]${NC} Installing Python dependencies..."
cd backend
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Setup environment file
echo -e "${YELLOW}[5/6]${NC} Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    echo -e "${YELLOW}   ⚠️  Please update .env with your credentials${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Initialize database
echo -e "${YELLOW}[6/6]${NC} Initializing database..."
python3 << EOF
from database import engine, Base
from models import *

Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")
EOF
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your M-Pesa, Email, and SMS credentials"
echo "2. Run tests: pytest"
echo "3. Start server: uvicorn main:app --reload"
echo ""
