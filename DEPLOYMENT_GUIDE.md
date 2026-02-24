# Deployment Guide
## GovData Analytics Platform

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB
- OS: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

**Recommended for Production:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB SSD
- OS: Linux (Ubuntu 22.04 LTS)

### Software Dependencies

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Python**: 3.10+ (for manual deployment)
- **Node.js**: 18+ (for manual deployment)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/govdata-analytics.git
cd govdata-analytics
```

### 2. Configure Environment Variables

Create `.env` file in the root directory:

```bash
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# LLM Configuration
DEFAULT_MODEL=mistral-small-latest
FALLBACK_MODEL=gemini-2.0-flash-lite
TERTIARY_MODEL=gpt-3.5-turbo
TEMPERATURE=0.1

# Database
DATABASE_URL=sqlite:///./govdata.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production

# Docker (optional)
DOCKER_USERNAME=your_docker_username
```

### 3. Secrets Management

**For Production:**

```bash
# Use environment-specific .env files
.env.production
.env.staging
.env.development

# Never commit .env files to git
echo ".env*" >> .gitignore
```

**Using Docker Secrets:**

```bash
# Create secrets
echo "your_api_key" | docker secret create gemini_api_key -
echo "your_api_key" | docker secret create mistral_api_key -

# Reference in docker-compose.yml
secrets:
  gemini_api_key:
    external: true
```

**Using Kubernetes Secrets:**

```bash
kubectl create secret generic llm-api-keys \
  --from-literal=gemini-api-key='your_key' \
  --from-literal=mistral-api-key='your_key'
```

---

## Docker Deployment

### Quick Start (Development)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build with production settings
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Update services
docker-compose pull
docker-compose up -d
```

### Docker Commands Reference

```bash
# View running containers
docker-compose ps

# Restart a service
docker-compose restart backend

# View service logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Remove all containers and volumes
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000

# View container health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Manual Deployment

### Backend Deployment

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key
export MISTRAL_API_KEY=your_key
# ... other variables

# Run database migrations (if any)
# alembic upgrade head

# Start server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn for production
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend Deployment

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Start production server
npm start

# Or use PM2 for process management
pm2 start npm --name "govdata-frontend" -- start
```

---

## Production Deployment

### Architecture Overview

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
         ┌────▼────┐              ┌────▼────┐
         │Frontend │              │ Backend │
         │ (Next.js│              │(FastAPI)│
         │  :3000) │              │  :8000) │
         └─────────┘              └────┬────┘
                                       │
                                  ┌────▼────┐
                                  │Database │
                                  │(SQLite) │
                                  └─────────┘
```

### 1. Nginx Configuration

```nginx
# /etc/nginx/sites-available/govdata

upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name govdata.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name govdata.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/govdata.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/govdata.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running queries
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
```

### 2. SSL/TLS Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d govdata.example.com

# Auto-renewal (cron job)
sudo certbot renew --dry-run
```

### 3. Process Management with Systemd

**Backend Service (`/etc/systemd/system/govdata-backend.service`):**

```ini
[Unit]
Description=GovData Analytics Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/govdata/backend
Environment="PATH=/opt/govdata/backend/venv/bin"
EnvironmentFile=/opt/govdata/backend/.env
ExecStart=/opt/govdata/backend/venv/bin/gunicorn api.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    --access-logfile /var/log/govdata/backend-access.log \
    --error-logfile /var/log/govdata/backend-error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/govdata-frontend.service`):**

```ini
[Unit]
Description=GovData Analytics Frontend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/govdata/frontend
Environment="NODE_ENV=production"
Environment="PORT=3000"
EnvironmentFile=/opt/govdata/frontend/.env
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable govdata-backend
sudo systemctl enable govdata-frontend
sudo systemctl start govdata-backend
sudo systemctl start govdata-frontend

# Check status
sudo systemctl status govdata-backend
sudo systemctl status govdata-frontend
```

### 4. Database Setup

```bash
# For production, consider PostgreSQL instead of SQLite
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE govdata;
CREATE USER govdata_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE govdata TO govdata_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://govdata_user:secure_password@localhost/govdata
```

### 5. Monitoring Setup

**Install Prometheus and Grafana:**

```bash
# Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana
docker run -d \
  --name grafana \
  -p 3001:3000 \
  grafana/grafana
```

**Prometheus Configuration (`prometheus.yml`):**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'govdata-backend'
    static_configs:
      - targets: ['localhost:8000']
  
  - job_name: 'govdata-frontend'
    static_configs:
      - targets: ['localhost:3000']
```

---

## Monitoring & Maintenance

### Application Logs

```bash
# Backend logs
tail -f /var/log/govdata/backend-error.log
tail -f /var/log/govdata/backend-access.log

# Frontend logs
journalctl -u govdata-frontend -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f --tail=100
```

### Performance Monitoring

```bash
# CPU and Memory usage
docker stats

# Disk usage
df -h
du -sh /opt/govdata/*

# Network connections
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000
```

### Database Maintenance

```bash
# Backup SQLite database
cp govdata.db govdata.db.backup.$(date +%Y%m%d)

# Backup PostgreSQL database
pg_dump -U govdata_user govdata > backup.sql

# Restore PostgreSQL database
psql -U govdata_user govdata < backup.sql
```

### Updates and Upgrades

```bash
# Pull latest code
git pull origin main

# Backend updates
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart govdata-backend

# Frontend updates
cd frontend
npm ci
npm run build
sudo systemctl restart govdata-frontend

# Docker updates
docker-compose pull
docker-compose up -d
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Not Starting

```bash
# Check logs
journalctl -u govdata-backend -n 50

# Common causes:
# - Missing environment variables
# - Port already in use
# - Database connection issues

# Solutions:
# Check .env file
cat /opt/govdata/backend/.env

# Check port availability
lsof -i :8000

# Test database connection
python -c "from config.settings import settings; print(settings.DATABASE_URL)"
```

#### 2. Frontend Build Errors

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm ci
npm run build

# Check Node.js version
node --version  # Should be 18+

# Check environment variables
cat .env.local
```

#### 3. LLM API Errors

```bash
# Test API keys
curl -H "Authorization: Bearer $MISTRAL_API_KEY" \
  https://api.mistral.ai/v1/models

# Check rate limits
# Review error logs for 429 (rate limit) or 401 (auth) errors

# Switch to fallback model
# Update DEFAULT_MODEL in .env
```

#### 4. High Memory Usage

```bash
# Check memory usage
free -h
docker stats

# Solutions:
# - Reduce worker count
# - Implement caching
# - Upgrade server resources
# - Use connection pooling
```

#### 5. Slow Query Performance

```bash
# Enable query logging
# Add to backend .env:
DEBUG=true
LOG_LEVEL=DEBUG

# Monitor query times
tail -f /var/log/govdata/backend-access.log | grep "query"

# Solutions:
# - Implement caching
# - Optimize data loading
# - Add database indexes
# - Increase timeout limits
```

---

## Security Checklist

- [ ] All API keys stored in environment variables, not code
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] Regular security updates applied
- [ ] Database credentials rotated regularly
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Logging enabled for security events
- [ ] Backup strategy implemented

---

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# /opt/govdata/scripts/backup.sh

BACKUP_DIR="/opt/govdata/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp /opt/govdata/backend/govdata.db "$BACKUP_DIR/db_$DATE.db"

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
  /opt/govdata/backend/.env \
  /opt/govdata/frontend/.env

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Schedule with cron:**

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/govdata/scripts/backup.sh >> /var/log/govdata/backup.log 2>&1
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Load Balancing

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Caching Strategy

```python
# Implement Redis caching
REDIS_URL=redis://localhost:6379/0

# Cache LLM responses
# Cache query results
# Cache static analysis
```

---

## Contact & Support

- **Documentation**: https://docs.govdata.example.com
- **Issues**: https://github.com/your-org/govdata-analytics/issues
- **Email**: support@govdata.example.com

---

## Appendix

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `MISTRAL_API_KEY` | Yes | - | Mistral AI API key |
| `OPENAI_API_KEY` | No | - | OpenAI API key (optional) |
| `DEFAULT_MODEL` | Yes | mistral-small-latest | Primary LLM model |
| `FALLBACK_MODEL` | Yes | gemini-2.0-flash-lite | Fallback LLM model |
| `DATABASE_URL` | Yes | sqlite:///./govdata.db | Database connection string |
| `API_HOST` | Yes | 0.0.0.0 | API host address |
| `API_PORT` | Yes | 8000 | API port |
| `DEBUG` | No | false | Enable debug mode |
| `NEXT_PUBLIC_API_URL` | Yes | http://localhost:8000 | Backend API URL for frontend |

### Port Reference

| Service | Port | Protocol |
|---------|------|----------|
| Backend API | 8000 | HTTP |
| Frontend | 3000 | HTTP |
| Nginx | 80, 443 | HTTP/HTTPS |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| Prometheus | 9090 | HTTP |
| Grafana | 3001 | HTTP |
