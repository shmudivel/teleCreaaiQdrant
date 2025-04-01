# Daily Monitoring Commands for Telegram Bot

A quick reference guide for daily monitoring of your Telegram Bot deployment.

## Quick Status Check

```bash
# Connect to your server
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41

# Check if containers are running
docker ps

# Check system resources
df -h                # Disk space
free -m              # Memory usage
uptime               # Load average
```

## Log Checking Workflow

### 1. Check Bot Logs

```bash
# View recent bot logs (last 50 lines)
docker logs --tail 50 telecreaaiqdrant-bot-1

# Follow live bot logs (use when actively debugging)
docker logs -f telecreaaiqdrant-bot-1

# Check for errors in bot logs
docker logs telecreaaiqdrant-bot-1 | grep -i "error\|exception\|warning" | tail -50
```

### 2. Check Database Logs

```bash
# View recent Qdrant logs
docker logs --tail 50 telecreaaiqdrant-qdrant-1

# Check for errors in Qdrant logs
docker logs telecreaaiqdrant-qdrant-1 | grep -i "error\|warn" | tail -50
```

### 3. Check Resource Usage

```bash
# View container resource usage
docker stats --no-stream

# Check if any process is consuming too much CPU
top -b -n 1 | head -20
```

## Common Tasks

```bash
# Restart the bot service if needed
docker restart telecreaaiqdrant-bot-1

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Run a backup
./backup.sh /var/backups/telegram-bot
```

## Remote One-Liner Commands

Run these from your local machine for quick checks:

```bash
# Quick status check (one command)
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "echo '=== CONTAINERS ==='; docker ps; echo -e '\n=== DISK SPACE ==='; df -h | grep -E 'Filesystem|/$'; echo -e '\n=== MEMORY ==='; free -m | grep -E 'total|Mem:'"

# Quick log check (one command)
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "echo '=== BOT LOGS (LAST 20 LINES) ==='; docker logs telecreaaiqdrant-bot-1 --tail 20; echo -e '\n=== QDRANT LOGS (LAST 10 LINES) ==='; docker logs telecreaaiqdrant-qdrant-1 --tail 10"

# Check for errors only (one command)
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "echo '=== BOT ERRORS ==='; docker logs telecreaaiqdrant-bot-1 | grep -i 'error\|exception\|warning' | tail -20"
``` 