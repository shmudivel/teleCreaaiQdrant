# Deployment Guide for Telegram Bot Project

This guide provides detailed instructions for deploying the Telegram Bot project in a production environment.

## Overview

This project consists of a Telegram bot that generates optimized content for different social media platforms. It uses Docker for containerization and includes two main services:

1. **Bot service**: The main application that runs the Telegram bot
2. **Qdrant service**: Vector database for storing and retrieving data

## Getting Started

To deploy this application, follow these steps:

### Prerequisites

- A server with Docker and Docker Compose installed
- Access to the Git repository
- Required API keys and credentials

### Quick Deployment

1. Clone the repository:
   ```bash
   git clone -b deployment https://github.com/yourusername/teleCreaaiQdrant.git
   cd teleCreaaiQdrant
   ```

2. Configure your environment:
   - Make sure your `.env.prod` file contains valid API keys and credentials
   - Ensure the Google service account JSON file is present

3. Deploy with Docker Compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. Verify the deployment:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs
   ```

### Automated Deployment

For automated deployment to DigitalOcean:

1. Update the `deploy_to_digitalocean.sh` script with your server details
2. Make the script executable: `chmod +x deploy_to_digitalocean.sh`
3. Run the script: `./deploy_to_digitalocean.sh`

## Monitoring and Maintenance

- Use the `monitor.sh` script to check the health of your application
- Set up a cron job to run the monitoring script regularly:
  ```
  */10 * * * * /path/to/monitor.sh youremail@example.com > /dev/null 2>&1
  ```

- Use the `startup.sh` script to start or restart the application

## Security Considerations

- Always use HTTPS for external communications
- Keep your API keys and credentials secure
- Restrict SSH access to your server
- Keep your Docker images updated

## Troubleshooting

If you encounter issues:

1. Check the application logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify the containers are running: `docker ps`
3. Check the server's resource usage: `htop` or `top`
4. Ensure all required environment variables are set correctly

## Additional Resources

- Refer to `DEPLOYMENT.md` for a complete deployment checklist
- See the main `README.md` for general project information

## Contact

For deployment-related issues, please contact the DevOps team. 