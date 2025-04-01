#!/bin/bash

# Simple monitoring script for the Telegram bot service
# Usage: ./monitor.sh [email@example.com]

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Email for notifications
EMAIL_TO="${1:-root@localhost}"

# Application name for logs
APP_NAME="Telegram Bot"

# Timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Log file
LOG_FILE="/var/log/telebot_monitor.log"
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="./telebot_monitor.log"

# Function to log messages
log_message() {
    echo -e "$1"
    echo "[$TIMESTAMP] $2" >> "$LOG_FILE"
}

# Check if docker is running
if ! docker info >/dev/null 2>&1; then
    log_message "${RED}Docker is not running!${NC}" "ERROR: Docker is not running"
    
    # Send email alert
    echo "ALERT: Docker is not running on $(hostname) at $TIMESTAMP" | mail -s "$APP_NAME Monitor Alert" "$EMAIL_TO" 2>/dev/null
    exit 1
fi

# Check if containers are running
CONTAINERS=$(docker-compose -f docker-compose.prod.yml ps -q 2>/dev/null)
if [ -z "$CONTAINERS" ]; then
    log_message "${RED}No containers are running!${NC}" "ERROR: No containers are running"
    
    # Send email alert
    echo "ALERT: $APP_NAME containers are not running on $(hostname) at $TIMESTAMP" | mail -s "$APP_NAME Monitor Alert" "$EMAIL_TO" 2>/dev/null
    
    # Attempt restart
    log_message "${YELLOW}Attempting to restart...${NC}" "INFO: Attempting to restart"
    docker-compose -f docker-compose.prod.yml up -d
    
    # Check if restart was successful
    sleep 10
    if [ -z "$(docker-compose -f docker-compose.prod.yml ps -q 2>/dev/null)" ]; then
        log_message "${RED}Restart failed!${NC}" "ERROR: Restart failed"
        exit 1
    else
        log_message "${GREEN}Restart successful!${NC}" "INFO: Restart successful"
    fi
else
    # Check container health
    UNHEALTHY_CONTAINERS=0
    for CONTAINER_ID in $CONTAINERS; do
        STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_ID" 2>/dev/null)
        if [ "$STATUS" != "running" ]; then
            CONTAINER_NAME=$(docker inspect --format='{{.Name}}' "$CONTAINER_ID" 2>/dev/null | cut -c2-)
            log_message "${RED}Container $CONTAINER_NAME is not running (status: $STATUS)${NC}" "ERROR: Container $CONTAINER_NAME is not running (status: $STATUS)"
            ((UNHEALTHY_CONTAINERS++))
        fi
    done
    
    if [ "$UNHEALTHY_CONTAINERS" -gt 0 ]; then
        log_message "${YELLOW}Found $UNHEALTHY_CONTAINERS unhealthy containers. Restarting...${NC}" "WARNING: Found $UNHEALTHY_CONTAINERS unhealthy containers"
        docker-compose -f docker-compose.prod.yml restart
        
        # Send email alert
        echo "ALERT: $UNHEALTHY_CONTAINERS containers were unhealthy on $(hostname) at $TIMESTAMP and were restarted" | mail -s "$APP_NAME Monitor Alert" "$EMAIL_TO" 2>/dev/null
    else
        log_message "${GREEN}All containers are running properly.${NC}" "INFO: All containers are running properly"
        
        # Check resource usage
        CPU_USAGE=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $CONTAINERS)
        log_message "${GREEN}Resource usage:${NC}\n$CPU_USAGE" "INFO: Resource usage: $CPU_USAGE"
    fi
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    log_message "${RED}Disk usage is high: ${DISK_USAGE}%${NC}" "WARNING: Disk usage is high: ${DISK_USAGE}%"
    
    # Send email alert
    echo "ALERT: Disk usage on $(hostname) is at ${DISK_USAGE}% at $TIMESTAMP" | mail -s "$APP_NAME Monitor Alert" "$EMAIL_TO" 2>/dev/null
fi

log_message "${GREEN}Monitoring completed.${NC}" "INFO: Monitoring completed"

# Example of how to use this script in a crontab:
# */10 * * * * /path/to/monitor.sh admin@example.com > /dev/null 2>&1 