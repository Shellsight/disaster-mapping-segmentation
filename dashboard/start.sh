#!/bin/bash

echo "Starting Disaster Response Dashboard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

echo "Starting Docker containers..."
docker-compose up --build -d

echo "Waiting for services to start..."
sleep 10

echo "Dashboard should be available at:"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8001"
echo "API Docs: http://localhost:8001/docs" 