#!/bin/bash

echo "=================================================="
echo "    Setting Up HANERMA Development Environment    "
echo "=================================================="

# Check for Docker
if ! command -v docker &> /dev/null
then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

echo "[1/3] Spinning up infrastructure containers..."
docker-compose -f docker-compose.yml up -d neo4j-db redis-cache

echo "[2/3] Waiting for Neo4j initialization..."
sleep 10  # Simplistic wait, ideally we'd health-check

echo "[3/3] Creating Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev,xerv]

echo "=================================================="
echo "    Setup Complete! "
echo "    Run 'make run-server' to start the orchestration engine."
echo "=================================================="
