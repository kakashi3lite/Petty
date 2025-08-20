# System Architecture Overview

## High-Level Architecture

Petty is built as a serverless, event-driven system on AWS, designed for scalability, security, and real-time responsiveness.

```mermaid
graph TB
    subgraph "Client Layer"
        Mobile[Flutter Mobile App]
        WebApp[Web Dashboard]
        CLI[CLI Tools]
    end

    subgraph "API Gateway Layer"
        APIGW[AWS API Gateway]
        WS[WebSocket API]
        LB[Load Balancer]
    end

    subgraph "Authentication & Security"
        Auth[JWT/API Key Auth]
        RateLimit[Rate Limiter]
        WAF[AWS WAF]
    end

    subgraph "Serverless Compute"
        DataProcessor[Data Processor Lambda]
        BehaviorAnalyzer[Behavior Analyzer Lambda]
        TimelineGen[Timeline Generator Lambda]
        FeedbackHandler[Feedback Handler Lambda]
        AlertProcessor[Alert Processor Lambda]
    end

    subgraph "AI/ML Services"
        BehaviorModel[Behavioral Interpreter]
        NutritionCalc[Nutrition Calculator]
        RecommendationEngine[Recommendation Engine]
        AnomalyDetector[Anomaly Detection]
    end

    subgraph "Data Layer"
        Timestream[(AWS Timestream)]
        S3[(S3 Buckets)]
        DynamoDB[(DynamoDB)]
        ElastiCache[(ElastiCache)]
    end

    subgraph "External Services"
        SQS[AWS SQS]
        SNS[AWS SNS]
        EventBridge[EventBridge]
        CloudWatch[CloudWatch]
    end

    Mobile --> APIGW
    WebApp --> APIGW
    CLI --> APIGW
    
    APIGW --> Auth
    APIGW --> RateLimit
    APIGW --> WAF
    
    Auth --> DataProcessor
    Auth --> BehaviorAnalyzer
    Auth --> TimelineGen
    Auth --> FeedbackHandler
    
    DataProcessor --> BehaviorModel
    DataProcessor --> Timestream
    DataProcessor --> SQS
    
    BehaviorAnalyzer --> BehaviorModel
    BehaviorAnalyzer --> NutritionCalc
    BehaviorAnalyzer --> RecommendationEngine
    BehaviorAnalyzer --> AnomalyDetector
    
    TimelineGen --> DynamoDB
    TimelineGen --> ElastiCache
    
    FeedbackHandler --> S3
    FeedbackHandler --> DynamoDB
    
    AlertProcessor --> SNS
    AlertProcessor --> EventBridge
    
    SQS --> AlertProcessor
    EventBridge --> CloudWatch
```

## Core Components

### 1. Data Ingestion Pipeline

```mermaid
sequenceDiagram
    participant Collar as Smart Collar
    participant Gateway as API Gateway
    participant Processor as Data Processor
    participant Validator as Input Validator
    participant Store as Timestream DB
    participant Queue as SQS Queue
    participant Analyzer as Behavior Analyzer

    Collar->>Gateway: POST /ingest (sensor data)
    Gateway->>Processor: Route request
    Processor->>Validator: Validate input
    Validator->>Processor: Validated data
    Processor->>Store: Store raw metrics
    Processor->>Queue: Enqueue for analysis
    Queue->>Analyzer: Process behavior analysis
    Analyzer->>Processor: Analysis complete
    Processor->>Collar: Response (status)
```

### 2. Behavioral Analysis Engine

```mermaid
graph LR
    subgraph "Input Processing"
        RawData[Raw Sensor Data]
        Validator[Input Validator]
        Normalizer[Data Normalizer]
    end

    subgraph "Feature Engineering"
        ActivityExtractor[Activity Feature Extractor]
        HeartRateAnalyzer[Heart Rate Analyzer]
        LocationProcessor[Location Processor]
        TemporalAnalyzer[Temporal Pattern Analyzer]
    end

    subgraph "AI Models"
        BehaviorClassifier[Behavior Classifier]
        AnomalyDetector[Anomaly Detector]
        HealthScorer[Health Score Calculator]
        PredictiveModel[Predictive Model]
    end

    subgraph "Post-Processing"
        ConfidenceScorer[Confidence Scorer]
        EventGenerator[Event Generator]
        AlertTrigger[Alert Trigger]
    end

    RawData --> Validator
    Validator --> Normalizer
    Normalizer --> ActivityExtractor
    Normalizer --> HeartRateAnalyzer
    Normalizer --> LocationProcessor
    Normalizer --> TemporalAnalyzer

    ActivityExtractor --> BehaviorClassifier
    HeartRateAnalyzer --> HealthScorer
    LocationProcessor --> BehaviorClassifier
    TemporalAnalyzer --> PredictiveModel

    BehaviorClassifier --> ConfidenceScorer
    AnomalyDetector --> AlertTrigger
    HealthScorer --> EventGenerator
    PredictiveModel --> EventGenerator

    ConfidenceScorer --> EventGenerator
    EventGenerator --> AlertTrigger
```

### 3. Real-Time Communication

```mermaid
graph TB
    subgraph "Mobile App"
        Dashboard[Dashboard Screen]
        Profile[Pet Profile Screen]
        Alerts[Alert Center]
    end

    subgraph "Real-Time Layer"
        WS[WebSocket Gateway]
        ConnectionManager[Connection Manager]
        MessageRouter[Message Router]
        PresenceService[Presence Service]
    end

    subgraph "Event Sources"
        BehaviorEvents[Behavior Events]
        AlertEvents[Alert Events]
        StatusUpdates[Status Updates]
        FeedbackEvents[Feedback Events]
    end

    subgraph "Caching Layer"
        Redis[(Redis Cache)]
        SessionStore[(Session Store)]
    end

    Dashboard --> WS
    Profile --> WS
    Alerts --> WS

    WS --> ConnectionManager
    ConnectionManager --> MessageRouter
    ConnectionManager --> PresenceService

    BehaviorEvents --> MessageRouter
    AlertEvents --> MessageRouter
    StatusUpdates --> MessageRouter
    FeedbackEvents --> MessageRouter

    MessageRouter --> Redis
    PresenceService --> SessionStore

    MessageRouter --> Dashboard
    MessageRouter --> Profile
    MessageRouter --> Alerts
```

## Security Architecture

```mermaid
graph TB
    subgraph "Perimeter Security"
        CloudFront[CloudFront CDN]
        WAF[AWS WAF]
        Shield[AWS Shield]
    end

    subgraph "API Security"
        APIGateway[API Gateway]
        Authorizer[Lambda Authorizer]
        RateLimiter[Rate Limiter]
        IPWhitelist[IP Whitelist]
    end

    subgraph "Application Security"
        InputValidator[Input Validator]
        OutputSanitizer[Output Sanitizer]
        Redactor[PII Redactor]
        Encryptor[Data Encryptor]
    end

    subgraph "Infrastructure Security"
        VPC[Private VPC]
        SecurityGroups[Security Groups]
        NACLs[Network ACLs]
        IAMRoles[IAM Roles]
    end

    subgraph "Data Security"
        KMS[AWS KMS]
        SecretsManager[Secrets Manager]
        SSE[S3 Server-Side Encryption]
        VolumeEncryption[EBS Encryption]
    end

    CloudFront --> WAF
    WAF --> Shield
    Shield --> APIGateway

    APIGateway --> Authorizer
    APIGateway --> RateLimiter
    APIGateway --> IPWhitelist

    Authorizer --> InputValidator
    InputValidator --> OutputSanitizer
    OutputSanitizer --> Redactor
    Redactor --> Encryptor

    Encryptor --> VPC
    VPC --> SecurityGroups
    SecurityGroups --> NACLs
    NACLs --> IAMRoles

    IAMRoles --> KMS
    KMS --> SecretsManager
    SecretsManager --> SSE
    SSE --> VolumeEncryption
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Data Sources"
        Collar[Smart Collar]
        Mobile[Mobile App]
        Web[Web Interface]
        API[Third-party APIs]
    end

    subgraph "Ingestion Layer"
        Gateway[API Gateway]
        Kinesis[Kinesis Data Streams]
        Firehose[Kinesis Firehose]
    end

    subgraph "Processing Layer"
        Lambda[Lambda Functions]
        EMR[EMR Clusters]
        Glue[AWS Glue]
    end

    subgraph "Storage Layer"
        Timestream[(Timestream)]
        S3[(S3 Data Lake)]
        DynamoDB[(DynamoDB)]
        RDS[(RDS Aurora)]
    end

    subgraph "Analytics Layer"
        QuickSight[QuickSight]
        Athena[Athena]
        SageMaker[SageMaker]
    end

    subgraph "Output Layer"
        Dashboard[Dashboards]
        Reports[Reports]
        Alerts[Real-time Alerts]
        ML[ML Models]
    end

    Collar --> Gateway
    Mobile --> Gateway
    Web --> Gateway
    API --> Gateway

    Gateway --> Kinesis
    Kinesis --> Firehose
    Kinesis --> Lambda

    Lambda --> Timestream
    Lambda --> DynamoDB
    Firehose --> S3
    EMR --> S3
    Glue --> RDS

    Timestream --> Athena
    S3 --> Athena
    DynamoDB --> QuickSight
    RDS --> SageMaker

    Athena --> Dashboard
    QuickSight --> Reports
    SageMaker --> ML
    Lambda --> Alerts
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Source Control"
        GitHub[GitHub Repository]
        Branches[Feature Branches]
    end

    subgraph "CI/CD Pipeline"
        Actions[GitHub Actions]
        Build[Build & Test]
        Security[Security Scans]
        Deploy[Deployment]
    end

    subgraph "Environments"
        Dev[Development]
        Staging[Staging]
        Prod[Production]
    end

    subgraph "Infrastructure as Code"
        SAM[AWS SAM]
        CloudFormation[CloudFormation]
        Terraform[Terraform]
    end

    subgraph "Monitoring & Observability"
        CloudWatch[CloudWatch]
        XRay[X-Ray Tracing]
        Logs[CloudWatch Logs]
    end

    GitHub --> Actions
    Branches --> Actions
    Actions --> Build
    Build --> Security
    Security --> Deploy

    Deploy --> Dev
    Deploy --> Staging
    Deploy --> Prod

    SAM --> CloudFormation
    CloudFormation --> Terraform

    Dev --> CloudWatch
    Staging --> CloudWatch
    Prod --> CloudWatch

    CloudWatch --> XRay
    XRay --> Logs
```

## Scalability Patterns

### Auto-Scaling Strategy
```mermaid
graph LR
    subgraph "Metrics Collection"
        CPUMetrics[CPU Utilization]
        MemoryMetrics[Memory Usage]
        RequestMetrics[Request Count]
        LatencyMetrics[Response Latency]
    end

    subgraph "Scaling Triggers"
        CloudWatch[CloudWatch Alarms]
        ASG[Auto Scaling Groups]
        Lambda[Lambda Concurrency]
    end

    subgraph "Scaling Actions"
        ScaleOut[Scale Out]
        ScaleIn[Scale In]
        PreWarming[Pre-warming]
    end

    CPUMetrics --> CloudWatch
    MemoryMetrics --> CloudWatch
    RequestMetrics --> CloudWatch
    LatencyMetrics --> CloudWatch

    CloudWatch --> ASG
    CloudWatch --> Lambda
    
    ASG --> ScaleOut
    ASG --> ScaleIn
    Lambda --> PreWarming
```

### Caching Strategy
```mermaid
graph TB
    subgraph "Cache Layers"
        CDN[CloudFront CDN]
        AppCache[Application Cache]
        DatabaseCache[Database Cache]
        SessionCache[Session Cache]
    end

    subgraph "Cache Types"
        Static[Static Assets]
        API[API Responses]
        Database[Database Queries]
        Session[Session Data]
    end

    subgraph "Cache Invalidation"
        TTL[Time-to-Live]
        EventBased[Event-based]
        Manual[Manual Flush]
    end

    Static --> CDN
    API --> AppCache
    Database --> DatabaseCache
    Session --> SessionCache

    CDN --> TTL
    AppCache --> EventBased
    DatabaseCache --> TTL
    SessionCache --> Manual
```

## Performance Characteristics

| Component | Latency Target | Throughput Target | Availability |
|-----------|----------------|-------------------|--------------|
| API Gateway | < 100ms | 10,000 req/s | 99.95% |
| Lambda Functions | < 500ms | 1,000 concurrent | 99.9% |
| Database Queries | < 50ms | 5,000 ops/s | 99.99% |
| Real-time Updates | < 200ms | 1,000 connections | 99.9% |
| Behavioral Analysis | < 2s | 100 analyses/min | 99.5% |

## Disaster Recovery

```mermaid
graph LR
    subgraph "Primary Region"
        PrimaryData[(Primary Data)]
        PrimaryCompute[Primary Compute]
        PrimaryNetwork[Primary Network]
    end

    subgraph "Backup Region"
        BackupData[(Backup Data)]
        BackupCompute[Backup Compute]
        BackupNetwork[Backup Network]
    end

    subgraph "Recovery Process"
        Monitoring[Health Monitoring]
        Failover[Automatic Failover]
        Restoration[Data Restoration]
    end

    PrimaryData -.->|Cross-Region Replication| BackupData
    PrimaryCompute -.->|Standby Resources| BackupCompute
    PrimaryNetwork -.->|Route 53 Health Checks| BackupNetwork

    Monitoring --> Failover
    Failover --> BackupData
    Failover --> BackupCompute
    Failover --> BackupNetwork

    BackupData --> Restoration
    BackupCompute --> Restoration
    BackupNetwork --> Restoration
```

## Technology Stack

### Backend
- **Runtime**: Python 3.11
- **Framework**: AWS Lambda + SAM
- **Database**: AWS Timestream, DynamoDB
- **Cache**: ElastiCache (Redis)
- **Queue**: AWS SQS
- **Storage**: S3 with SSE-S3

### Frontend
- **Mobile**: Flutter/Dart
- **Web**: React.js (planned)
- **State Management**: Provider/Riverpod
- **HTTP Client**: Dio/http

### DevOps
- **CI/CD**: GitHub Actions
- **IaC**: AWS SAM + CloudFormation
- **Monitoring**: CloudWatch + X-Ray
- **Security**: CodeQL + Bandit

### AI/ML
- **Framework**: scikit-learn + custom models
- **Feature Store**: DynamoDB
- **Model Serving**: Lambda functions
- **Training**: SageMaker (future)

---

**Next**: [Data Flow Architecture](data-flow.md) | [Infrastructure Details](infrastructure.md)