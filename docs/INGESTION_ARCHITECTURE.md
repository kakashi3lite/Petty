# Cloud Ingestion Architecture (AWS)

- **Ingestion**: API Gateway (HTTP) → Lambda (DataProcessorFunction)
- **Storage**: Amazon Timestream (CollarMetrics)
- **Processing**: Lambda applies alert rules, persists payloads
- **Security**: Each collar authenticates via token; TLS enforced
