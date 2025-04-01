#!/bin/bash

# Exit on error
set -e

# Configuration variables - update these with your values
DROPLET_IP="104.248.170.41"
SSH_USER="root"
SSH_KEY_PATH="~/.ssh/id_ed25519"
REPO_URL="https://github.com/shmudivel/teleCreaaiQdrant.git"
BRANCH="deployment"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
function echo_color {
    echo -e "${2}${1}${NC}"
}

echo_color "Starting deployment to Digital Ocean..." "${GREEN}"

# Check if IP is provided
if [ -z "$DROPLET_IP" ]; then
    echo_color "Error: Please set DROPLET_IP in the script" "${RED}"
    exit 1
fi

echo_color "1. Connecting to Digital Ocean droplet..." "${GREEN}"
ssh -i $SSH_KEY_PATH $SSH_USER@$DROPLET_IP << 'ENDSSH'
    echo "Connected to server"
    
    # Install Docker if not already installed
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update
        apt-get install -y docker-ce
    else
        echo "Docker already installed"
    fi

    # Install Docker Compose if not already installed
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose already installed"
    fi

    # Use existing project directory
    APP_DIR="/root/teleCreaaiQdrant"
    
    cd $APP_DIR
    
    # Backup current configuration
    echo "Backing up current configuration..."
    if [ -f ".env.prod" ]; then
        cp .env.prod .env.prod.backup
    fi
    
    # Backup any custom credentials
    if [ -f "bustling-folio-439811-h8-539f8ab05fa7.json" ]; then
        cp bustling-folio-439811-h8-539f8ab05fa7.json bustling-folio-439811-h8-539f8ab05fa7.json.backup
    fi
    
    # Stop current containers
    echo "Stopping current services..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Update repository
    echo "Updating repository..."
    git fetch
    git checkout main
    git pull
    
    # Update to deployment branch if it exists
    if git ls-remote --heads origin deployment | grep deployment; then
        echo "Checking out deployment branch..."
        git checkout deployment || git checkout -b deployment origin/deployment
    fi
    
    # Restore configuration from backup
    if [ -f ".env.prod.backup" ]; then
        echo "Restoring .env.prod from backup..."
        cp .env.prod.backup .env.prod
    fi
    
    # Restore credentials
    if [ -f "bustling-folio-439811-h8-539f8ab05fa7.json.backup" ]; then
        echo "Restoring Google credentials from backup..."
        cp bustling-folio-439811-h8-539f8ab05fa7.json.backup bustling-folio-439811-h8-539f8ab05fa7.json
    fi
    
    # Build and start containers
    echo "Building and starting containers..."
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Check if containers are running
    echo "Checking container status..."
    docker ps
    
    echo "Deployment completed."
ENDSSH

echo_color "Deployment script completed." "${GREEN}"
echo_color "Your application has been updated on the DigitalOcean droplet!" "${GREEN}" 