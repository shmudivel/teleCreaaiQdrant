# Deployment Instructions

This document provides step-by-step instructions for deploying the Telegram bot to the DigitalOcean server.

## Prerequisites

- SSH access to the DigitalOcean server (`~/.ssh/id_ed25519`)
- Git access to the repository
- Docker and Docker Compose installed locally (for testing)

## Local Development

### 1. Making Changes

Make your code changes locally and test them:

```bash
# Run tests
python -m tests.run_tests

# Test locally if possible
docker-compose up
```

### 2. Committing Changes

```bash
# Add changed files
git add .

# Commit with descriptive message
git commit -m "Description of changes"

# Check status
git status
```

### 3. Pushing to GitHub

```bash
# Make sure you're on the deployment branch
git checkout deployment

# Push to GitHub
git push origin deployment
```

## Server Deployment

### 4. Deploying to the Server

```bash
# Connect to server, pull latest code, and restart containers
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cd /root/teleCreaaiQdrant && git pull origin deployment && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml build && docker-compose -f docker-compose.prod.yml up -d"
```

### 5. Verifying Deployment

```bash
# Check if containers are running
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker ps"

# Check recent logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 --tail 20"

# Run the automated check script
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "./check_telegram_bot.sh"
```

## Troubleshooting

### If containers fail to start

```bash
# Check for errors in the logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1"

# Check Docker Compose configuration
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cat docker-compose.prod.yml"

# Try rebuilding without cache
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cd /root/teleCreaaiQdrant && docker-compose -f docker-compose.prod.yml build --no-cache && docker-compose -f docker-compose.prod.yml up -d"
```

### If the bot is not responding

```bash
# Restart just the bot container
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker restart telecreaaiqdrant-bot-1"

# Check for Python errors
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 | grep -i error"
```

### Checking Environment Variables

```bash
# View environment variables in the container
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker exec telecreaaiqdrant-bot-1 env"
```

## Rollback Process

If the new deployment has critical issues:

```bash
# Connect to the server
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41

# Check out previous commit
cd /root/teleCreaaiQdrant
git log --oneline  # Find the previous commit hash
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring After Deployment

Continue to monitor the application after deployment:

```bash
# Follow live logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs -f telecreaaiqdrant-bot-1"

# Run the monitoring script
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "./check_telegram_bot.sh"
```

For more detailed monitoring commands, refer to [MONITORING_README.md](MONITORING_README.md) and [monitoring_workflow.md](monitoring_workflow.md). 