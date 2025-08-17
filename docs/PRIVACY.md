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
