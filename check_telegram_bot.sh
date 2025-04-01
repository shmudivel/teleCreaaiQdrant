#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server details
SERVER_IP="104.248.170.41"
SSH_KEY="~/.ssh/id_ed25519"
SSH_USER="root"

# Print section header
print_header() {
    echo -e "\n${GREEN}===== $1 =====${NC}\n"
}

# Print error message
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Execute SSH command
run_ssh_command() {
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "$1"
    return $?
}

# Check if we can connect to the server
print_header "TESTING CONNECTION TO SERVER"
if run_ssh_command "echo Connection successful"; then
    echo "Server connection established."
else
    print_error "Could not connect to server $SERVER_IP"
    exit 1
fi

# Check if docker is running
print_header "CHECKING DOCKER SERVICE"
if run_ssh_command "systemctl is-active docker"; then
    echo "Docker service is running."
else
    print_error "Docker service is not running!"
    run_ssh_command "systemctl status docker"
    exit 1
fi

# Check containers status
print_header "CHECKING CONTAINERS"
CONTAINERS=$(run_ssh_command "docker ps --format '{{.Names}}: {{.Status}}'")
echo "$CONTAINERS"

# Count running containers
RUNNING_COUNT=$(echo "$CONTAINERS" | wc -l)
if [ "$RUNNING_COUNT" -lt 2 ]; then
    print_warning "Not all expected containers are running!"
fi

# Check disk space
print_header "CHECKING DISK SPACE"
DISK_USAGE=$(run_ssh_command "df -h | grep -E 'Filesystem|/$'")
echo "$DISK_USAGE"

# Alert if disk usage is over 85%
DISK_PERCENT=$(echo "$DISK_USAGE" | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_PERCENT" -gt 85 ]; then
    print_warning "Disk usage is high: ${DISK_PERCENT}%"
fi

# Check memory usage
print_header "CHECKING MEMORY"
MEM_USAGE=$(run_ssh_command "free -m | grep -E 'total|Mem:'")
echo "$MEM_USAGE"

# Check recent bot logs
print_header "RECENT BOT LOGS (LAST 10 LINES)"
run_ssh_command "docker logs telecreaaiqdrant-bot-1 --tail 10"

# Check for errors in logs
print_header "CHECKING FOR ERRORS IN LOGS"
ERROR_COUNT=$(run_ssh_command "docker logs telecreaaiqdrant-bot-1 | grep -i 'error\|exception\|warning' | wc -l")
if [ "$ERROR_COUNT" -gt 0 ]; then
    print_warning "Found $ERROR_COUNT errors/warnings in logs"
    run_ssh_command "docker logs telecreaaiqdrant-bot-1 | grep -i 'error\|exception\|warning' | tail -5"
else
    echo "No errors found in logs."
fi

print_header "MONITORING COMPLETED"
echo "The Telegram Bot application appears to be running normally."
echo "For more detailed information, connect to the server:"
echo "ssh -i $SSH_KEY $SSH_USER@$SERVER_IP" 