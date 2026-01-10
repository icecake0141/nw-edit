#!/bin/bash

# Start script for Network Device Configuration Manager

echo "Starting Network Device Configuration Manager..."
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "Starting with docker-compose..."
    docker-compose up -d
    echo ""
    echo "✓ Services started!"
    echo ""
    echo "Access the application:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose down"
else
    echo "Error: docker-compose not found"
    echo "Please install Docker and Docker Compose first"
    exit 1
fi
