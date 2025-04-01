#!/bin/bash

# Backup script for Telegram Bot application data
# Usage: ./backup.sh [backup_dir]

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Backup directory (default or provided)
BACKUP_DIR="${1:-/var/backups/telegram-bot}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/qdrant_backup_${TIMESTAMP}.tar.gz"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}Starting backup process...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running.${NC}"
    exit 1
fi

# Check if containers are running
if [ -z "$(docker-compose -f docker-compose.prod.yml ps -q qdrant)" ]; then
    echo -e "${RED}Error: Qdrant container is not running.${NC}"
    exit 1
fi

# Create a temporary directory for the backup
TEMP_DIR=$(mktemp -d)
echo -e "${GREEN}Created temporary directory at ${TEMP_DIR}${NC}"

# Copy Qdrant data from the volume to the temporary directory
echo -e "${GREEN}Copying Qdrant data...${NC}"
docker run --rm \
    --volumes-from $(docker-compose -f docker-compose.prod.yml ps -q qdrant) \
    -v "${TEMP_DIR}:/backup" \
    alpine sh -c "cd /qdrant/storage && tar cf /backup/qdrant_data.tar ."

# Backup configuration files
echo -e "${GREEN}Backing up configuration files...${NC}"
cp .env.prod "${TEMP_DIR}/env.prod"
cp docker-compose.prod.yml "${TEMP_DIR}/docker-compose.prod.yml"
cp bustling-folio-439811-h8-539f8ab05fa7.json "${TEMP_DIR}/google_credentials.json" 2>/dev/null || echo -e "${RED}Warning: Google credentials file not found.${NC}"

# Create the final backup archive
echo -e "${GREEN}Creating backup archive...${NC}"
tar czf "${BACKUP_FILE}" -C "${TEMP_DIR}" .

# Cleanup
echo -e "${GREEN}Cleaning up temporary files...${NC}"
rm -rf "${TEMP_DIR}"

# Set proper permissions
chmod 600 "${BACKUP_FILE}"

# Verify backup file
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}Backup completed successfully!${NC}"
    echo -e "Backup saved to: ${BACKUP_FILE}"
    echo -e "Backup size: ${BACKUP_SIZE}"
    
    # Keep only the 5 most recent backups
    echo -e "${GREEN}Removing old backups...${NC}"
    ls -t "${BACKUP_DIR}"/qdrant_backup_*.tar.gz | tail -n +6 | xargs rm -f 2>/dev/null || true
    
    # List current backups
    echo -e "${GREEN}Current backups:${NC}"
    ls -lh "${BACKUP_DIR}"/qdrant_backup_*.tar.gz | awk '{print $9, "(" $5 ")"}'
else
    echo -e "${RED}Error: Backup file was not created.${NC}"
    exit 1
fi

# Example usage in crontab:
# 0 2 * * * /path/to/backup.sh /path/to/backup/directory > /var/log/telegram-bot-backup.log 2>&1 