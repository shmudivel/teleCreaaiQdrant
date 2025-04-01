#!/bin/bash

# Exit on error
set -e

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting the Telegram Bot application...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Starting Docker...${NC}"
    systemctl start docker
    sleep 5
fi

# Check if .env.prod file exists
if [ ! -f ".env.prod" ]; then
    echo -e "${RED}Error: .env.prod file not found. Please create this file first.${NC}"
    exit 1
fi

# Check if Google credentials file exists
if [ ! -f "bustling-folio-439811-h8-539f8ab05fa7.json" ]; then
    echo -e "${RED}Error: Google credentials file not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Running Docker Compose...${NC}"
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Check if containers are running
if [ $(docker-compose -f docker-compose.prod.yml ps -q | wc -l) -gt 0 ]; then
    echo -e "${GREEN}Application started successfully!${NC}"
    docker-compose -f docker-compose.prod.yml ps
else
    echo -e "${RED}Error: Containers failed to start.${NC}"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

echo -e "${GREEN}Showing logs (press Ctrl+C to exit)${NC}"
docker-compose -f docker-compose.prod.yml logs -f 