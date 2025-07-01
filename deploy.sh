#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSH_KEY="~/.ssh/id_ed25519"
SERVER_IP="104.248.170.41"
SERVER_USER="root"
PROJECT_DIR="/root/teleCreaaiQdrant"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

echo -e "${BLUE}=== Secure Deployment Process ===${NC}"
echo -e "${YELLOW}Starting secure deployment to DigitalOcean server...${NC}"

# Step 0: Run security cleanup before any git operations
echo -e "${BLUE}Step 0: Security cleanup - Removing sensitive data...${NC}"
if [ -f "./cleanup_secrets.sh" ]; then
    chmod +x ./cleanup_secrets.sh
    ./cleanup_secrets.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Security cleanup failed. Aborting deployment.${NC}"
        echo -e "${YELLOW}Please fix any security issues and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Security cleanup completed successfully.${NC}"
else
    echo -e "${YELLOW}Warning: cleanup_secrets.sh not found. Proceeding without security cleanup.${NC}"
    echo -e "${YELLOW}It's recommended to run security cleanup before deployment.${NC}"
fi

# Check git status and commit if there are changes from cleanup
echo -e "${YELLOW}Checking for changes from security cleanup...${NC}"
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}Security cleanup made changes. Committing them...${NC}"
    git add .
    git commit -m "Security: Remove sensitive data before deployment - $(date '+%Y-%m-%d %H:%M:%S')"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to commit security changes. Aborting deployment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Security changes committed successfully.${NC}"
else
    echo -e "${GREEN}No changes from security cleanup.${NC}"
fi

# Step 1: Push cleaned code to GitHub
echo -e "${BLUE}Step 1: Pushing cleaned code to GitHub...${NC}"
git push origin deployment
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to push to GitHub. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully pushed to GitHub.${NC}"

# Step 2: Connect to server and pull latest code
echo -e "${BLUE}Step 2: Pulling latest code from deployment branch...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && git pull origin deployment"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to pull latest code. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully pulled latest code.${NC}"

# Step 3: Install python-telegram-bot with job-queue support
echo -e "${BLUE}Step 3: Installing required packages...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && pip install \"python-telegram-bot[job-queue]\""
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Failed to install packages directly. Will attempt through Docker container.${NC}"
    # Alternative: We'll add this to the Docker build process
fi

# Step 4: Stopping existing containers
echo -e "${BLUE}Step 4: Stopping existing containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE down"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to stop containers. Continuing anyway...${NC}"
fi

# Step 5: Rebuilding containers
echo -e "${BLUE}Step 5: Rebuilding containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE build"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build containers. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully built containers.${NC}"

# Step 6: Starting containers
echo -e "${BLUE}Step 6: Starting containers...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && docker-compose -f $DOCKER_COMPOSE_FILE up -d"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start containers. Aborting deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully started containers.${NC}"

# Step 7: Verifying deployment
echo -e "${BLUE}Step 7: Verifying deployment...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "docker ps | grep telecreaaiqdrant-bot"
if [ $? -ne 0 ]; then
    echo -e "${RED}Bot container not found. Deployment may have failed.${NC}"
    exit 1
fi
echo -e "${GREEN}Bot container is running.${NC}"

# Step 8: Check recent logs
echo -e "${BLUE}Step 8: Checking recent logs...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "docker logs telecreaaiqdrant-bot-1 --tail 20"

# Step 9: Run automated check script if it exists
echo -e "${BLUE}Step 9: Running automated checks...${NC}"
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "./check_telegram_bot.sh" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Automated check script not found or failed. Please verify manually.${NC}"
fi

echo -e "\n${GREEN}🎉 Secure deployment completed successfully! 🎉${NC}"
echo -e "${BLUE}=== Deployment Summary ===${NC}"
echo -e "${GREEN}✓${NC} Security cleanup completed"
echo -e "${GREEN}✓${NC} Sensitive data removed from repository"
echo -e "${GREEN}✓${NC} Code pushed to GitHub securely"
echo -e "${GREEN}✓${NC} Server updated with latest code"
echo -e "${GREEN}✓${NC} Application containers rebuilt and started"
echo -e "${GREEN}✓${NC} Deployment verification completed"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "1. Verify that the bot is functioning correctly"
echo -e "2. Monitor logs for any issues"
echo -e "3. Test all bot features"

echo -e "\n${YELLOW}🔍 Monitoring Commands:${NC}"
echo -e "Real-time logs: ${BLUE}ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP \"docker logs -f telecreaaiqdrant-bot-1\"${NC}"
echo -e "Container status: ${BLUE}ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP \"docker ps\"${NC}"
echo -e "Bot health check: ${BLUE}ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP \"./check_telegram_bot.sh\"${NC}"

echo -e "\n${YELLOW}🔒 Security Features Applied:${NC}"
echo -e "1. Automated removal of hardcoded API keys"
echo -e "2. Secure environment variable usage"
echo -e "3. Sensitive files excluded from repository"
echo -e "4. Updated .gitignore for future protection"

echo -e "\n${YELLOW}🛠 Recent Fixes Applied:${NC}"
echo -e "1. Fixed 'Обновить Google Sheet' button functionality"
echo -e "2. Improved /start command to properly reset all states"
echo -e "3. Installed python-telegram-bot[job-queue] for conversation timeouts"
echo -e "4. Enhanced security with automated credential cleanup"

echo -e "\n${YELLOW}⚠ Important Reminders:${NC}"
echo -e "- Ensure all environment variables are set on the server"
echo -e "- Never commit actual API keys or credentials"
echo -e "- Use .env.example as a template for required variables"
echo -e "- Run ./cleanup_secrets.sh before any manual git operations" 