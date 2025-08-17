# Production Deployment Guide

This guide covers deploying the Petty AI Pet Monitoring System to production environments with enterprise-grade security and reliability.

## Prerequisites

### System Requirements
- **Docker Engine**: 20.10+ with BuildKit support
- **Docker Compose**: v2.0+
- **Kubernetes**: 1.24+ (for K8s deployment)
- **Memory**: 4GB+ available RAM
- **Storage**: 20GB+ available disk space
- **Network**: HTTPS/TLS certificates for production

### Required Secrets
Before deployment, configure the following secrets:

```bash
# JWT Configuration
JWT_ALGORITHM=RS256
JWT_ISSUER=petty-api
JWT_AUDIENCE=petty-users

# Database
POSTGRES_PASSWORD=<secure-password>
REDIS_PASSWORD=<secure-password>

# Monitoring
GRAFANA_PASSWORD=<secure-password>

# External Services
CODACY_PROJECT_TOKEN=<your-token>
CODECOV_TOKEN=<your-token>
```

## Docker Deployment

### Quick Start
```bash
# Clone repository
git clone https://github.com/kakashi3lite/Petty.git
cd Petty

# Configure environment
cp .env.example .env
# Edit .env with your values

# Start production stack
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs petty-api
```

### Production Configuration
```bash
# Build production image
make docker-build

# Run security scan
make scan-vulnerabilities

# Generate SBOM
make generate-sbom

# Start production stack
docker-compose --profile production up -d
```

### Health Checks
```bash
# Check application health
curl http://localhost:8080/health

# Check monitoring stack
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
curl http://localhost:16686  # Jaeger
```

## Kubernetes Deployment

### Namespace Setup
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: petty-production
  labels:
    security.policy: strict
---
apiVersion: v1
kind: Secret
metadata:
  name: petty-secrets
  namespace: petty-production
type: Opaque
stringData:
  postgres-password: <base64-encoded>
  redis-password: <base64-encoded>
  jwt-secret: <base64-encoded>
```

### Application Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: petty-api
  namespace: petty-production
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
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: petty-api
        image: ghcr.io/kakashi3lite/petty:latest
        ports:
        - containerPort: 8080
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: petty-secrets
              key: postgres-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

### Service and Ingress
```yaml
apiVersion: v1
kind: Service
metadata:
  name: petty-api-service
  namespace: petty-production
spec:
  selector:
    app: petty-api
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: petty-api-ingress
  namespace: petty-production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.petty.yourdomain.com
    secretName: petty-tls
  rules:
  - host: api.petty.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: petty-api-service
            port:
              number: 80
```

## Security Hardening

### Container Security
```bash
# Scan container for vulnerabilities
trivy image ghcr.io/kakashi3lite/petty:latest

# Verify signatures
cosign verify ghcr.io/kakashi3lite/petty:latest

# Check SBOM
cosign download sbom ghcr.io/kakashi3lite/petty:latest
```

### Network Security
```bash
# Configure firewall rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5432/tcp   # PostgreSQL (internal only)
ufw deny 6379/tcp   # Redis (internal only)
ufw enable
```

### SSL/TLS Configuration
```nginx
# Nginx configuration for production
server {
    listen 443 ssl http2;
    server_name api.petty.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/petty.crt;
    ssl_certificate_key /etc/ssl/private/petty.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Observability

### Prometheus Configuration
```yaml
# prometheus.yml for production
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'petty-api'
    static_configs:
      - targets: ['petty-api:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Petty Production Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation
```yaml
# Fluentd configuration for log collection
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/petty-*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      index_name petty-logs
    </match>
```

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL backup
kubectl exec -n petty-production postgres-0 -- pg_dump -U petty petty > backup-$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/petty"
DATE=$(date +%Y%m%d_%H%M%S)
kubectl exec -n petty-production postgres-0 -- pg_dump -U petty petty | gzip > "$BACKUP_DIR/petty-$DATE.sql.gz"

# Retention policy (keep 30 days)
find "$BACKUP_DIR" -name "petty-*.sql.gz" -mtime +30 -delete
```

### Configuration Backup
```bash
# Backup Kubernetes resources
kubectl get all,secrets,configmaps -n petty-production -o yaml > k8s-backup-$(date +%Y%m%d).yaml

# Backup Docker volumes
docker run --rm -v petty_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz /data
```

## Disaster Recovery

### Recovery Time Objectives (RTO)
- **Database Recovery**: < 4 hours
- **Application Recovery**: < 1 hour
- **Full System Recovery**: < 8 hours

### Recovery Point Objectives (RPO)
- **Database**: < 1 hour data loss
- **Configuration**: < 24 hours
- **Logs**: < 15 minutes

### Recovery Procedures
1. **Database Recovery**:
   ```bash
   # Restore from backup
   kubectl exec -n petty-production postgres-0 -- psql -U petty -d petty < backup-20240101.sql
   ```

2. **Application Recovery**:
   ```bash
   # Redeploy application
   kubectl rollout restart deployment/petty-api -n petty-production
   ```

3. **Full System Recovery**:
   ```bash
   # Restore entire namespace
   kubectl apply -f k8s-backup-20240101.yaml
   ```

## Performance Tuning

### Database Optimization
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

### Application Tuning
```yaml
# Resource optimization
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# JVM tuning (if applicable)
env:
- name: JAVA_OPTS
  value: "-Xms512m -Xmx1g -XX:+UseG1GC"
```

### Caching Strategy
```python
# Redis caching configuration
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'redis:6379',
        'OPTIONS': {
            'DB': 0,
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Container Won't Start**:
   ```bash
   # Check logs
   docker logs petty-api
   kubectl logs -n petty-production deployment/petty-api
   
   # Check resource usage
   docker stats
   kubectl top pods -n petty-production
   ```

2. **Database Connection Issues**:
   ```bash
   # Test connectivity
   docker exec -it petty-postgres psql -U petty -d petty -c "SELECT 1;"
   kubectl exec -n petty-production postgres-0 -- psql -U petty -d petty -c "SELECT 1;"
   ```

3. **Authentication Failures**:
   ```bash
   # Check JWT configuration
   docker exec -it petty-api env | grep JWT
   kubectl exec -n petty-production deployment/petty-api -- env | grep JWT
   ```

### Performance Issues
```bash
# Monitor resource usage
docker stats
kubectl top nodes
kubectl top pods -n petty-production

# Check application metrics
curl http://localhost:8080/metrics

# Database performance
docker exec -it petty-postgres psql -U petty -d petty -c "
  SELECT query, calls, total_time, mean_time 
  FROM pg_stat_statements 
  ORDER BY total_time DESC LIMIT 10;"
```

### Log Analysis
```bash
# Application logs
docker logs petty-api --tail 100 -f
kubectl logs -n petty-production deployment/petty-api --tail 100 -f

# System logs
journalctl -u docker -f
journalctl -u kubelet -f

# Log aggregation query
# In Grafana/Prometheus
sum(rate(log_messages_total{level="error"}[5m])) by (service)
```

## Maintenance

### Regular Maintenance Tasks
- **Weekly**: Security updates, log rotation
- **Monthly**: Performance review, capacity planning
- **Quarterly**: Security assessment, disaster recovery testing
- **Annually**: Architecture review, technology updates

### Update Procedures
1. **Security Updates**:
   ```bash
   # Update base images
   docker pull python:3.11-slim-bullseye
   make docker-build
   
   # Update dependencies
   pip install --upgrade -r requirements.txt
   ```

2. **Application Updates**:
   ```bash
   # Rolling update
   kubectl set image deployment/petty-api petty-api=ghcr.io/kakashi3lite/petty:v1.1.0 -n petty-production
   kubectl rollout status deployment/petty-api -n petty-production
   ```

---

For additional support, please refer to the main documentation or contact the development team.