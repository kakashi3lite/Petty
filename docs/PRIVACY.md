# Privacy Policy and Data Protection

## Overview

This document outlines Petty's commitment to protecting user privacy and pet data through comprehensive privacy controls, including Differential Privacy mechanisms for analytics exports.

## Data Classification

### Sensitivity Levels

#### Public Data
- Non-identifying pet breed information
- Aggregated, anonymized behavioral statistics  
- Public API documentation and schemas

#### Internal Data
- Pet profile information (name, breed, age)
- Historical behavioral trends (aggregated)
- System performance metrics
- Non-sensitive user preferences

#### Confidential Data
- Real-time location coordinates
- Detailed behavioral events with timestamps
- User account information and authentication data
- Individual pet health indicators

#### Restricted Data
- Precise GPS coordinates (full precision)
- Medical alerts and health emergencies
- User personal information (names, addresses, contacts)
- Payment and billing information

## Data Collection Principles

### Data Minimization
- Only collect data necessary for stated purposes
- Automatic data expiration based on retention policies
- Regular auditing of collected data types
- User controls for data collection granularity

### Purpose Limitation
- Data used only for explicitly stated purposes
- No secondary use without user consent
- Clear boundaries between features and data requirements
- Regular review of data usage patterns

### Storage Minimization
- Raw sensor data aggregated after 48 hours
- Location precision reduced automatically over time
- Automatic deletion of expired data
- Compressed storage formats to minimize footprint

## Privacy-Enhancing Technologies (PETs)

### Differential Privacy Implementation

#### Overview
Petty implements differential privacy (DP) mechanisms for any analytics exports or research data sharing, providing mathematical guarantees of individual privacy protection.

#### DP Parameters
- **Default ε (epsilon)**: 1.0 for standard analytics
- **Research ε**: 0.1 for external research collaborations  
- **δ (delta)**: 1/n where n is the dataset size
- **Clipping bounds**: Based on sensor data ranges
- **Noise mechanism**: Gaussian mechanism for continuous data, Laplace for counts

#### Implementation Details

```python
# Example DP configuration
DP_CONFIG = {
    "standard_analytics": {
        "epsilon": 1.0,
        "delta": 1e-5,
        "mechanism": "gaussian",
        "sensitivity": 2.0
    },
    "research_export": {
        "epsilon": 0.1,
        "delta": 1e-6, 
        "mechanism": "laplace",
        "sensitivity": 1.0
    }
}
```

#### Privacy Budget Management
- Total privacy budget: ε = 10.0 per user per year
- Budget allocation: 70% ongoing analytics, 30% research/special projects
- Automatic budget tracking and enforcement
- User notification when budget approaches limits

### Federated Learning Architecture

#### Design Principles
- Model training distributed across user devices
- No raw data leaves user environment
- Aggregated model updates with DP noise
- Secure aggregation protocols

#### Implementation Status
- **Phase 1** (Current): Centralized rule-based system
- **Phase 2** (Q4 2025): Federated rule refinement
- **Phase 3** (Q2 2026): Full federated ML models
- **Phase 4** (2027): Cross-device collaborative learning

#### Technical Architecture

```
[User Device] → [Local Model Training] → [DP Model Updates] 
                                            ↓
[Secure Aggregation Server] → [Global Model Update] → [Distribution]
                                            ↓
[All User Devices] ← [Updated Global Model] ← [Validation & Testing]
```

#### Privacy Controls
- Users can opt-out of federated learning
- Local-only mode with no model sharing
- Granular control over contribution types
- Transparent reporting of participation impact

## Encryption and Security

### Data at Rest
- **Algorithm**: AES-256-GCM with AWS KMS
- **Key Management**: Automatic key rotation every 90 days
- **Encryption Scope**: All PII and location data
- **Backup Encryption**: Separate key hierarchy for backups

### Data in Transit
- **Protocol**: TLS 1.3 minimum for all communications
- **Certificate Pinning**: Mobile app implements certificate pinning
- **API Security**: mTLS for service-to-service communication
- **IoT Security**: Device-specific X.509 certificates

### Key Management
- **Primary Keys**: AWS KMS with CloudHSM backing
- **Device Keys**: Unique per-device encryption keys
- **User Keys**: Derived keys for user-specific data
- **Rotation Schedule**: Quarterly for high-value keys, annually for device keys

## User Rights and Controls

### Access Rights (GDPR Article 15)
- **Data Export**: JSON format with all user data
- **Data Visualization**: Dashboard showing all collected data
- **Query Interface**: Search and filter collected data
- **Response Time**: Within 30 days of request

#### DSAR (Data Subject Access Request) Flow
1. **Request Initiation**: Users submit DSAR requests via API or support portal
2. **Request Validation**: Automated validation of request parameters and user identity
3. **Data Extraction**: Comprehensive extraction from all data stores (Timestream, S3, etc.)
4. **Privacy Protection**: Differential privacy applied to aggregated data
5. **Bundle Creation**: Cryptographically signed export bundle with manifest
6. **Secure Delivery**: Time-limited presigned URLs for secure download
7. **Audit Trail**: Complete audit log of all DSAR operations

#### DSAR Export Features
- **Comprehensive Coverage**: All behavioral events, sensor metrics, location data
- **Multiple Formats**: JSON primary format with CSV option for tabular data
- **Cryptographic Integrity**: HMAC-SHA256 signatures for data verification
- **Differential Privacy**: Configurable privacy protection for sensitive aggregations
- **Secure Access**: Presigned URLs with 24-hour expiration
- **Audit Compliance**: Full audit trail meeting regulatory requirements

#### DSAR SLAs (Service Level Agreements)
- **Simple Requests**: 72 hours for standard data export
- **Complex Requests**: 7 days for large datasets or custom formats
- **Maximum Response Time**: 30 days (GDPR compliance requirement)
- **Download Availability**: 30 days from completion notification
- **Support Response**: 2 business days for DSAR-related inquiries

### Rectification Rights (GDPR Article 16)
- **Profile Updates**: Real-time updates to pet profiles
- **Data Corrections**: User-initiated corrections to behavioral data
- **Bulk Updates**: CSV upload for historical data corrections
- **Audit Trail**: All changes logged with timestamps

### Erasure Rights (GDPR Article 17)
- **Account Deletion**: Complete removal within 30 days
- **Selective Deletion**: Choose specific data types to delete
- **Backup Purging**: Automated removal from all backups
- **Third-party Notification**: Automatic notification to data processors

#### DSAR Deletion Options
1. **Soft Deletion with Retention Policies**
   - **Standard Policy**: 90-day retention for operational recovery
   - **Short Policy**: 30-day retention for expedited requests
   - **Immediate Policy**: No retention, immediate marking for deletion
   - **Legal Hold**: 7-year retention for compliance requirements

2. **Hard Deletion**
   - **Immediate Removal**: Direct deletion from active systems
   - **Backup Cleanup**: Coordinated removal from all backup systems
   - **Audit Trail**: Comprehensive deletion audit records
   - **Third-party Coordination**: Automatic notification to data processors

#### Deletion SLAs
- **Soft Deletion**: Marked within 24 hours, final deletion per retention policy
- **Hard Deletion**: Complete removal within 7 days
- **Backup Removal**: Within 30 days of deletion request
- **Verification**: Deletion confirmation within 2 business days
- **Appeals Process**: 14 days to contest deletion decisions

### Portability Rights (GDPR Article 20)
- **Standard Formats**: JSON, CSV export options
- **API Access**: RESTful API for programmatic data export
- **Third-party Integration**: Direct export to compatible services
- **Data Validation**: Checksums and validation for exported data

### Objection Rights (GDPR Article 21)
- **Processing Objection**: Opt-out of specific data processing
- **Marketing Opt-out**: Granular marketing communication controls
- **Analytics Opt-out**: Exclude data from analytics and research
- **Profiling Objection**: Disable behavioral profiling features

## DSAR Technical Implementation

### Architecture Overview
The DSAR (Data Subject Access Request) system is implemented using a serverless architecture with AWS Step Functions orchestrating the workflow:

```
API Gateway → DSAR Processor → Step Functions State Machine
                                      ↓
                           ┌─────────────────────┐
                           │  DSAR Workflow      │
                           │                     │
                           │  1. Validate        │
                           │  2. Export/Delete   │
                           │  3. Generate URLs   │
                           │  4. Audit & Notify  │
                           └─────────────────────┘
                                      ↓
                              S3 Bucket (Encrypted)
```

### Core Components

#### 1. DSAR Processor Lambda (`/dsar/request`, `/dsar/status/{id}`)
- Request validation and sanitization
- Step Functions workflow orchestration
- Status tracking and monitoring
- Rate limiting and security controls

#### 2. DSAR Export Lambda
- Comprehensive data extraction from Timestream
- Differential privacy application
- Cryptographic signing and bundle creation
- S3 storage with server-side encryption

#### 3. DSAR Delete Lambda
- Soft deletion with configurable retention
- Hard deletion for immediate compliance
- Backup and third-party coordination
- Comprehensive audit logging

#### 4. Step Functions State Machine
- Reliable workflow orchestration
- Error handling and retry logic
- Parallel processing capabilities
- Audit trail generation

### Security Features

#### Data Protection
- **Encryption at Rest**: AES-256 encryption for all stored data
- **Encryption in Transit**: TLS 1.3 for all data transmission
- **Cryptographic Signing**: HMAC-SHA256 for data integrity
- **Access Controls**: Time-limited presigned URLs (24-hour expiration)

#### Privacy Protection
- **Differential Privacy**: Configurable epsilon values for different use cases
- **Data Minimization**: Only requested data types included in exports
- **Anonymization**: Location data anonymized to area-level precision
- **Audit Compliance**: Full audit trail with 7-year retention

#### Security Controls
- **Rate Limiting**: 5 requests per hour per user for DSAR endpoints
- **Input Validation**: Comprehensive request validation and sanitization
- **Circuit Breakers**: Automatic failure protection with retry logic
- **Monitoring**: Real-time monitoring and alerting for all operations

### API Endpoints

#### POST /dsar/request
Submit a new DSAR request for data export or deletion.

**Request Body:**
```json
{
  "user_id": "string",
  "request_type": "export|delete",
  "data_types": ["behavioral_events", "sensor_metrics", "location_data"],
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z"
  },
  "deletion_type": "soft|hard",
  "retention_policy": "immediate|short|standard|legal_hold",
  "include_raw": false,
  "apply_differential_privacy": true
}
```

**Response:**
```json
{
  "request_id": "abc123def456",
  "status": "processing",
  "message": "DSAR request submitted successfully",
  "estimated_completion": "2024-01-02T12:00:00Z",
  "execution_arn": "arn:aws:states:..."
}
```

#### GET /dsar/status/{request_id}
Check the status of a DSAR request.

**Response:**
```json
{
  "request_id": "abc123def456",
  "status": "completed|processing|failed|cancelled",
  "started_at": "2024-01-01T12:00:00Z",
  "last_updated": "2024-01-01T15:30:00Z",
  "download_url": "https://s3.amazonaws.com/...",
  "download_expires_at": "2024-01-02T15:30:00Z"
}
```

### Compliance and Monitoring

#### Audit Trail
Every DSAR operation generates comprehensive audit records including:
- Request details and validation results
- Data extraction and processing logs
- Export/deletion completion confirmations
- Access and download tracking
- Error and exception handling

#### Metrics and Monitoring
- Request volume and success rates
- Processing time and performance metrics
- Data volume and export sizes
- Security event monitoring
- Compliance reporting dashboards

#### Regulatory Compliance
- **GDPR Articles 15-20**: Full compliance with EU data protection rights
- **Audit Requirements**: 7-year audit trail retention
- **Data Minimization**: Only necessary data collected and processed
- **Privacy by Design**: Built-in privacy protection at every stage

## Privacy Mode Features

### Location Privacy
- **Precision Levels**: 
  - High: ±3 meters (default)
  - Medium: ±50 meters (privacy mode)
  - Low: ±500 meters (maximum privacy)
- **Home Location**: Automatic detection and fuzzing of home area
- **Geofencing**: User-defined areas with enhanced privacy
- **Temporal Fuzzing**: Time-based location blurring

### Behavioral Privacy
- **Aggregation Windows**: Longer time windows in privacy mode
- **Behavior Suppression**: Option to disable specific behavior detection
- **Confidence Thresholds**: Higher thresholds in privacy mode
- **Pattern Breaking**: Artificial noise injection to prevent profiling

### Social Privacy
- **Data Sharing**: Granular controls for vet/family member access
- **Anonymous Mode**: Complete anonymization of public contributions
- **Research Participation**: Opt-in/opt-out for research studies
- **Community Features**: Privacy-preserving social features

## Data Retention and Deletion

### Retention Periods

#### Operational Data
- **Real-time Sensor Data**: 48 hours (raw), 30 days (processed)
- **Location History**: 90 days (precise), 1 year (aggregated)
- **Behavioral Events**: 2 years (individual), 5 years (anonymized patterns)
- **User Interactions**: 1 year (detailed), 3 years (aggregated analytics)

#### Compliance Data
- **Audit Logs**: 7 years (security events), 3 years (general logs)
- **Consent Records**: 7 years after consent withdrawal
- **Data Processing Records**: 3 years after processing ends
- **Legal Hold Data**: Until legal requirement ends

#### Backup Data
- **Operational Backups**: 30 days retention
- **Archive Backups**: 1 year retention with annual review
- **Disaster Recovery**: 2 years retention for critical data
- **Compliance Backups**: Aligned with compliance requirements

### Automated Deletion
- **Daily Cleanup**: Expired temporary data
- **Weekly Cleanup**: Aggregated raw sensor data
- **Monthly Cleanup**: Expired behavioral events
- **Quarterly Cleanup**: User account cleanup for deleted accounts

### Manual Deletion Procedures
- **User Requests**: Processed within 30 days
- **Legal Requests**: Coordinated with legal team
- **Security Incidents**: Emergency deletion procedures
- **Data Breach Response**: Rapid deletion of exposed data

## Consent Management

### Consent Types

#### Required Consents
- **Service Operation**: Basic pet monitoring functionality
- **Data Processing**: Processing of sensor data for behavioral analysis
- **Communication**: Essential service communications
- **Legal Compliance**: Required regulatory and legal processing

#### Optional Consents
- **Analytics**: Contribution to aggregated analytics
- **Research**: Participation in research studies
- **Marketing**: Promotional and marketing communications
- **Social Features**: Sharing with other users or community features

### Consent Mechanisms
- **Granular Controls**: Individual toggles for each consent type
- **Consent Withdrawal**: One-click withdrawal for any consent
- **Consent History**: Complete audit trail of consent changes
- **Regular Review**: Annual consent review and confirmation

### Consent Documentation
- **Legal Basis**: GDPR Article 6 legal basis for each processing activity
- **Purpose Description**: Clear explanation of processing purposes
- **Data Categories**: Specific data types covered by each consent
- **Retention Periods**: Clear timelines for each data category

## Privacy Impact Assessments

### Regular Assessments
- **Feature PIAs**: Required for all new features involving personal data
- **Annual Review**: Comprehensive review of all data processing
- **Incident PIAs**: Assessment after any privacy incidents
- **Third-party PIAs**: Assessment of vendor and partner privacy practices

### Assessment Framework
1. **Data Mapping**: Comprehensive mapping of data flows
2. **Risk Assessment**: Privacy risks to individuals
3. **Mitigation Measures**: Technical and organizational measures
4. **Residual Risk**: Remaining risks after mitigation
5. **Review Schedule**: Regular review and updates

### Stakeholder Involvement
- **Data Protection Officer**: Oversight of all PIAs
- **Engineering Teams**: Technical feasibility assessment
- **Legal Team**: Compliance and legal risk review
- **User Representatives**: User impact assessment

## Vendor and Third-Party Management

### Vendor Privacy Requirements
- **Data Processing Agreements**: GDPR-compliant DPAs with all vendors
- **Privacy Certifications**: SOC 2, ISO 27001, or equivalent
- **Security Assessments**: Regular security and privacy audits
- **Incident Response**: Coordinated incident response procedures

### Data Transfer Controls
- **Adequacy Decisions**: EU adequacy decisions for international transfers
- **Standard Contractual Clauses**: SCCs for non-adequate countries
- **Binding Corporate Rules**: For transfers within multinational organizations
- **Supplementary Measures**: Additional protections for high-risk transfers

### Vendor Monitoring
- **Regular Audits**: Annual privacy and security audits
- **Performance Monitoring**: KPIs for privacy compliance
- **Incident Reporting**: Mandatory incident reporting requirements
- **Contract Review**: Regular review and updates of vendor contracts

---

**Document Version**: 1.0  
**Last Updated**: August 16, 2025  
**Next Review Date**: November 16, 2025  
**Data Protection Officer**: privacy@petty.ai
