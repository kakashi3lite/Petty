# Frequently Asked Questions (FAQ)

## 🏠 General Questions

### What is Petty?
Petty is an open-source, AI-powered pet monitoring platform that analyzes behavioral data from smart collars to provide real-time health insights, activity tracking, and personalized care recommendations for pets.

### How does Petty work?
Petty collects sensor data (heart rate, activity, location, temperature) from smart pet collars, processes it through AI models to classify behaviors, and provides insights through a mobile app and web dashboard. The system can detect patterns like play sessions, rest periods, and potential health anomalies.

### Is Petty free to use?
Yes! Petty is open-source software released under the MIT license. You can self-host it for free. The only costs are your infrastructure expenses (AWS services, server hosting, etc.) if you choose to deploy it in the cloud.

### What types of pets does Petty support?
Currently, Petty is optimized for dogs, but the system can be adapted for cats and other pets. The behavioral models and health parameters can be customized based on species, breed, age, and size.

## 🔧 Technical Questions

### What hardware do I need?
You need a smart collar or wearable device that can send sensor data via API. Petty includes a simulator for testing, and it's compatible with any device that can send JSON data over HTTP/WebSocket connections.

**Required sensors:**
- Heart rate monitor
- Accelerometer (for activity detection)

**Optional sensors:**
- GPS (for location tracking)
- Temperature sensor
- Battery level indicator

### Can I run Petty without AWS?
Yes! Petty supports multiple deployment options:
- **Local development**: SQLite database with in-memory caching
- **Self-hosted**: PostgreSQL + Redis on your own servers
- **Docker**: Complete containerized deployment
- **Kubernetes**: Scalable cloud-native deployment
- **AWS**: Serverless deployment (recommended for production)

### What programming languages does Petty use?
- **Backend**: Python 3.11+ (FastAPI, Pydantic, scikit-learn)
- **Mobile App**: Flutter/Dart
- **Infrastructure**: AWS SAM, CloudFormation
- **Database**: PostgreSQL, AWS Timestream, Redis
- **AI/ML**: Python with scikit-learn (SageMaker integration planned)

### How accurate is the behavioral analysis?
The current system achieves 85-90% accuracy for basic activities (resting, walking, playing). Accuracy improves over time as the system learns your pet's patterns. User feedback helps train the models for better precision.

**Confidence scores** are provided for each behavioral event, allowing you to filter results based on reliability.

## 📱 Mobile App Questions

### Which mobile platforms are supported?
The Flutter mobile app supports:
- **Android**: Version 6.0+ (API level 23+)
- **iOS**: Version 12.0+
- **Web**: Modern browsers (Chrome, Firefox, Safari, Edge)

### Can I use Petty offline?
The mobile app can cache recent data for offline viewing, but real-time monitoring requires an internet connection. Collar data is buffered locally and synced when connectivity is restored.

### How often does the app update?
The app uses adaptive polling that adjusts based on activity:
- **High activity**: Updates every 5 seconds
- **Normal activity**: Updates every 30 seconds  
- **Rest periods**: Updates every 60 seconds
- **Sleep mode**: Updates every 5 minutes

## 🔒 Security & Privacy Questions

### How is my pet's data protected?
Petty implements enterprise-grade security:
- **Encryption**: Data encrypted at rest (AES-256) and in transit (TLS 1.3)
- **Access Control**: API key authentication and JWT tokens
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: Comprehensive data sanitization
- **Privacy Controls**: PII redaction and data anonymization options

### Who has access to my pet's data?
**You own your data.** With self-hosting, you have complete control. Even with cloud deployment, Petty follows privacy-by-design principles:
- No third-party data sharing without explicit consent
- Optional location data with configurable precision
- Automatic data retention policies
- Export functionality for data portability

### Is location tracking required?
No, location tracking is optional. You can:
- Disable location tracking entirely
- Reduce location precision (e.g., city-level instead of exact coordinates)
- Set geofences without storing precise locations
- Use "home zone" detection without GPS coordinates

### How long is data stored?
Default retention policies:
- **Raw sensor data**: 90 days
- **Behavioral events**: 1 year
- **Health trends**: 2 years
- **User feedback**: Indefinitely (for model training)

All retention periods are configurable and you can export or delete data at any time.

## 🚀 Deployment & Setup Questions

### How long does setup take?
- **Quick start (local)**: 10 minutes
- **Self-hosted deployment**: 30-60 minutes
- **AWS production deployment**: 2-3 hours
- **Enterprise setup with customization**: 1-2 days

### What are the minimum system requirements?
**For local development:**
- 4GB RAM, 2 CPU cores
- 10GB storage
- Python 3.11+, Flutter 3.16+

**For production (self-hosted):**
- 8GB RAM, 4 CPU cores
- 50GB storage with backup
- PostgreSQL, Redis
- SSL certificate for HTTPS

**For AWS deployment:**
- AWS account with appropriate permissions
- SAM CLI and AWS CLI installed
- S3 bucket for deployments

### Can I customize the behavioral models?
Yes! Petty is designed for customization:
- **Breed-specific models**: Adjust thresholds for different breeds
- **Custom activities**: Define new behavior types
- **Health parameters**: Set breed/age appropriate ranges
- **Alert rules**: Configure custom notification triggers
- **Integration hooks**: Add custom data sources and outputs

### How do I backup my data?
**Self-hosted:**
```bash
# Database backup
pg_dump petty_db > backup_$(date +%Y%m%d).sql

# File backup
tar -czf petty_backup_$(date +%Y%m%d).tar.gz data/ logs/
```

**AWS deployment:**
- Timestream: Automatic backups with point-in-time recovery
- S3: Cross-region replication and versioning
- DynamoDB: Continuous backups and on-demand backups

## 🩺 Health & Veterinary Questions

### Should I replace regular vet visits with Petty?
**No, Petty is a monitoring tool, not a replacement for veterinary care.** It helps you:
- Track your pet's normal patterns
- Detect changes that might warrant a vet visit
- Provide data to your veterinarian
- Monitor progress during treatment

**Always consult a veterinarian for health concerns.**

### What health issues can Petty detect?
Petty can identify patterns that may indicate:
- **Activity changes**: Sudden lethargy or hyperactivity
- **Heart rate anomalies**: Irregular patterns or sustained elevation
- **Behavioral changes**: Disrupted sleep patterns, reduced play
- **Temperature variations**: Fever indicators (if temperature sensor available)

**Important**: Petty provides alerts for unusual patterns, not medical diagnoses.

### How do I share data with my veterinarian?
Petty provides several data export options:
- **PDF reports**: Summary reports for vet visits
- **CSV exports**: Raw data for analysis
- **API access**: Direct integration with practice management systems
- **Timeline sharing**: Shareable links for specific time periods

### Can multiple vets access the same pet's data?
Yes, you can:
- Generate temporary access links for specific data ranges
- Create API keys for veterinary practices
- Export reports for email sharing
- Set up automated report delivery

## 🔧 Troubleshooting Questions

### The collar isn't sending data. What should I check?
1. **Network connectivity**: Ensure the collar has internet access
2. **API endpoint**: Verify the correct API URL is configured
3. **Authentication**: Check API key validity
4. **Battery level**: Low battery can affect transmission
5. **Rate limits**: Check for rate limiting errors in logs

**Debug steps:**
```bash
# Test API connectivity
curl -H "Authorization: Bearer your_api_key" https://your-api-url/health

# Check collar simulator
python tools/collar_simulator.py --collar-id "TEST" --endpoint-url "your-api-url"
```

### The mobile app shows "Connection Failed"
Common solutions:
1. **Check API URL**: Ensure correct base URL in app settings
2. **Network issues**: Verify internet connectivity
3. **Firewall**: Check if API port is accessible
4. **SSL issues**: For HTTPS endpoints, verify certificate validity
5. **API authentication**: Confirm API key configuration

**For development:**
- Android emulator: Use `http://10.0.2.2:3000`
- iOS simulator: Use `http://localhost:3000`
- Physical device: Use your computer's IP address

### Behavioral analysis seems inaccurate. How can I improve it?
1. **Provide feedback**: Use the feedback feature to correct misclassifications
2. **Training period**: Allow 1-2 weeks for the system to learn patterns
3. **Breed customization**: Adjust settings for your pet's breed/size
4. **Sensor placement**: Ensure proper collar fit and sensor positioning
5. **Data quality**: Check for sensor malfunctions or intermittent connectivity

### How do I report bugs or request features?
1. **Search existing issues**: Check [GitHub Issues](https://github.com/kakashi3lite/Petty/issues)
2. **Create detailed bug reports**: Include logs, steps to reproduce, environment details
3. **Feature requests**: Use the feature request template
4. **Security issues**: Email security@petty.ai for responsible disclosure
5. **General questions**: Use [GitHub Discussions](https://github.com/kakashi3lite/Petty/discussions)

## 💰 Cost & Licensing Questions

### What does it cost to run Petty?
**Self-hosted**: Only your infrastructure costs (server, storage, bandwidth)

**AWS deployment** (estimated monthly costs for 1 pet):
- Lambda: $2-5 (depending on data frequency)
- Timestream: $5-15 (data storage and queries)
- S3: $1-3 (feedback and file storage)
- API Gateway: $1-5 (API calls)
- **Total**: $10-30/month per pet

**Cost optimization tips:**
- Use AWS Free Tier for development
- Implement data retention policies
- Use S3 Intelligent Tiering
- Monitor usage with CloudWatch

### Can I use Petty commercially?
Yes! The MIT license allows commercial use. You can:
- Offer Petty as a service to customers
- Integrate Petty into commercial products
- Modify and redistribute the software
- Build proprietary extensions

**Requirements**: Include the original MIT license notice in distributions.

### Are there enterprise support options?
Currently, Petty is community-supported. However, we're exploring:
- **Professional support subscriptions**
- **Custom development services**
- **Enterprise deployment assistance**
- **Training and consulting**

Contact team@petty.ai for enterprise inquiries.

## 🔮 Future Plans Questions

### What features are planned for future releases?
**v0.2.0 (Next Release):**
- Advanced ML models for health prediction
- Multi-pet household support
- Veterinarian dashboard
- Integration with fitness trackers

**Future Releases:**
- Computer vision for behavior analysis
- Voice recognition for stress detection
- IoT device integrations (smart feeders, toys)
- Multi-language support
- Mobile app widgets

See our [roadmap](https://github.com/kakashi3lite/Petty/projects) for detailed timelines.

### How can I contribute to Petty's development?
We welcome contributions in many forms:
- **Code**: Submit pull requests for bug fixes and features
- **Documentation**: Improve guides, tutorials, and API docs
- **Testing**: Report bugs, test new features, write test cases
- **Design**: UI/UX improvements for mobile and web apps
- **Community**: Help other users, answer questions, create content

**[📝 Contributing Guide](meta/contributing.md)** | **[💬 Join Discussions](https://github.com/kakashi3lite/Petty/discussions)**

### Will Petty always be free and open source?
Yes! Petty is committed to remaining free and open source under the MIT license. We believe pet health technology should be accessible to everyone.

**Our commitment:**
- Core platform will always be free
- No vendor lock-in or proprietary dependencies
- Community-driven development
- Transparent roadmap and decision-making

---

## 🆘 Still Have Questions?

**Can't find what you're looking for?**

- **📖 Browse Documentation**: [docs.petty.ai](docs/README.md)
- **💬 Ask the Community**: [GitHub Discussions](https://github.com/kakashi3lite/Petty/discussions)
- **🐛 Report Issues**: [GitHub Issues](https://github.com/kakashi3lite/Petty/issues)
- **📧 Contact Us**: support@petty.ai

**Response Times:**
- Community forums: Usually within 24 hours
- GitHub issues: 2-3 business days
- Email support: 3-5 business days

---

**Last Updated**: January 20, 2024 | **Version**: 0.1.0