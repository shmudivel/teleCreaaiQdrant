# Telegram Bot Monitoring Guide

This repository contains several tools to help you monitor and maintain your Telegram bot deployment on DigitalOcean.

## Quick Start

For a quick health check of your application, run:

```bash
./check_telegram_bot.sh
```

This script will:
- Test connection to your server
- Check Docker service status
- Verify container status
- Check disk space and memory usage
- Display recent logs
- Check for errors in logs

## Available Documentation

We provide several reference documents for monitoring:

1. **monitoring_workflow.md** - Comprehensive reference with all commands for monitoring and managing your deployment.

2. **daily_monitoring.md** - Focused guide with the most essential daily monitoring commands.

3. **check_telegram_bot.sh** - Automated script to quickly check the application status.

## Monitoring Workflow

Our recommended monitoring workflow is:

### 1. Daily Quick Check
Run the automated check script once daily:

```bash
./check_telegram_bot.sh
```

### 2. Regular Log Review
Check application logs at least once per day:

```bash
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41 "docker logs telecreaaiqdrant-bot-1 --tail 50"
```

### 3. Weekly Maintenance
Once per week:
- Run a backup
- Check for disk space issues
- Prune unused Docker resources

```bash
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41
./backup.sh /var/backups/telegram-bot
df -h
docker system prune -f
```

## Setting Up Automated Monitoring

To set up automated monitoring, you can:

1. **On the server**: Set up a cron job to run the check script and email results:

```bash
# Copy the check script to the server
scp -i ~/.ssh/id_ed25519 check_telegram_bot.sh root@104.248.170.41:/root/teleCreaaiQdrant/

# Connect to the server
ssh -i ~/.ssh/id_ed25519 root@104.248.170.41

# Add a cron job (this runs daily at 8 AM)
crontab -e
# Add the following line:
0 8 * * * /root/teleCreaaiQdrant/check_telegram_bot.sh > /var/log/bot_status.log 2>&1
```

2. **On your local machine**: Schedule the script to run from your computer.

## Troubleshooting Common Issues

If you encounter issues, refer to the comprehensive command reference in `monitoring_workflow.md`.

Common troubleshooting steps:

1. **Bot not responding**:
   ```bash
   docker restart telecreaaiqdrant-bot-1
   ```

2. **Application errors**:
   ```bash
   docker logs telecreaaiqdrant-bot-1 | grep -i "error"
   ```

3. **Complete restart**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Contact Support

If you encounter issues you can't resolve, contact the development team for assistance. 