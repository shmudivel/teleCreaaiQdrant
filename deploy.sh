#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SSH_KEY="~/.ssh/id_ed25519"
SERVER_IP="104.248.170.41"
SERVER_USER="root"
PROJECT_DIR="/root/teleCreaaiQdrant"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

echo -e "${YELLOW}Starting deployment to DigitalOcean server...${NC}"

# Step 1: Connect to server and pull latest code
echo -e "${YELLOW}Pulling latest code from deployment branch...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && git pull origin deployment"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to pull latest code. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully pulled latest code.${NC}"

# Step 2: Install python-telegram-bot with job-queue support
echo -e "${YELLOW}Installing required packages...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && pip install \"python-telegram-bot[job-queue]\""
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Failed to install packages directly. Will attempt through Docker container.${NC}"
    # Alternative: We'll add this to the Docker build process
fi

# Step 3: Stopping existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE down"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to stop containers. Continuing anyway...${NC}"
fi

# Step 4: Rebuilding containers
echo -e "${YELLOW}Rebuilding containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE build"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build containers. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully built containers.${NC}"

# Step 5: Starting containers
echo -e "${YELLOW}Starting containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE up -d"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start containers. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully started containers.${NC}"

# Step 6: Verifying deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "docker ps | grep telecreaaiqdrant-bot"
if [ $? -ne 0 ]; then
    echo -e "${RED}Bot container not found. Deployment may have failed.${NC}"
    exit 1
fi
echo -e "${GREEN}Bot container is running.${NC}"

# Step 7: Check recent logs
echo -e "${YELLOW}Checking recent logs...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "docker logs telecreaaiqdrant-bot-1 --tail 20"

# Step 8: Run automated check script if it exists
echo -e "${YELLOW}Running automated checks...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "./check_telegram_bot.sh" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Automated check script not found or failed. Please verify manually.${NC}"
fi

echo -e "${GREEN}Deployment completed! Please verify that the bot is functioning correctly.${NC}"
echo -e "${YELLOW}To monitor logs in real-time, run:${NC}"
echo -e "ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP \"docker logs -f telecreaaiqdrant-bot-1\""

# Reminder about the fixes
echo -e "\n${YELLOW}Reminder of fixes applied:${NC}"
echo -e "1. Fixed 'Обновить Google Sheet' button functionality"
echo -e "2. Improved /start command to properly reset all states"
echo -e "3. Installed python-telegram-bot[job-queue] for conversation timeouts"
echo -e "\n${YELLOW}Known issues:${NC}"
echo -e "- 'Создать текстовый пост' button may still have issues"
echo -e "  If this button doesn't work, check Google API credentials and add more logging" 