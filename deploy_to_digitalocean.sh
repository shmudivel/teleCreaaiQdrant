#!/bin/bash

# Exit on error
set -e

# Configuration variables - update these with your values
DROPLET_IP=""
SSH_USER="root"
SSH_KEY_PATH="~/.ssh/id_rsa"
REPO_URL="https://github.com/yourusername/teleCreaaiQdrant.git"
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

    # Create app directory if it doesn't exist
    APP_DIR="/opt/telecreat"
    if [ ! -d "$APP_DIR" ]; then
        echo "Creating application directory..."
        mkdir -p $APP_DIR
    fi
    
    cd $APP_DIR
    
    # Clone or update repository
    if [ ! -d ".git" ]; then
        echo "Cloning repository..."
        git clone -b BRANCH REPO_URL .
    else
        echo "Updating repository..."
        git fetch
        git checkout BRANCH
        git pull
    fi
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env.prod" ]; then
        echo "Warning: .env.prod file not found. Please upload it manually."
    fi
    
    # Copy Google credentials if needed
    if [ ! -f "bustling-folio-439811-h8-539f8ab05fa7.json" ]; then
        echo "Warning: Google credentials file not found. Please upload it manually."
    fi
    
    # Build and start containers
    echo "Building and starting containers..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Check if containers are running
    echo "Checking container status..."
    docker ps
    
    echo "Deployment completed."
ENDSSH

# Replace placeholders with actual values
sed -i "s|REPO_URL|$REPO_URL|g; s|BRANCH|$BRANCH|g" deploy_to_digitalocean.sh

echo_color "Deployment script completed." "${GREEN}"
echo_color "IMPORTANT:" "${RED}"
echo_color "1. Update DROPLET_IP, SSH_USER, SSH_KEY_PATH, and REPO_URL in this script" "${RED}"
echo_color "2. Make sure you've copied your Google credentials and .env.prod files to the server" "${RED}"
echo_color "3. Run this script with: bash deploy_to_digitalocean.sh" "${RED}" 