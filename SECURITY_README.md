# 🔐 Security & Safe Development Guide

This project includes comprehensive security measures to prevent accidentally committing API keys, tokens, and other sensitive data.

## 🚀 Quick Start

**For most users, this is all you need:**

```bash
# Make scripts executable (first time only)
chmod +x cleanup_secrets.sh secure_commit.sh deploy.sh

# Secure commit and deploy
./secure_commit.sh "Your commit message"
./deploy.sh
```

## 📋 Available Scripts

### `cleanup_secrets.sh` 
**Purpose**: Remove all sensitive data before any git operations

**What it does**:
- ❌ Removes hardcoded API keys (Anthropic, OpenAI, Google)
- ❌ Deletes token files (youtube_token.json, etc.)
- ❌ Removes environment files with credentials
- ✅ Replaces hardcoded keys with `os.environ.get()` calls
- ✅ Updates .gitignore with security patterns
- ✅ Creates .env.example template

**Usage**:
```bash
./cleanup_secrets.sh
```

### `secure_commit.sh`
**Purpose**: Safely commit changes with automatic security cleanup

**What it does**:
- 🔒 Runs `cleanup_secrets.sh` automatically
- 📝 Commits your changes
- ⬆️ Optionally pushes to GitHub
- ✅ Prevents sensitive data from being committed

**Usage**:
```bash
./secure_commit.sh "Your commit message"
```

### `deploy.sh` (Updated)
**Purpose**: Secure deployment with built-in security checks

**What it does**:
- 🔒 Runs security cleanup before deployment
- 📝 Commits any security-related changes
- ⬆️ Pushes to GitHub safely
- 🖥️ Deploys to DigitalOcean server
- ✅ Verifies deployment

**Usage**:
```bash
./deploy.sh
```

## 🔍 Security Patterns Detected

The cleanup script automatically detects and removes:

| Pattern | Description | Example |
|---------|-------------|---------|
| `sk-ant-api03-*` | Anthropic API keys | `sk-ant-api03-abc123...` |
| `sk-proj-*` | OpenAI project API keys | `sk-proj-abc123...` |
| `GOCSPX-*` | Google OAuth client secrets | `GOCSPX-abc123...` |
| `*.apps.googleusercontent.com` | Google OAuth client IDs | `123456789.apps.googleusercontent.com` |
| `youtube_token.json` | YouTube API tokens | Any file with this name |
| `env.*` files | Environment files | `env.`, `.env.local`, etc. |

## 🔧 Environment Variables Setup

### 1. Copy the template:
```bash
cp .env.example .env
```

### 2. Fill in your actual values:
```bash
# Core API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here
OPENAI_API_KEY=sk-proj-your_actual_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Google Services  
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret
GOOGLE_SERVICE_ACCOUNT_PATH=path/to/service_account.json

# Additional Services
ELEVENLABS_API_KEY=your_elevenlabs_key
HEYGEN_API_KEY=your_heygen_key
QDRANT_API_KEY=your_qdrant_key
```

### 3. On deployment server:
Set these same environment variables in your production environment.

## 🛠 Development Workflows

### Option 1: Automated (Recommended)
```bash
# Make changes to your code
# ...

# Secure commit (includes cleanup)
./secure_commit.sh "Add new feature"

# Deploy (includes security checks)
./deploy.sh
```

### Option 2: Manual Control
```bash
# Make changes to your code
# ...

# Manual security cleanup
./cleanup_secrets.sh

# Review changes
git status
git diff

# Commit manually
git add .
git commit -m "Add new feature"
git push origin deployment

# Deploy
./deploy.sh
```

### Option 3: Quick Security Check
```bash
# Before any commit, scan for secrets
grep -r "sk-ant-\|sk-proj-\|GOCSPX-" . --exclude-dir=venv || echo "✅ No API keys found"
```

## ⚠️ What NOT to Do

❌ **Don't commit these**:
```python
# BAD
ANTHROPIC_API_KEY = "sk-ant-api03-actual-key-here"
client = OpenAI(api_key="sk-proj-actual-key-here")
```

✅ **Do this instead**:
```python
# GOOD
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

❌ **Don't commit these files**:
- `youtube_token.json`
- `.env` (with actual values)
- `credentials.json`
- `service-account-*.json`

✅ **Do commit these**:
- `.env.example` (with placeholder values)
- Code that uses environment variables
- Updated .gitignore

## 🚨 Emergency: If You Accidentally Committed Secrets

### 1. Stop and clean immediately:
```bash
./cleanup_secrets.sh
git add .
git commit -m "Security: Remove accidentally committed secrets"
```

### 2. Clean git history:
```bash
# Remove secrets from entire git history
git filter-branch --force --tree-filter 'find . -name "*.py" -exec sed -i "s/sk-ant-[^\"]*/__REMOVED_API_KEY__/g" {} \;' HEAD
git gc --prune=now --aggressive
```

### 3. Force push (CAUTION):
```bash
git push --force-with-lease origin deployment
```

### 4. Rotate compromised credentials:
- Generate new API keys
- Update environment variables
- Revoke old keys

## 🔍 Troubleshooting

### Script permission denied:
```bash
chmod +x cleanup_secrets.sh secure_commit.sh deploy.sh
```

### Environment variables not working:
```bash
# Check if they're set
echo $ANTHROPIC_API_KEY

# Test in Python
python -c "import os; print('✓' if os.getenv('ANTHROPIC_API_KEY') else '✗')"
```

### Security cleanup found issues:
Read the output carefully and manually review any files mentioned.

### GitHub still rejecting push:
The git history might contain secrets. Use the emergency procedure above.

## 📞 Support

If you encounter security-related issues:

1. **Don't panic** - Secrets can usually be cleaned from git history
2. **Run cleanup script** - `./cleanup_secrets.sh` fixes most issues
3. **Check the logs** - The scripts provide detailed output
4. **Review manually** - Sometimes manual review is needed
5. **Rotate credentials** - When in doubt, generate new API keys

Remember: **Prevention is better than cleanup!** Always use the secure scripts for commits and deployments. 