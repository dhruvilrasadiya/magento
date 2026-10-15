# TESS (Magento Bot) - Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the TESS (Magento Bot) application to the production server. The deployment process involves pushing code to GitLab and then deploying using Docker Compose on the target server.

## Server Information

### Access Details
- **SSH Access:** `secure.gbi-varpo.nl:222`
- **RDP Access:** `secure.gbi-varpo.nl:4015`
- **Username:** `gbi_varpo` (Administrator rights)
- **Password:** Available via secure link (24-hour validity, single use)

### Server Environment
- **Production URL:** `http://tess.gbi-varpo.nl:5173/`
- **Local Access:** `http://localhost:5173/`
- **Default Login:** Username: `admin`, Password: `admin`

## Application Architecture

### Services Overview
The TESS application consists of the following containerized services:

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| **Frontend** | 5173 | React UI Application | API |
| **API** | 8000 | FastAPI Backend | MongoDB, Qdrant |
| **Airflow** | 8080 | Data Pipeline Orchestration | PostgreSQL, Qdrant |
| **MongoDB** | 27017 | Primary Database | None |
| **Qdrant** | 6333 | Vector Database | None |
| **PostgreSQL** | 5432 | Airflow Metadata DB | None |

### Network Architecture
```
Internet → Server (secure.gbi-varpo.nl)
    ├── Frontend (Port 5173) → API (Port 8000)
    ├── Airflow (Port 8080) → PostgreSQL (Port 5432)
    ├── API → MongoDB (Port 27017)
    ├── API → Qdrant (Port 6333)
    └── Airflow → Qdrant (Port 6333)
```

## Pre-Deployment Requirements

### 1. Environment Configuration
Ensure the following environment variables are properly configured in `.env` file:

#### API Configuration
```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False  # Set to False for production
```

#### OpenAI Configuration
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

#### Database Configuration
```env
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DATABASE=chatdb
MONGODB_USERNAME=adminuser
MONGODB_PASSWORD=adminuser
```

#### External API Configuration
```env
MAGENTO_API_URL=https://www.terrasheater.nl/
MAGENTO_API_TOKEN=your_magento_token
DGE_API_URL=https://c1.dgebv.nl
DGE_USERNAME=your_dge_username
DGE_PASSWORD=your_dge_password
```

### 2. Security Configuration
```env
SECRET_KEY=your_jwt_secret_key
REFRESH_SECRET_KEY=your_refresh_secret_key
ALGORITHM=HS256
```

### 3. Email Configuration
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SENDER_EMAIL=your_sender_email@gmail.com
SENDER_PASSWORD=your_sender_password
```

## Deployment Process

### Step 1: Code Preparation and Push

#### 1.1 Prepare Local Environment
```bash
# Ensure all changes are committed
git status
git add .
git commit -m "Production deployment - [describe changes]"
```

#### 1.2 Push to GitLab Repository
```bash
# Push to origin-gitlab remote
git push origin-gitlab main
```

**Note:** The `origin-gitlab` remote should be configured to point to the GitLab repository that is linked with the production server.

### Step 2: Server Access and Deployment

#### 2.1 Connect to Server
```bash
# SSH Connection
ssh gbi_varpo@secure.gbi-varpo.nl -p 222

# Or use RDP for GUI access
# RDP: secure.gbi-varpo.nl:4015
```

#### 2.2 Navigate to Application Directory
```bash
# Navigate to the application directory
cd /path/to/tess-application  # Replace with actual path
```

#### 2.3 Pull Latest Code
```bash
# Pull the latest code from GitLab
git pull origin main
```

#### 2.4 Deploy with Docker Compose
```bash
# Stop existing containers (if running)
docker-compose down

# Pull latest images and start services
docker-compose up -d

# Verify all services are running
docker-compose ps
```

#### 2.5 Verify Deployment
```bash
# Check service logs
docker-compose logs -f

# Check individual service logs
docker-compose logs frontend
docker-compose logs api
docker-compose logs airflow
```

### Step 3: Post-Deployment Verification

#### 3.1 Service Health Checks
```bash
# Check if all containers are running
docker-compose ps

# Expected output should show all services as "Up"
```

#### 3.2 Application Access Verification
1. **Frontend Access:**
   - External: `http://tess.gbi-varpo.nl:5173/`
   - Local: `http://localhost:5173/`

2. **API Documentation:**
   - `http://localhost:8000/docs`

3. **Airflow Dashboard:**
   - `http://localhost:8080`

#### 3.3 Login Verification
- **Username:** `admin`
- **Password:** `admin`
- Verify successful login and basic functionality

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Conflicts
```bash
# Check if ports are already in use
netstat -tulpn | grep :5173
netstat -tulpn | grep :8000

# Kill processes using required ports if necessary
sudo kill -9 $(lsof -t -i:5173)
```

#### 2. Docker Issues
```bash
# Restart Docker service
sudo systemctl restart docker

# Clean up Docker resources
docker system prune -f
docker volume prune -f
```

#### 3. Database Connection Issues
```bash
# Check MongoDB container
docker-compose logs mongodb

# Check Qdrant container
docker-compose logs data_qdrant

# Restart database services
docker-compose restart mongodb data_qdrant
```

#### 4. Environment Variable Issues
```bash
# Verify .env file exists and has correct permissions
ls -la .env
cat .env | grep -E "(API_KEY|SECRET_KEY|PASSWORD)" | wc -l

# Restart services after .env changes
docker-compose down
docker-compose up -d
```

### Log Monitoring
```bash
# Monitor all services
docker-compose logs -f

# Monitor specific service
docker-compose logs -f frontend
docker-compose logs -f api

# Check last 100 lines
docker-compose logs --tail=100 api
```

## Maintenance Commands

### Regular Maintenance
```bash
# Update application
git pull origin main
docker-compose down
docker-compose up -d

# Clean up unused Docker resources
docker system prune -f

# Backup databases
docker exec mongodb_container mongodump --out /backup/$(date +%Y%m%d)
```

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
df -h
docker system df
```

## Security Considerations

### 1. Firewall Configuration
- Ensure only necessary ports are exposed
- Configure firewall rules for ports 5173, 8000, 8080

### 2. SSL/TLS (Recommended for Production)
- Consider implementing SSL certificates
- Use reverse proxy (Nginx) for HTTPS termination

### 3. Environment Security
- Regularly rotate API keys and passwords
- Use strong passwords for database access
- Implement proper backup strategies

## Rollback Procedure

In case of deployment issues:

```bash
# 1. Stop current deployment
docker-compose down

# 2. Revert to previous commit
git log --oneline -10  # Find previous stable commit
git checkout <previous-commit-hash>

# 3. Redeploy
docker-compose up -d

# 4. Verify rollback
curl http://localhost:5173/
```

## Support and Contacts

### Technical Support
- **Repository:** GitLab repository linked to server
- **Documentation:** This deployment guide and technical documentation
- **Logs Location:** Docker container logs via `docker-compose logs`

### Emergency Procedures
1. **Service Down:** Restart with `docker-compose restart`
2. **Complete Failure:** Full redeployment with `docker-compose down && docker-compose up -d`
3. **Data Issues:** Restore from database backups

---

## Quick Reference Commands

```bash
# Deployment sequence
git push origin-gitlab main
ssh gbi_varpo@secure.gbi-varpo.nl -p 222
cd /path/to/application
git pull origin main
docker-compose up -d

# Health check
docker-compose ps
curl http://localhost:5173/

# Monitoring
docker-compose logs -f
docker stats
```

This deployment guide ensures reliable and consistent deployment of the TESS application to the production environment.

---

## Advanced Configuration

### Docker Compose Service Details

#### Frontend Service Configuration
```yaml
frontend:
  build:
    context: .
    dockerfile: frontend/Dockerfile
  ports:
    - "5173:5173"  # React development server
  environment:
    - CHOKIDAR_USEPOLLING=true  # File watching for hot reload
    - WATCHPACK_POLLING=true
  volumes:
    - ./frontend:/app
    - /app/node_modules  # Anonymous volume for node_modules
```

#### API Service Configuration
```yaml
api:
  build:
    context: .
    dockerfile: docker/Dockerfile.api
  ports:
    - "8000:8000"  # FastAPI server
  environment:
    - MONGODB_URI=mongodb://mongodb:27017
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - PYTHONPATH=/app
  volumes:
    - ./api:/app/api
    - ./agentic_ai:/app/agentic_ai
    - .env:/app/.env
```

### Environment-Specific Configurations

#### Production Environment Variables
```env
# Production-specific settings
DEBUG=False
LOG_LEVEL=WARNING
API_HOST=0.0.0.0

# Frontend URL for production
FRONTEND_URL=http://tess.gbi-varpo.nl:5173

# Database optimization for production
MONGODB_URI=mongodb://mongodb:27017/chatdb?retryWrites=true&w=majority
```

#### Development vs Production Differences
| Setting | Development | Production |
|---------|-------------|------------|
| DEBUG | True | False |
| LOG_LEVEL | DEBUG | WARNING |
| FRONTEND_URL | localhost:5173 | tess.gbi-varpo.nl:5173 |
| SSL | Disabled | Recommended |
| Volume Mounts | Source code | Minimal |

## Monitoring and Alerting

### Health Check Endpoints
```bash
# API Health Check
curl http://localhost:8000/health

# Frontend Health Check
curl http://localhost:5173/

# Database Health Check
docker exec mongodb_container mongo --eval "db.adminCommand('ping')"

# Qdrant Health Check
curl http://localhost:6333/health
```

### Performance Metrics
```bash
# Container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Disk usage monitoring
du -sh /var/lib/docker/volumes/

# Network connectivity
docker network ls
docker network inspect magento-bot_app_network
```

### Log Aggregation
```bash
# Centralized logging setup
docker-compose logs --timestamps --follow > /var/log/tess/application.log

# Log rotation configuration
logrotate /etc/logrotate.d/tess-logs
```

## Backup and Recovery

### Database Backup Strategy
```bash
# MongoDB backup
docker exec mongodb_container mongodump --out /backup/mongodb/$(date +%Y%m%d_%H%M%S)

# Qdrant backup
docker exec data_qdrant_container tar -czf /backup/qdrant/$(date +%Y%m%d_%H%M%S).tar.gz /qdrant/storage

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/tess/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
docker-compose exec mongodb mongodump --out $BACKUP_DIR/mongodb
docker-compose exec data_qdrant tar -czf $BACKUP_DIR/qdrant.tar.gz /qdrant/storage
```

### Recovery Procedures
```bash
# MongoDB restore
docker exec mongodb_container mongorestore /backup/mongodb/YYYYMMDD_HHMMSS/

# Qdrant restore
docker exec data_qdrant_container tar -xzf /backup/qdrant/YYYYMMDD_HHMMSS.tar.gz -C /
docker-compose restart data_qdrant
```

## SSL/HTTPS Configuration (Recommended)

### Nginx Reverse Proxy Setup
```nginx
# /etc/nginx/sites-available/tess
server {
    listen 80;
    server_name tess.gbi-varpo.nl;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Certificate Installation
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d tess.gbi-varpo.nl

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Scaling and Performance Optimization

### Horizontal Scaling Options
```yaml
# docker-compose.override.yml for scaling
version: '3.8'
services:
  api:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"

  frontend:
    deploy:
      replicas: 2
    ports:
      - "5173-5174:5173"
```

### Performance Tuning
```bash
# Increase Docker resources
# Edit /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {"hard": -1, "soft": -1},
    "nofile": {"hard": 65536, "soft": 65536}
  }
}

# Restart Docker
sudo systemctl restart docker
```

This comprehensive deployment guide covers all aspects of deploying, monitoring, and maintaining the TESS application in a production environment.
