# Deployment Guide

Production-ready deployment strategies for Petty across different environments and platforms.

## 🚀 Deployment Overview

| Deployment Type | Best For | Complexity | Scalability | Cost |
|----------------|----------|------------|-------------|------|
| **AWS Serverless** | Production, Auto-scaling | High | Excellent | Variable |
| **Docker Swarm** | Self-hosted, Medium scale | Medium | Good | Fixed |
| **Kubernetes** | Enterprise, Large scale | Very High | Excellent | High |
| **Single Server** | Small teams, Development | Low | Limited | Low |

## ☁️ AWS Serverless Deployment (Recommended)

### Prerequisites
```bash
# Install required tools
pip install aws-sam-cli awscli
aws configure

# Verify setup
aws sts get-caller-identity
sam --version
```

### Step 1: Configure Deployment Parameters

#### Create S3 Bucket for Deployments
```bash
# Create deployment bucket
aws s3 mb s3://your-petty-deployment-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-petty-deployment-bucket \
  --versioning-configuration Status=Enabled
```

#### Update SAM Configuration
```yaml
# samconfig.toml
version = 0.1

[prod]
[prod.deploy]
[prod.deploy.parameters]
stack_name = "petty-prod"
s3_bucket = "your-petty-deployment-bucket"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
  "Environment=production",
  "LogLevel=warn",
  "EnableXRayTracing=true",
  "AlertsEmail=alerts@yourcompany.com"
]
confirm_changeset = true
fail_on_empty_changeset = false

[staging]
[staging.deploy]
[staging.deploy.parameters]
stack_name = "petty-staging"
s3_bucket = "your-petty-deployment-bucket"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
  "Environment=staging",
  "LogLevel=info",
  "EnableXRayTracing=true"
]
```

### Step 2: Build and Deploy

#### Build Application
```bash
# Build SAM application
sam build --parallel

# Validate template
sam validate --lint
```

#### Deploy to Staging
```bash
# First deployment (guided)
sam deploy --config-env staging --guided

# Subsequent deployments
sam deploy --config-env staging
```

#### Deploy to Production
```bash
# Production deployment with approval
sam deploy --config-env prod

# Monitor deployment
aws cloudformation describe-stacks \
  --stack-name petty-prod \
  --query 'Stacks[0].StackStatus'
```

### Step 3: Post-Deployment Configuration

#### Set Up Custom Domain
```bash
# Create ACM certificate
aws acm request-certificate \
  --domain-name api.yourcompany.com \
  --validation-method DNS \
  --region us-east-1

# Create API Gateway custom domain
aws apigatewayv2 create-domain-name \
  --domain-name api.yourcompany.com \
  --domain-name-configurations CertificateArn=arn:aws:acm:us-east-1:123456789:certificate/abc123
```

#### Configure CloudFront Distribution
```yaml
# Add to template.yaml
PettyCloudFrontDistribution:
  Type: AWS::CloudFront::Distribution
  Properties:
    DistributionConfig:
      Origins:
        - Id: PettyAPIOrigin
          DomainName: !Sub "${PettyApi}.execute-api.${AWS::Region}.amazonaws.com"
          CustomOriginConfig:
            HTTPPort: 443
            OriginProtocolPolicy: https-only
      DefaultCacheBehavior:
        TargetOriginId: PettyAPIOrigin
        ViewerProtocolPolicy: redirect-to-https
        CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # CachingDisabled
      Enabled: true
      Aliases:
        - api.yourcompany.com
      ViewerCertificate:
        AcmCertificateArn: !Ref SSLCertificate
        SslSupportMethod: sni-only
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Single Server)

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  petty-api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "80:8000"
      - "443:8443"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=warn
      - DATABASE_URL=postgresql://petty:${POSTGRES_PASSWORD}@postgres:5432/petty
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./ssl:/app/ssl:ro
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: petty
      POSTGRES_USER: petty
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - petty-api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Production Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY pyproject.toml setup.py README.md ./
RUN pip install --no-cache-dir --user .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd --create-home --shell /bin/bash petty && \
    chown -R petty:petty /app
USER petty

# Make sure scripts are executable
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Start application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "src.api.main:app"]
```

#### Deploy with Docker Compose
```bash
# Set environment variables
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# Create environment file
cat > .env.prod << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
ENVIRONMENT=production
LOG_LEVEL=warn
EOF

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Option 2: Docker Swarm (Multi-Server)

#### Initialize Swarm
```bash
# On manager node
docker swarm init --advertise-addr <MANAGER-IP>

# On worker nodes
docker swarm join --token <TOKEN> <MANAGER-IP>:2377

# Verify cluster
docker node ls
```

#### Deploy Stack
```yaml
# docker-stack.yml
version: '3.8'

services:
  petty-api:
    image: petty:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    networks:
      - petty-network
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: petty
      POSTGRES_USER: petty
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - petty-network
    secrets:
      - postgres_password
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.postgres == true

networks:
  petty-network:
    driver: overlay
    attachable: true

volumes:
  postgres_data:

secrets:
  postgres_password:
    external: true
```

```bash
# Create secrets
echo "your_secure_password" | docker secret create postgres_password -

# Deploy stack
docker stack deploy -c docker-stack.yml petty

# Monitor deployment
docker service ls
docker service logs petty_petty-api
```

## ☸️ Kubernetes Deployment

### Step 1: Prepare Kubernetes Manifests

#### Namespace and ConfigMap
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: petty
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: petty-config
  namespace: petty
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "warn"
  API_PORT: "8000"
```

#### Secrets
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: petty-secrets
  namespace: petty
type: Opaque
data:
  postgres-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-secret>
```

#### PostgreSQL Deployment
```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: petty
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: petty
        - name: POSTGRES_USER
          value: petty
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: petty-secrets
              key: postgres-password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: petty
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### Petty API Deployment
```yaml
# k8s/petty-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: petty-api
  namespace: petty
spec:
  replicas: 3
  selector:
    matchLabels:
      app: petty-api
  template:
    metadata:
      labels:
        app: petty-api
    spec:
      containers:
      - name: petty-api
        image: petty:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://petty:$(POSTGRES_PASSWORD)@postgres-service:5432/petty"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: petty-secrets
              key: postgres-password
        envFrom:
        - configMapRef:
            name: petty-config
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: petty-api-service
  namespace: petty
spec:
  selector:
    app: petty-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: petty-api-hpa
  namespace: petty
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: petty-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Step 2: Deploy to Kubernetes
```bash
# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n petty

# Deploy Petty API
kubectl apply -f k8s/petty-api.yaml

# Set up autoscaling
kubectl apply -f k8s/hpa.yaml

# Check deployment status
kubectl get pods -n petty
kubectl get services -n petty
```

## 🔧 Environment Configuration

### Environment Variables Reference
```bash
# Required Variables
ENVIRONMENT=production|staging|development
LOG_LEVEL=debug|info|warn|error
API_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db

# AWS Configuration (for serverless)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Security Configuration
JWT_SECRET=your_jwt_secret
API_KEY_SECRET=your_api_key_secret

# Feature Flags
ENABLE_REAL_TIME_ALERTS=true
ENABLE_ANALYTICS=true
ENABLE_DEBUG_MODE=false

# External Services
SMTP_HOST=smtp.yourcompany.com
SMTP_PORT=587
SMTP_USER=noreply@yourcompany.com
SMTP_PASSWORD=your_smtp_password
```

### Configuration Files
```yaml
# config/production.yaml
environment: production
log_level: warn

api:
  port: 8000
  host: 0.0.0.0
  cors_enabled: false
  rate_limit:
    enabled: true
    max_requests: 1000
    window_minutes: 60

database:
  pool_size: 20
  max_overflow: 30
  echo: false

cache:
  ttl: 3600
  max_size: 10000

security:
  jwt_expiry_minutes: 60
  password_hash_rounds: 12
  api_key_length: 32

monitoring:
  enable_metrics: true
  enable_tracing: true
  health_check_interval: 30
```

## 📊 Monitoring and Observability

### CloudWatch Setup (AWS)
```yaml
# Add to SAM template
PettyLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${PettyFunction}'
    RetentionInDays: 30

PettyDashboard:
  Type: AWS::CloudWatch::Dashboard
  Properties:
    DashboardName: PettyMonitoring
    DashboardBody: !Sub |
      {
        "widgets": [
          {
            "type": "metric",
            "properties": {
              "metrics": [
                ["AWS/Lambda", "Invocations", "FunctionName", "${PettyFunction}"],
                ["AWS/Lambda", "Errors", "FunctionName", "${PettyFunction}"],
                ["AWS/Lambda", "Duration", "FunctionName", "${PettyFunction}"]
              ],
              "period": 300,
              "stat": "Sum",
              "region": "${AWS::Region}",
              "title": "Lambda Metrics"
            }
          }
        ]
      }
```

### Prometheus/Grafana Setup (Docker/K8s)
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'petty-api'
    static_configs:
      - targets: ['petty-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Application Metrics
```python
# Add to your application
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('petty_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('petty_request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = Gauge('petty_active_connections', 'Active connections')

# Use in endpoints
@REQUEST_LATENCY.time()
def some_endpoint():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/data').inc()
    # ... endpoint logic
```

## 🔐 Security Considerations

### SSL/TLS Configuration
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;

    ssl_certificate /etc/ssl/certs/yourcompany.crt;
    ssl_certificate_key /etc/ssl/private/yourcompany.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    location / {
        proxy_pass http://petty-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Secrets Management
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "petty/prod/database" \
  --description "Production database credentials" \
  --secret-string '{"username":"petty","password":"secure_password"}'

# Kubernetes Secrets
kubectl create secret generic petty-secrets \
  --from-literal=postgres-password=secure_password \
  --from-literal=jwt-secret=jwt_secret_key \
  --namespace=petty
```

## 🔄 CI/CD Pipeline

### GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Setup SAM
        uses: aws-actions/setup-sam@v2

      - name: Build SAM application
        run: sam build

      - name: Deploy to production
        run: sam deploy --config-env prod --no-confirm-changeset
```

## 🚨 Rollback Procedures

### AWS SAM Rollback
```bash
# List stack events to find last good deployment
aws cloudformation describe-stack-events --stack-name petty-prod

# Rollback to previous version
aws cloudformation cancel-update-stack --stack-name petty-prod

# Or deploy previous version
git checkout <previous-commit>
sam deploy --config-env prod
```

### Docker Rollback
```bash
# Tag current version before deploying
docker tag petty:latest petty:backup-$(date +%Y%m%d)

# Rollback to previous image
docker service update --image petty:previous-version petty_petty-api
```

### Kubernetes Rollback
```bash
# Check rollout history
kubectl rollout history deployment/petty-api -n petty

# Rollback to previous version
kubectl rollout undo deployment/petty-api -n petty

# Rollback to specific revision
kubectl rollout undo deployment/petty-api --to-revision=2 -n petty
```

## 📈 Scaling Strategies

### Vertical Scaling
```bash
# AWS Lambda: Increase memory allocation
sam deploy --parameter-overrides MemorySize=1024

# Docker: Update resource limits
docker service update --limit-memory 2G petty_petty-api

# Kubernetes: Update resource requests/limits
kubectl patch deployment petty-api -n petty -p '{"spec":{"template":{"spec":{"containers":[{"name":"petty-api","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

### Horizontal Scaling
```bash
# AWS Lambda: Increase concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name petty-function \
  --provisioned-concurrency-config AllocatedConcurrency=100

# Docker Swarm: Scale services
docker service scale petty_petty-api=5

# Kubernetes: Scale deployment
kubectl scale deployment petty-api --replicas=5 -n petty
```

## 📝 Post-Deployment Checklist

- [ ] **Health Checks**: All services responding to health checks
- [ ] **Database Connectivity**: Application can connect to database
- [ ] **API Endpoints**: All critical endpoints returning expected responses
- [ ] **Authentication**: Login and token validation working
- [ ] **Real-time Features**: WebSocket connections establishing
- [ ] **Monitoring**: Metrics and logs flowing to monitoring systems
- [ ] **Alerts**: Alert notifications configured and tested
- [ ] **Backups**: Automated backup procedures verified
- [ ] **SSL/TLS**: HTTPS working with valid certificates
- [ ] **Performance**: Response times within acceptable limits
- [ ] **Security**: Security scans passed, no vulnerabilities

---

**Deployment Complete!** 🎉

Your Petty installation is now running in production. Monitor the system closely during the first 24 hours and refer to the [Operations Guide](../operations/monitoring.md) for ongoing maintenance.

**Need Help?** Check the [Troubleshooting Guide](../troubleshooting/README.md) or [open an issue](https://github.com/kakashi3lite/Petty/issues).

**Last Updated**: January 20, 2024 | **Version**: 0.1.0