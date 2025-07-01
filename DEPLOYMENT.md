# Secure Deployment Instructions

This document provides step-by-step instructions for securely deploying the Telegram bot to the DigitalOcean server with automated security cleanup.

## Prerequisites

- SSH access to the DigitalOcean server (`~/.ssh/id_ed25519`)
- Git access to the repository
- Docker and Docker Compose installed locally (for testing)
- Security cleanup scripts (`cleanup_secrets.sh`, `secure_commit.sh`)

## 🔒 Security-First Development Workflow

**IMPORTANT**: This project includes automated security cleanup to prevent accidentally committing API keys and sensitive data.

### 1. Making Changes

Make your code changes locally and test them:

```bash
# Run tests
python -m tests.run_tests

# Test locally if possible
docker-compose up
```

### 2. Secure Committing (RECOMMENDED)

Use the automated secure commit script:

```bash
# Make scripts executable (first time only)
chmod +x cleanup_secrets.sh secure_commit.sh

# Secure commit with automatic cleanup
./secure_commit.sh "Description of your changes"
```

This script automatically:
- ✅ Removes hardcoded API keys and sensitive data
- ✅ Updates .gitignore for security
- ✅ Commits your changes safely
- ✅ Optionally pushes to GitHub

### 3. Manual Security Process (Alternative)

If you prefer manual control:

```bash
# STEP 1: Clean sensitive data BEFORE committing
./cleanup_secrets.sh

# STEP 2: Review and commit changes
git add .
git commit -m "Description of changes"

# STEP 3: Push to GitHub
git push origin deployment
```

### 4. Quick Deployment Check

Before any commit, verify no sensitive data:

```bash
# Quick security scan
grep -r "sk-ant-\|sk-proj-\|GOCSPX-" . --exclude-dir=venv || echo "✅ No API keys found"
```

## 🚀 Automated Secure Deployment

### 4. One-Command Secure Deployment

The deployment script now includes automated security cleanup:

```bash
# Secure deployment with automatic cleanup
./deploy.sh
```

This script automatically:
- 🔒 Runs security cleanup before deployment
- 📝 Commits any security changes
- ⬆️ Pushes cleaned code to GitHub  
- 🖥️ Deploys to DigitalOcean server
- ✅ Verifies deployment success

### 5. Manual Deployment Steps (Alternative)

If you prefer manual control over each step:

```bash
# Step 1: Security cleanup
./cleanup_secrets.sh

# Step 2: Commit and push
git add . && git commit -m "Security cleanup before deployment"
git push origin deployment

# Step 3: Deploy to server
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cd /root/teleCreaaiQdrant && git pull origin deployment && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml build && docker-compose -f docker-compose.prod.yml up -d"
```

### 6. Verifying Deployment

```bash
# Check if containers are running
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker ps"

# Check recent logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 --tail 20"

# Run the automated check script
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "./check_telegram_bot.sh"
```

## 🔐 Security Features

### Automated Security Cleanup

The project includes comprehensive security measures:

**`cleanup_secrets.sh`** - Removes sensitive data:
- ❌ Hardcoded API keys (Anthropic, OpenAI, Google)
- ❌ OAuth credentials and tokens
- ❌ Sensitive files (tokens, credentials)
- ✅ Replaces with environment variables
- ✅ Updates .gitignore patterns

**`secure_commit.sh`** - Safe git operations:
- 🔒 Runs security cleanup automatically
- 📝 Commits changes securely
- ⬆️ Optional push to GitHub

### Required Environment Variables

Ensure these are set on your deployment server:

```bash
# Core API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here

# Google Services
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service_account.json

# Additional Services
ELEVENLABS_API_KEY=your_key_here
HEYGEN_API_KEY=your_key_here
QDRANT_API_KEY=your_key_here
```

### Security Best Practices

1. **Never commit actual API keys** - Always use environment variables
2. **Run cleanup before commits** - Use `./secure_commit.sh` or `./cleanup_secrets.sh`
3. **Review .env.example** - Template for required environment variables
4. **Monitor for secrets** - Scripts scan for common patterns
5. **Keep backups secure** - Backup files are automatically excluded

## Troubleshooting

### Security Issues

#### If sensitive data is detected during push:
```bash
# Clean the repository
./cleanup_secrets.sh

# If git history needs cleaning
git filter-branch --force --tree-filter 'find . -name "*.py" -exec sed -i "s/sk-ant-[^\"]*\"/__REMOVED_API_KEY__\"/g" {} \;' HEAD
git gc --prune=now --aggressive

# Recommit and push
git add . && git commit -m "Security: Remove sensitive data"
git push --force-with-lease origin deployment
```

#### Environment variables not working:
```bash
# Check if .env.example exists and copy it
cp .env.example .env
# Edit .env with your actual values

# On server, verify environment variables
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker exec telecreaaiqdrant-bot-1 env | grep API"
```

### Application Issues

#### If containers fail to start:

```bash
# Check for errors in the logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1"

# Check Docker Compose configuration
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cat docker-compose.prod.yml"

# Try rebuilding without cache
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "cd /root/teleCreaaiQdrant && docker-compose -f docker-compose.prod.yml build --no-cache && docker-compose -f docker-compose.prod.yml up -d"
```

#### If the bot is not responding:

```bash
# Restart just the bot container
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker restart telecreaaiqdrant-bot-1"

# Check for Python errors
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 | grep -i error"
```

#### Checking Environment Variables:

```bash
# View environment variables in the container
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker exec telecreaaiqdrant-bot-1 env"

# Test specific API key availability
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker exec telecreaaiqdrant-bot-1 python -c 'import os; print(\"ANTHROPIC_API_KEY:\", \"✓\" if os.getenv(\"ANTHROPIC_API_KEY\") else \"✗\")'"
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