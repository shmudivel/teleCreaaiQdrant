# Deployment Checklist

## Pre-Deployment Steps

1. **Version Control**
   - [x] Create `deployment` branch from current working branch
   - [ ] Commit all changes to the `deployment` branch
   - [ ] Push the `deployment` branch to remote repository

2. **Environment Variables**
   - [ ] Review `.env.prod` file for any missing or incorrect values
   - [ ] Ensure all API keys are valid and not expired
   - [ ] Remove any development-specific variables
   - [ ] Verify Telegram bot token is correct
   - [ ] Check Qdrant connection parameters
   - [ ] Verify LLM provider API keys (Anthropic/OpenAI)

3. **Docker Configuration**
   - [x] Verify `Dockerfile` contains all required dependencies
   - [x] Ensure `docker-compose.prod.yml` is properly configured
   - [ ] Test build locally: `docker-compose -f docker-compose.prod.yml build`
   - [ ] Test run locally: `docker-compose -f docker-compose.prod.yml up`

## Deployment Process

1. **Server Setup**
   - [ ] Provision VM on preferred cloud platform (DigitalOcean, AWS, GCP, etc.)
   - [ ] Install Docker and Docker Compose on the server
   - [ ] Configure firewall to allow necessary connections
   - [ ] Set up SSH keys for secure access

2. **Project Deployment**
   - [ ] Clone the repository on the server: `git clone -b deployment [repository-url]`
   - [ ] Copy necessary credential files to the server (Google service account JSON)
   - [ ] Configure any server-specific environment variables
   - [ ] Run `docker-compose -f docker-compose.prod.yml up -d` to start in detached mode

3. **Post-Deployment Verification**
   - [ ] Check if all containers are running: `docker ps`
   - [ ] Verify logs for any errors: `docker-compose -f docker-compose.prod.yml logs`
   - [ ] Test Telegram bot functionality
   - [ ] Confirm Qdrant database is properly initialized
   - [ ] Verify Google Drive integration is working

## Maintenance and Monitoring

1. **Monitoring**
   - [ ] Set up container monitoring (resources, uptime)
   - [ ] Configure log aggregation
   - [ ] Implement alerting for critical errors

2. **Backup Strategy**
   - [ ] Set up regular backups for Qdrant data volume
   - [ ] Document the process for restoring from backups

3. **Update Process**
   - [ ] Document process for deploying updates
   - [ ] Plan for zero-downtime updates if possible

## Security Considerations

1. **Sensitive Data**
   - [ ] Ensure API keys are not exposed in code or logs
   - [ ] Verify no sensitive data is committed to the repository
   - [ ] Consider using a secure vault service for credentials

2. **Server Security**
   - [ ] Keep server OS and software updated
   - [ ] Restrict SSH access
   - [ ] Configure proper firewall rules 