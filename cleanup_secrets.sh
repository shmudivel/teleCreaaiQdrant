#!/bin/bash

# Security Cleanup Script - Remove sensitive data before deployment
# This script should be run before any git commit or push operations

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Security Cleanup Script ===${NC}"
echo -e "${YELLOW}Removing sensitive data before deployment...${NC}"

# Function to log actions
log_action() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to replace hardcoded API keys in files
replace_hardcoded_keys() {
    local file="$1"
    local backup_file="${file}.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Create backup
    cp "$file" "$backup_file"
    
    # Replace common API key patterns
    sed -i.tmp \
        -e 's/sk-ant-api03-[A-Za-z0-9_-]\{95\}/os.environ.get("ANTHROPIC_API_KEY")/g' \
        -e 's/sk-proj-[A-Za-z0-9_-]\{95\}/os.environ.get("OPENAI_API_KEY")/g' \
        -e 's/GOCSPX-[A-Za-z0-9_-]\{28\}/os.environ.get("GOOGLE_CLIENT_SECRET")/g' \
        -e 's/[0-9]\{12\}-[A-Za-z0-9]\{32\}\.apps\.googleusercontent\.com/os.environ.get("GOOGLE_CLIENT_ID")/g' \
        -e 's/"sk-ant-[^"]*"/"REMOVED_API_KEY"/g' \
        -e 's/"sk-proj-[^"]*"/"REMOVED_API_KEY"/g' \
        -e 's/"GOCSPX-[^"]*"/"REMOVED_SECRET"/g' \
        "$file"
    
    # Remove temporary file
    rm -f "${file}.tmp"
    
    # Check if file was changed
    if ! cmp -s "$file" "$backup_file"; then
        log_action "Cleaned API keys from: $file"
        rm "$backup_file"
        return 0
    else
        rm "$backup_file"
        return 1
    fi
}

# 1. Remove sensitive files
echo -e "\n${BLUE}1. Removing sensitive files...${NC}"

# List of sensitive files to remove
SENSITIVE_FILES=(
    "youtube_token.json"
    "tests/big_text_to_reels/youtube_token.json"
    "tests/big_text_to_edited_text/env."
    "*.token"
    ".env.local"
    ".env.dev"
    "**/credentials.json"
    "**/service-account-*.json"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if find . -name "$pattern" -type f | grep -q .; then
        find . -name "$pattern" -type f -delete
        log_action "Removed files matching: $pattern"
    fi
done

# 2. Clean API keys from Python files
echo -e "\n${BLUE}2. Cleaning hardcoded API keys from Python files...${NC}"

# Find and clean Python files
find . -name "*.py" -type f | while read -r file; do
    # Skip virtual environment and backup files
    if [[ "$file" == *"/venv/"* ]] || [[ "$file" == *".backup_"* ]]; then
        continue
    fi
    
    # Check if file contains potential API keys
    if grep -q -E "(sk-ant-|sk-proj-|GOCSPX-|\.apps\.googleusercontent\.com)" "$file"; then
        replace_hardcoded_keys "$file"
    fi
done

# 3. Update .gitignore to prevent future commits of sensitive data
echo -e "\n${BLUE}3. Updating .gitignore...${NC}"

GITIGNORE_ENTRIES=(
    ""
    "# Sensitive files and API keys"
    "youtube_token.json"
    "**/youtube_token.json"
    "*.token"
    ".env"
    ".env.*"
    "env.*"
    "**/env.*"
    "credentials.json"
    "**/credentials.json"
    "service-account-*.json"
    "**/service-account-*.json"
    ""
    "# API keys and secrets"
    "**/sk-*"
    "**/ANTHROPIC_API_KEY"
    "**/OPENAI_API_KEY"
    "**/GOOGLE_CLIENT_*"
    "**/GOCSPX-*"
    ""
    "# Backup files"
    "*.backup_*"
    "**/*.backup_*"
)

# Check if .gitignore needs updating
NEEDS_UPDATE=false
for entry in "${GITIGNORE_ENTRIES[@]}"; do
    if [[ -n "$entry" ]] && ! grep -Fxq "$entry" .gitignore 2>/dev/null; then
        NEEDS_UPDATE=true
        break
    fi
done

if [[ "$NEEDS_UPDATE" == true ]]; then
    for entry in "${GITIGNORE_ENTRIES[@]}"; do
        if [[ -n "$entry" ]] && ! grep -Fxq "$entry" .gitignore 2>/dev/null; then
            echo "$entry" >> .gitignore
        fi
    done
    log_action "Updated .gitignore with security patterns"
else
    log_action ".gitignore already contains security patterns"
fi

# 4. Check for remaining sensitive data
echo -e "\n${BLUE}4. Scanning for remaining sensitive data...${NC}"

# Patterns to check for
SENSITIVE_PATTERNS=(
    "sk-ant-api03-"
    "sk-proj-"
    "GOCSPX-"
    "AIzaSy"
    "ya29\."
    "1//0"
)

FOUND_ISSUES=false
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if find . -name "*.py" -o -name "*.js" -o -name "*.json" | \
       xargs grep -l "$pattern" 2>/dev/null | \
       grep -v "/venv/" | \
       grep -v ".backup_"; then
        log_error "Found potential API key pattern '$pattern' in files above"
        FOUND_ISSUES=true
    fi
done

# Check for actual API keys in documentation files (not examples)
DOC_ISSUES=false
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if find . -name "*.md" -o -name "*.txt" | \
       xargs grep -l "$pattern" 2>/dev/null | \
       grep -v "/venv/" | \
       grep -v ".backup_" | \
       xargs grep -l "sk-.*-[A-Za-z0-9]\{50,\}" 2>/dev/null; then
        log_warning "Found potential REAL API keys in documentation files above - please verify these are examples"
        DOC_ISSUES=true
    fi
done

# 5. Verify environment variable usage
echo -e "\n${BLUE}5. Verifying environment variable usage...${NC}"

# Check if files properly use environment variables
PYTHON_FILES=$(find . -name "*.py" -type f | grep -v "/venv/" | grep -v ".backup_")
ISSUES_FOUND=false

for file in $PYTHON_FILES; do
    # Check for proper environment variable usage
    if grep -q "os.environ.get.*API" "$file" || grep -q "os.getenv.*API" "$file"; then
        continue
    fi
    
    # Check if file deals with APIs but doesn't use env vars
    if grep -q -E "(anthropic|openai|google.*api)" "$file" 2>/dev/null; then
        if ! grep -q -E "(os\.environ|os\.getenv)" "$file" 2>/dev/null; then
            log_warning "File $file may need environment variable usage: check manually"
        fi
    fi
done

# 6. Create example environment file
echo -e "\n${BLUE}6. Creating example environment file...${NC}"

cat > .env.example << 'EOF'
# Example environment variables for the application
# Copy this file to .env and fill in your actual values

# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Google APIs
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_SERVICE_ACCOUNT_PATH=path_to_service_account_json

# YouTube API
YOUTUBE_CLIENT_ID=your_youtube_client_id_here
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret_here

# ElevenLabs API
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# HeyGen API
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_AVATAR_ID_1=your_avatar_id_1_here
HEYGEN_AVATAR_ID_2=your_avatar_id_2_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Qdrant Vector Database
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key_here
EOF

log_action "Created .env.example file"

# 7. Summary and recommendations
echo -e "\n${BLUE}=== Cleanup Summary ===${NC}"

if [[ "$FOUND_ISSUES" == true ]]; then
    log_error "Some sensitive data patterns were found - please review manually"
    echo -e "${YELLOW}Please review the files listed above and ensure all API keys use environment variables${NC}"
    exit 1
else
    log_action "No obvious sensitive data patterns found"
fi

echo -e "\n${GREEN}Security cleanup completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Review any changes made to your files"
echo -e "2. Test your application to ensure environment variables work correctly"
echo -e "3. Commit your changes: ${BLUE}git add . && git commit -m 'Security: Remove hardcoded credentials'${NC}"
echo -e "4. Push to repository: ${BLUE}git push origin deployment${NC}"

echo -e "\n${YELLOW}Remember:${NC}"
echo -e "- Set all required environment variables on your deployment server"
echo -e "- Never commit actual API keys or credentials"
echo -e "- Use .env.example as a template for required environment variables" 