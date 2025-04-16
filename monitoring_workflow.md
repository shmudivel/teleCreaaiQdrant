# Monitoring Workflow for Telegram Bot on DigitalOcean

This document provides commands to monitor your deployed Telegram bot project on DigitalOcean.

## Basic Connection

```bash
# Connect to your DigitalOcean Droplet
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41
```

## Container Management

```bash
# List all running containers
docker ps

# List all containers (including stopped ones)
docker ps -a

# View container statistics (CPU, memory, network, etc.)
docker stats

# Restart all containers
docker-compose -f docker-compose.prod.yml restart

# Stop all containers
docker-compose -f docker-compose.prod.yml down

# Start all containers
docker-compose -f docker-compose.prod.yml up -d
```

## Log Monitoring

```bash
# View logs from the bot container
docker logs telecreaaiqdrant-bot-1

# View logs from the Qdrant container
docker logs telecreaaiqdrant-qdrant-1

# Follow live logs from the bot container (press Ctrl+C to exit)
docker logs -f telecreaaiqdrant-bot-1

# Follow live logs from the Qdrant container (press Ctrl+C to exit)
docker logs -f telecreaaiqdrant-qdrant-1

# View logs with timestamps
docker logs --timestamps telecreaaiqdrant-bot-1

# View only the last 100 lines of logs
docker logs --tail 100 telecreaaiqdrant-bot-1

# View logs from both containers
docker-compose -f docker-compose.prod.yml logs
```

## Resource Monitoring

```bash
# Check server resource usage
htop

# Check disk space usage
df -h

# Check memory usage
free -m

# Check CPU information
lscpu

# Monitor system resources (press q to exit)
top
```

## Database Management

```bash
# Get Qdrant status through HTTP API
curl http://localhost:6333

# Check Qdrant collections
curl http://localhost:6333/collections
```

## Backup Commands

```bash
# Run the backup script
./backup.sh /path/to/backup/directory

# List available backups
ls -la /var/backups/telegram-bot/
```

## Common Troubleshooting

```bash
# Check if Docker service is running
systemctl status docker

# Inspect bot container details
docker inspect telecreaaiqdrant-bot-1

# View bot container environment variables
docker exec telecreaaiqdrant-bot-1 env

# Check container network
docker network ls

# Prune unused Docker resources
docker system prune -a
```

## Application Health Check

```bash
# Check if Telegram Bot is running properly
docker exec telecreaaiqdrant-bot-1 ps aux | grep python

# Check Python version used inside the container
docker exec telecreaaiqdrant-bot-1 python --version

# Check installed Python packages
docker exec telecreaaiqdrant-bot-1 pip list
```

## Deployment Workflow

When you need to redeploy or update your application:

```bash
# 1. Connect to the server
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41

# 2. Navigate to the project directory
cd /root/teleCreaaiQdrant

# 3. Pull the latest changes
git pull origin deployment

# 4. Build and restart containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Check if containers are running
docker ps

# 6. Check logs for any errors
docker logs telecreaaiqdrant-bot-1
```

## SSH Connection Troubleshooting

If you're having issues connecting to the server:

```bash
# Test SSH connection with verbose output
ssh -v -i ~/.ssh/id_ed25519 root@104.248.170.41

# Check if the SSH key has correct permissions
chmod 600 ~/.ssh/id_ed25519

# Verify SSH key is being used by SSH agent
ssh-add -l

# Add your key to SSH agent if needed
ssh-add ~/.ssh/id_ed25519

# Test connectivity to the server
ping 104.248.170.41

# Connection with alternative port if standard port is blocked
ssh -i ~/.ssh/id_ed25519 -p 22 root@104.248.170.41
```

## Scheduled Monitoring Script

Create a script to check your services regularly:

```bash
# Create a monitoring script
cat > check_services.sh << 'EOF'
#!/bin/bash

echo "=== Checking Docker services at $(date) ==="
docker ps

echo -e "\n=== Checking disk space ==="
df -h | grep -E "Filesystem|/$"

echo -e "\n=== Checking memory usage ==="
free -m | grep -E "total|Mem:"

echo -e "\n=== Checking container logs (last 10 lines) ==="
echo "Bot logs:"
docker logs --tail 10 telecreaaiqdrant-bot-1
echo -e "\nQdrant logs:"
docker logs --tail 10 telecreaaiqdrant-qdrant-1
EOF

# Make it executable
chmod +x check_services.sh

# Run whenever needed
./check_services.sh

# Add to crontab to run every hour
# crontab -e
# Add this line: 0 * * * * /root/teleCreaaiQdrant/check_services.sh > /var/log/service_check.log 2>&1
```

## Remote Monitoring from Your Local Machine

Run these commands from your local terminal:

```bash
# Check if services are running
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker ps"

# View the latest logs
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 --tail 50"

# Check server resources
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "free -m && df -h"
``` 