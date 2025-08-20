# Troubleshooting Guide

Common issues and solutions for Petty deployment, configuration, and operation.

## 🔍 Quick Diagnosis

### System Health Check
```bash
# Run comprehensive system validation
python tests/validate_system.py

# Check API health
curl http://localhost:3000/health

# Check service status
make validate
```

### Log Analysis
```bash
# View application logs
tail -f logs/petty.log

# AWS CloudWatch logs
aws logs tail /aws/lambda/petty-function --follow

# Docker logs
docker logs -f petty-api

# Kubernetes logs
kubectl logs -f deployment/petty-api -n petty
```

## 🚨 Installation Issues

### Python Environment Problems

#### Issue: `ModuleNotFoundError: No module named 'petty'`
**Symptoms:**
```
ImportError: No module named 'petty'
```

**Solutions:**
```bash
# Solution 1: Reinstall in development mode
pip install -e .

# Solution 2: Check Python path
python -c "import sys; print(sys.path)"

# Solution 3: Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Solution 4: Clear pip cache
pip cache purge
pip install --no-cache-dir -e .
```

#### Issue: `TOML Parsing Error`
**Symptoms:**
```
tomllib.TOMLDecodeError: Unescaped '\' in a string
```

**Solutions:**
```bash
# Check pyproject.toml syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Common fixes in pyproject.toml:
# Change: "class .*\bProtocol\):"
# To:     "class .*\\bProtocol\\):"
```

#### Issue: `Permission Denied` on Windows
**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**
```powershell
# Run as Administrator
Right-click Command Prompt → "Run as administrator"

# Or use user-level install
pip install --user -e .

# Or fix permissions
takeown /f C:\Python311 /r /d y
icacls C:\Python311 /grant %USERNAME%:F /t
```

### Flutter Environment Problems

#### Issue: `Flutter not found`
**Symptoms:**
```
'flutter' is not recognized as an internal or external command
```

**Solutions:**
```bash
# Add Flutter to PATH (Linux/macOS)
export PATH="$PATH:/path/to/flutter/bin"
echo 'export PATH="$PATH:/path/to/flutter/bin"' >> ~/.bashrc

# Add Flutter to PATH (Windows)
setx PATH "%PATH%;C:\src\flutter\bin"

# Verify installation
flutter doctor
```

#### Issue: `Android SDK not found`
**Symptoms:**
```
Android toolchain - develop for Android devices (X)
✗ Unable to locate Android SDK
```

**Solutions:**
```bash
# Install Android Studio
# Download from: https://developer.android.com/studio

# Or set ANDROID_HOME manually
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Accept licenses
flutter doctor --android-licenses
```

## 🔧 Configuration Issues

### Database Connection Problems

#### Issue: `Connection refused` to PostgreSQL
**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
net start postgresql-x64-15     # Windows

# Check connection string
export DATABASE_URL="postgresql://user:pass@localhost:5432/petty"

# Test connection manually
psql $DATABASE_URL -c "SELECT 1"
```

#### Issue: `Authentication failed`
**Symptoms:**
```
FATAL: password authentication failed for user "petty"
```

**Solutions:**
```bash
# Reset database password
sudo -u postgres psql -c "ALTER USER petty PASSWORD 'new_password';"

# Update connection string
export DATABASE_URL="postgresql://petty:new_password@localhost:5432/petty"

# Check pg_hba.conf settings
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Ensure: local all petty md5
```

### Redis Connection Problems

#### Issue: `Redis connection refused`
**Symptoms:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379
```

**Solutions:**
```bash
# Start Redis service
sudo systemctl start redis       # Linux
brew services start redis        # macOS
net start Redis                  # Windows

# Check Redis is running
redis-cli ping

# Check connection URL
export REDIS_URL="redis://localhost:6379/0"

# Test connection
redis-cli -u $REDIS_URL ping
```

## 🌐 API Issues

### Rate Limiting Problems

#### Issue: `429 Too Many Requests`
**Symptoms:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

**Solutions:**
```bash
# Check rate limit configuration
grep -r "rate_limit" src/

# Temporarily disable rate limiting (development only)
export DISABLE_RATE_LIMITING=true

# Increase rate limits in configuration
# Edit config/development.yaml:
rate_limit:
  max_requests: 10000
  window_minutes: 60
```

#### Issue: `Circuit breaker open`
**Symptoms:**
```json
{
  "error": "Service temporarily unavailable",
  "circuit_breaker": "open"
}
```

**Solutions:**
```python
# Reset circuit breaker manually
from src.common.security.rate_limiter import CircuitBreaker
breaker = CircuitBreaker()
breaker.reset()

# Check failure threshold configuration
# Adjust in src/behavioral_interpreter/interpreter.py:
self.circuit_breaker = CircuitBreaker(
    failure_threshold=10,  # Increase threshold
    timeout=30            # Reduce timeout
)
```

### Authentication Issues

#### Issue: `Invalid API key`
**Symptoms:**
```json
{
  "error": "Authentication failed",
  "code": "INVALID_API_KEY"
}
```

**Solutions:**
```bash
# Generate new API key
python -c "
from src.common.security.auth import APIKeyManager
manager = APIKeyManager()
key = manager.generate_api_key('test_service')
print(f'API Key: {key}')
"

# Check API key format
echo "pk_your_api_key" | grep -E "^pk_[a-f0-9]{32}$"

# Test API key
curl -H "Authorization: Bearer pk_your_api_key" http://localhost:3000/health
```

#### Issue: `JWT token expired`
**Symptoms:**
```json
{
  "error": "Token expired",
  "code": "TOKEN_EXPIRED"
}
```

**Solutions:**
```bash
# Generate new JWT token
python -c "
from src.common.security.auth import TokenManager
manager = TokenManager()
token = manager.generate_token('user123')
print(f'JWT Token: {token}')
"

# Check token expiration
python -c "
from src.common.security.auth import TokenManager
manager = TokenManager()
payload = manager.verify_token('your_token_here')
print(payload)
"
```

## 📱 Mobile App Issues

### Connection Problems

#### Issue: `Network request failed`
**Symptoms:**
```
DioError [DioErrorType.connectTimeout]: Connecting timeout
```

**Solutions:**
```dart
// Check API base URL configuration
// In lib/src/config/app_config.dart:
static const String apiBaseUrl = 'http://10.0.2.2:3000';  // Android emulator
// or
static const String apiBaseUrl = 'http://localhost:3000';  // iOS simulator
// or  
static const String apiBaseUrl = 'http://192.168.1.100:3000';  // Physical device

// Increase timeout
final dio = Dio(BaseOptions(
  connectTimeout: Duration(seconds: 30),
  receiveTimeout: Duration(seconds: 30),
));
```

#### Issue: `SSL certificate verification failed`
**Symptoms:**
```
HandshakeException: Handshake error in client
```

**Solutions:**
```dart
// For development only - disable SSL verification
(HttpOverrides.global as HttpOverrides).createHttpClient = (context) {
  return HttpClient()
    ..badCertificateCallback = (X509Certificate cert, String host, int port) => true;
};

// Or add certificate to assets/certificates/
// And configure in pubspec.yaml:
flutter:
  assets:
    - assets/certificates/
```

### UI/UX Issues

#### Issue: `Widget overflow errors`
**Symptoms:**
```
RenderFlex overflowed by X pixels on the right
```

**Solutions:**
```dart
// Wrap with Flexible or Expanded
Flexible(
  child: YourWidget(),
)

// Use SingleChildScrollView for scrollable content
SingleChildScrollView(
  scrollDirection: Axis.horizontal,
  child: YourWidget(),
)

// Use LayoutBuilder for responsive design
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth > 600) {
      return DesktopLayout();
    } else {
      return MobileLayout();
    }
  },
)
```

## 🔍 Performance Issues

### Slow API Response Times

#### Issue: `API responses taking >5 seconds`
**Symptoms:**
- Slow dashboard loading
- Timeout errors
- Poor user experience

**Diagnosis:**
```bash
# Enable performance monitoring
export ENABLE_PERFORMANCE_MONITORING=true

# Check slow queries
tail -f logs/slow_queries.log

# Profile API endpoints
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:3000/realtime?collar_id=SN-12345
```

**Solutions:**
```python
# Add database connection pooling
# In src/common/database.py:
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Add caching for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_pet_info(collar_id: str):
    # Cached function implementation
    pass

# Optimize database queries
# Use select_related() and prefetch_related()
# Add database indexes for frequent queries
```

### High Memory Usage

#### Issue: `Memory usage constantly increasing`
**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Diagnosis:**
```bash
# Monitor memory usage
top -p $(pgrep -f petty)

# Python memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py

# Check for memory leaks
valgrind --tool=memcheck python your_script.py
```

**Solutions:**
```python
# Clear unused variables
import gc
gc.collect()

# Use generators instead of lists for large datasets
def process_large_dataset():
    for item in large_dataset:
        yield process_item(item)

# Implement proper connection cleanup
try:
    # Database operations
    pass
finally:
    connection.close()
```

## 🚨 Security Issues

### SSL/TLS Certificate Problems

#### Issue: `Certificate verification failed`
**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**
```bash
# Check certificate validity
openssl x509 -in certificate.crt -text -noout

# Update CA certificates
sudo apt-get update && sudo apt-get install ca-certificates  # Ubuntu
brew install ca-certificates                                  # macOS

# For development, generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Input Validation Bypass

#### Issue: `Malicious input not being filtered`
**Symptoms:**
- XSS attacks successful
- SQL injection possible
- Invalid data in database

**Solutions:**
```python
# Strengthen input validation
# In src/common/security/input_validators.py:

def validate_collar_id(collar_id: str) -> bool:
    import re
    pattern = r'^[A-Z]{2}-\d{3,6}$'
    return bool(re.match(pattern, collar_id))

# Add output sanitization
import html
def sanitize_output(data: str) -> str:
    return html.escape(data)

# Use parameterized queries
cursor.execute(
    "SELECT * FROM collars WHERE id = %s",
    (collar_id,)
)
```

## 🐳 Docker Issues

### Container Startup Problems

#### Issue: `Container exits immediately`
**Symptoms:**
```
docker ps shows no running containers
Exit code 1 or 125
```

**Solutions:**
```bash
# Check container logs
docker logs container_name

# Run container interactively
docker run -it --entrypoint /bin/bash petty:latest

# Check Dockerfile syntax
docker build --no-cache -t petty:test .

# Verify base image
docker pull python:3.11-slim
```

#### Issue: `Port already in use`
**Symptoms:**
```
Error: bind: address already in use
```

**Solutions:**
```bash
# Find process using port
lsof -i :3000
netstat -tulpn | grep :3000

# Kill process or use different port
docker run -p 3001:3000 petty:latest

# Or stop conflicting container
docker stop $(docker ps -q --filter "publish=3000")
```

### Volume Mount Issues

#### Issue: `Permission denied` accessing volumes
**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/data'
```

**Solutions:**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./data

# Or run with correct user
docker run --user $(id -u):$(id -g) petty:latest

# Update Dockerfile to use proper user
RUN useradd --create-home --shell /bin/bash petty
USER petty
```

## ☸️ Kubernetes Issues

### Pod Startup Problems

#### Issue: `Pods stuck in Pending state`
**Symptoms:**
```
kubectl get pods shows STATUS: Pending
```

**Solutions:**
```bash
# Check pod events
kubectl describe pod pod-name -n petty

# Check node resources
kubectl top nodes
kubectl describe nodes

# Check resource requests/limits
kubectl get pods -n petty -o yaml | grep -A 10 resources

# Scale down or increase node capacity
kubectl scale deployment petty-api --replicas=2 -n petty
```

#### Issue: `ImagePullBackOff error`
**Symptoms:**
```
STATUS: ImagePullBackOff or ErrImagePull
```

**Solutions:**
```bash
# Check image name and tag
kubectl describe pod pod-name -n petty

# Verify image exists
docker pull petty:latest

# Update deployment with correct image
kubectl set image deployment/petty-api petty-api=petty:v1.0.0 -n petty

# Check registry authentication
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password
```

### Service Discovery Issues

#### Issue: `Service not reachable`
**Symptoms:**
```
Connection refused when accessing service
```

**Solutions:**
```bash
# Check service endpoints
kubectl get endpoints -n petty

# Check service selector
kubectl get service petty-api-service -n petty -o yaml

# Check pod labels
kubectl get pods -n petty --show-labels

# Test service connectivity
kubectl run test-pod --image=busybox -n petty --rm -it -- sh
# Inside pod:
nslookup petty-api-service
telnet petty-api-service 80
```

## 📊 Monitoring Issues

### Metrics Not Appearing

#### Issue: `No metrics in dashboard`
**Symptoms:**
- Empty Grafana/CloudWatch dashboards
- No data in monitoring systems

**Solutions:**
```bash
# Check metrics endpoint
curl http://localhost:3000/metrics

# Verify Prometheus configuration
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Check target discovery
curl http://prometheus:9090/api/v1/targets

# Restart monitoring stack
docker-compose restart prometheus grafana
```

### Log Aggregation Problems

#### Issue: `Logs not appearing in centralized system`
**Symptoms:**
- Missing logs in ELK/CloudWatch
- Log shipping errors

**Solutions:**
```bash
# Check log format
tail -f logs/petty.log

# Verify log shipping configuration
docker logs fluentd

# Test log shipping manually
echo "test log message" | logger -t petty

# Check log retention policies
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/petty"
```

## 🔄 Deployment Issues

### CI/CD Pipeline Failures

#### Issue: `GitHub Actions deployment failing`
**Symptoms:**
```
Error: The process 'sam' failed with exit code 1
```

**Solutions:**
```yaml
# Check workflow file syntax
# .github/workflows/deploy.yml

# Add debug output
- name: Debug SAM build
  run: |
    sam build --debug
    ls -la .aws-sam/

# Check AWS credentials
- name: Verify AWS credentials
  run: aws sts get-caller-identity

# Update SAM CLI version
- name: Setup SAM
  uses: aws-actions/setup-sam@v2
  with:
    version: latest
```

### Infrastructure Provisioning Errors

#### Issue: `CloudFormation stack creation failed`
**Symptoms:**
```
CREATE_FAILED: Insufficient permissions
```

**Solutions:**
```bash
# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/deployer \
  --action-names cloudformation:CreateStack \
  --resource-arns "*"

# Update IAM policy
aws iam put-user-policy \
  --user-name deployer \
  --policy-name CloudFormationAccess \
  --policy-document file://cf-policy.json

# Check stack events
aws cloudformation describe-stack-events --stack-name petty-prod
```

## 🆘 Emergency Procedures

### Service Down Recovery

#### Complete System Outage
```bash
# 1. Check overall system health
curl -f http://api.yourcompany.com/health || echo "API DOWN"

# 2. Check infrastructure status
aws cloudformation describe-stacks --stack-name petty-prod

# 3. Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# 4. Rollback to last known good version
git log --oneline -10
git checkout <previous-commit>
sam deploy --config-env prod

# 5. Notify stakeholders
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-type: application/json' \
  -d '{"text":"🚨 Petty service outage - rollback initiated"}'
```

#### Database Corruption Recovery
```bash
# 1. Stop all applications
docker-compose stop petty-api

# 2. Create database backup
pg_dump $DATABASE_URL > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from latest good backup
psql $DATABASE_URL < latest_good_backup.sql

# 4. Verify data integrity
python scripts/verify_data_integrity.py

# 5. Restart applications
docker-compose start petty-api
```

## 📋 Diagnostic Commands Reference

### System Information
```bash
# Python environment
python --version
pip list | grep petty
python -c "import petty; print(petty.__version__)"

# System resources
free -h        # Memory usage
df -h          # Disk usage
top -n 1       # CPU usage

# Network connectivity
ping api.yourcompany.com
telnet api.yourcompany.com 443
curl -I https://api.yourcompany.com/health
```

### Service Status
```bash
# Docker
docker ps
docker stats
docker system df

# Kubernetes
kubectl get pods -n petty
kubectl top pods -n petty
kubectl get events -n petty --sort-by='.lastTimestamp'

# AWS
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
aws lambda get-function --function-name petty-function
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/petty"
```

### Application Debugging
```bash
# Enable debug logging
export LOG_LEVEL=debug
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Python debugging
python -m pdb src/main.py
python -c "import src.behavioral_interpreter.interpreter; print('OK')"

# Database debugging
psql $DATABASE_URL -c "\dt"  # List tables
psql $DATABASE_URL -c "SELECT COUNT(*) FROM collar_data;"

# Cache debugging
redis-cli info
redis-cli keys "*"
```

## 📞 Getting Help

### Self-Service Resources
1. **Search this guide** for your specific error message
2. **Check logs** for detailed error information
3. **Review configuration** for common misconfigurations
4. **Run diagnostic commands** to gather system information

### Community Support
1. **GitHub Issues**: [Report bugs](https://github.com/kakashi3lite/Petty/issues)
2. **GitHub Discussions**: [Ask questions](https://github.com/kakashi3lite/Petty/discussions)
3. **Documentation**: [Browse all docs](../README.md)

### Professional Support
- **Email**: support@petty.ai
- **Priority Support**: Available for enterprise customers
- **Consulting**: Custom deployment and integration services

### Creating Effective Bug Reports

Include this information when reporting issues:

```markdown
## Environment
- OS: Ubuntu 22.04
- Python: 3.11.0
- Petty version: 0.1.0
- Deployment: Docker Compose

## Issue Description
Brief description of the problem

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Logs
```
[Paste relevant log entries here]
```

## Additional Context
Any other relevant information
```

---

**Still Need Help?** 

If this guide doesn't solve your issue, please [open a GitHub issue](https://github.com/kakashi3lite/Petty/issues) with detailed information about your problem.

**Last Updated**: January 20, 2024 | **Version**: 0.1.0