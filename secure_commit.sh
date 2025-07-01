#!/bin/bash

# Secure Commit Script - Automatically clean sensitive data before committing
# Usage: ./secure_commit.sh "Your commit message"

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if commit message is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Please provide a commit message${NC}"
    echo -e "${YELLOW}Usage: ./secure_commit.sh \"Your commit message\"${NC}"
    exit 1
fi

COMMIT_MESSAGE="$1"

echo -e "${BLUE}=== Secure Git Commit Process ===${NC}"
echo -e "${YELLOW}Preparing secure commit with message: \"$COMMIT_MESSAGE\"${NC}"

# Step 1: Run security cleanup
echo -e "\n${BLUE}Step 1: Running security cleanup...${NC}"
if [ -f "./cleanup_secrets.sh" ]; then
    chmod +x ./cleanup_secrets.sh
    ./cleanup_secrets.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Security cleanup failed. Aborting commit.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Security cleanup completed successfully.${NC}"
else
    echo -e "${RED}Error: cleanup_secrets.sh not found!${NC}"
    echo -e "${YELLOW}Please ensure the cleanup script is in the current directory.${NC}"
    exit 1
fi

# Step 2: Check git status
echo -e "\n${BLUE}Step 2: Checking git status...${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${YELLOW}No changes to commit.${NC}"
    exit 0
fi

# Step 3: Add all changes
echo -e "\n${BLUE}Step 3: Adding changes to git...${NC}"
git add .
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to add changes to git.${NC}"
    exit 1
fi
echo -e "${GREEN}Changes added successfully.${NC}"

# Step 4: Commit changes
echo -e "\n${BLUE}Step 4: Committing changes...${NC}"
git commit -m "$COMMIT_MESSAGE"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to commit changes.${NC}"
    exit 1
fi
echo -e "${GREEN}Changes committed successfully.${NC}"

# Step 5: Ask if user wants to push
echo -e "\n${YELLOW}Do you want to push to origin/deployment? (y/n):${NC}"
read -r PUSH_RESPONSE

if [[ "$PUSH_RESPONSE" =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Step 5: Pushing to origin/deployment...${NC}"
    git push origin deployment
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to push to origin/deployment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Successfully pushed to origin/deployment.${NC}"
else
    echo -e "${YELLOW}Skipping push. You can push later with: git push origin deployment${NC}"
fi

echo -e "\n${GREEN}🎉 Secure commit completed successfully! 🎉${NC}"
echo -e "${YELLOW}Summary:${NC}"
echo -e "- Security cleanup: ✓"
echo -e "- Git commit: ✓"
if [[ "$PUSH_RESPONSE" =~ ^[Yy]$ ]]; then
    echo -e "- Git push: ✓"
else
    echo -e "- Git push: Skipped"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
if [[ ! "$PUSH_RESPONSE" =~ ^[Yy]$ ]]; then
    echo -e "1. Push when ready: ${BLUE}git push origin deployment${NC}"
fi
echo -e "2. Deploy to server: ${BLUE}./deploy.sh${NC}"
echo -e "3. Monitor deployment: Check logs and verify functionality" 