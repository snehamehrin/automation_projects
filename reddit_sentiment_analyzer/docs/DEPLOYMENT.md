# Deployment Guide

This guide covers deploying the Reddit Sentiment Analyzer in various environments, from local development to production Kubernetes clusters.

## Prerequisites

### Required Tools
- Docker and Docker Compose
- Kubernetes cluster (for production)
- kubectl configured for your cluster
- Helm (optional, for advanced deployments)

### Required Accounts & API Keys
- OpenAI API key
- Apify API key
- Google Cloud Platform account (for Google Sheets)
- Domain name and SSL certificates (for production)

## Local Development

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd reddit_sentiment_analyzer
   python scripts/setup.py
   ```

2. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start Services**
   ```bash
   make dev
   ```

4. **Access Application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Development with Docker

1. **Build and Run**
   ```bash
   docker-compose -f deployment/docker/docker-compose.yml up --build
   ```

2. **View Logs**
   ```bash
   docker-compose -f deployment/docker/docker-compose.yml logs -f
   ```

## Production Deployment

### Docker Deployment

1. **Build Production Image**
   ```bash
   docker build -f deployment/docker/Dockerfile -t reddit-sentiment-analyzer:latest .
   ```

2. **Run with Docker Compose**
   ```bash
   # Set production environment variables
   export ENVIRONMENT=production
   export DEBUG=false
   
   docker-compose -f deployment/docker/docker-compose.yml up -d
   ```

3. **Verify Deployment**
   ```bash
   curl http://localhost:8000/health
   ```

### Kubernetes Deployment

#### 1. Prepare Kubernetes Cluster

```bash
# Create namespace
kubectl apply -f deployment/k8s/namespace.yaml

# Create secrets
kubectl create secret generic reddit-analyzer-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/reddit_analyzer" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=apify-api-key="your-apify-key" \
  --namespace=reddit-analyzer
```

#### 2. Deploy Application

```bash
# Deploy application
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml
kubectl apply -f deployment/k8s/ingress.yaml

# Verify deployment
kubectl get pods -n reddit-analyzer
kubectl get services -n reddit-analyzer
```

#### 3. Configure Ingress

Update the ingress configuration with your domain:

```yaml
# deployment/k8s/ingress.yaml
spec:
  rules:
  - host: your-domain.com  # Update this
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: reddit-analyzer-service
            port:
              number: 80
```

#### 4. SSL Certificate (Let's Encrypt)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Environment Configuration

### Development Environment

```bash
# .env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///dev.db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-dev-key
APIFY_API_KEY=your-dev-key
```

### Production Environment

```bash
# .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@postgres:5432/reddit_analyzer
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your-prod-key
APIFY_API_KEY=your-prod-key
SECRET_KEY=your-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## Database Setup

### PostgreSQL (Production)

1. **Create Database**
   ```sql
   CREATE DATABASE reddit_analyzer;
   CREATE USER reddit_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer TO reddit_user;
   ```

2. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

### SQLite (Development)

```bash
# Database will be created automatically
# No additional setup required
```

## Monitoring Setup

### Prometheus & Grafana

1. **Deploy Monitoring Stack**
   ```bash
   # Using Docker Compose
   docker-compose -f deployment/docker/docker-compose.yml up -d prometheus grafana
   
   # Access Grafana
   # URL: http://localhost:3000
   # Username: admin
   # Password: admin
   ```

2. **Configure Dashboards**
   - Import dashboard from `deployment/grafana/dashboards/`
   - Configure data sources to point to Prometheus

### Log Aggregation

1. **ELK Stack (Optional)**
   ```bash
   # Add to docker-compose.yml
   elasticsearch:
     image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
     environment:
       - discovery.type=single-node
       - xpack.security.enabled=false
     ports:
       - "9200:9200"
   
   kibana:
     image: docker.elastic.co/kibana/kibana:8.8.0
     ports:
       - "5601:5601"
     depends_on:
       - elasticsearch
   ```

## Security Configuration

### Network Security

1. **Firewall Rules**
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 22/tcp  # SSH
   ufw enable
   ```

2. **Kubernetes Network Policies**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: reddit-analyzer-netpol
     namespace: reddit-analyzer
   spec:
     podSelector:
       matchLabels:
         app: reddit-analyzer
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: ingress-nginx
       ports:
       - protocol: TCP
         port: 8000
   ```

### SSL/TLS Configuration

1. **Nginx SSL Configuration**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
       ssl_prefer_server_ciphers off;
       
       location / {
           proxy_pass http://reddit-analyzer:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Backup & Recovery

### Database Backup

1. **Automated Backup Script**
   ```bash
   #!/bin/bash
   # backup.sh
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump $DATABASE_URL > backup_$DATE.sql
   gzip backup_$DATE.sql
   aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
   ```

2. **Kubernetes CronJob**
   ```yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: database-backup
     namespace: reddit-analyzer
   spec:
     schedule: "0 2 * * *"  # Daily at 2 AM
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: backup
               image: postgres:15
               command:
               - /bin/bash
               - -c
               - pg_dump $DATABASE_URL | gzip > /backup/backup_$(date +%Y%m%d_%H%M%S).sql.gz
               env:
               - name: DATABASE_URL
                 valueFrom:
                   secretKeyRef:
                     name: reddit-analyzer-secrets
                     key: database-url
               volumeMounts:
               - name: backup-storage
                 mountPath: /backup
             volumes:
             - name: backup-storage
               persistentVolumeClaim:
                 claimName: backup-pvc
             restartPolicy: OnFailure
   ```

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check logs
   kubectl logs -f deployment/reddit-analyzer -n reddit-analyzer
   
   # Check service status
   kubectl get pods -n reddit-analyzer
   kubectl describe pod <pod-name> -n reddit-analyzer
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   kubectl exec -it <pod-name> -n reddit-analyzer -- python -c "
   from src.config.settings import get_database_settings
   print(get_database_settings().url)
   "
   ```

3. **API Key Issues**
   ```bash
   # Verify secrets
   kubectl get secrets -n reddit-analyzer
   kubectl describe secret reddit-analyzer-secrets -n reddit-analyzer
   ```

### Performance Tuning

1. **Resource Limits**
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "1Gi"
       cpu: "500m"
   ```

2. **Horizontal Pod Autoscaler**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: reddit-analyzer-hpa
     namespace: reddit-analyzer
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: reddit-analyzer
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

## Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   pip-compile --upgrade pyproject.toml
   docker build --no-cache -t reddit-sentiment-analyzer:latest .
   ```

2. **Database Maintenance**
   ```bash
   # Vacuum database
   kubectl exec -it <postgres-pod> -- psql -d reddit_analyzer -c "VACUUM ANALYZE;"
   ```

3. **Log Rotation**
   ```bash
   # Configure logrotate
   echo "/var/log/reddit-analyzer/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
   }" > /etc/logrotate.d/reddit-analyzer
   ```

This deployment guide provides comprehensive instructions for deploying the Reddit Sentiment Analyzer in various environments. Follow the sections relevant to your deployment needs and adjust configurations as necessary for your specific infrastructure.
