"""
GitHub Issue Creator Lambda function.
Creates GitHub issues for system alerts with detailed information and links.
"""

import json
import os
import boto3
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS clients
ssm_client = boto3.client('ssm')
cloudwatch_client = boto3.client('cloudwatch')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for GitHub issue creation
    
    Creates GitHub issues with:
    1. Alarm details and timeline
    2. Links to CloudWatch dashboards
    3. Current system metrics
    4. Recommended actions
    """
    logger.info("GitHub issue creation triggered", extra={"event": event})
    
    try:
        # Extract alarm data from Step Functions input
        alarm_data = event.get('alarmData', {})
        safe_mode = event.get('safeMode', 'unknown')
        
        if not alarm_data.get('AlarmName'):
            logger.error("No alarm data provided")
            return {"statusCode": 400, "body": "No alarm data provided"}
        
        # Get GitHub token from SSM
        github_token = _get_github_token()
        if not github_token:
            logger.error("GitHub token not available")
            return {"statusCode": 500, "body": "GitHub token not configured"}
        
        # Collect system metrics
        metrics = _collect_system_metrics(alarm_data)
        
        # Generate dashboard links
        dashboard_links = _generate_dashboard_links(alarm_data)
        
        # Create issue content
        issue_title = _generate_issue_title(alarm_data, safe_mode)
        issue_body = _generate_issue_body(alarm_data, safe_mode, metrics, dashboard_links)
        
        # Create GitHub issue
        issue_url = _create_github_issue(github_token, issue_title, issue_body, safe_mode)
        
        logger.info(f"GitHub issue created: {issue_url}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "GitHub issue created successfully",
                "issue_url": issue_url,
                "alarm": alarm_data.get("AlarmName")
            })
        }
        
    except Exception as e:
        logger.error(f"GitHub issue creation failed: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to create GitHub issue"})
        }


def _get_github_token() -> Optional[str]:
    """Retrieve GitHub token from SSM Parameter Store"""
    try:
        parameter_name = os.environ.get('GITHUB_TOKEN_PARAMETER', '/petty/github-token')
        
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        return response['Parameter']['Value']
        
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub token: {e}")
        return None


def _collect_system_metrics(alarm_data: Dict[str, Any]) -> Dict[str, Any]:
    """Collect current system metrics from CloudWatch"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=30)
        
        metrics = {}
        
        # API Gateway metrics
        try:
            api_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApiGatewayV2',
                MetricName='4XXError',
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            if api_metrics['Datapoints']:
                latest_errors = api_metrics['Datapoints'][-1]['Sum']
                metrics['api_4xx_errors'] = latest_errors
            
        except Exception as e:
            logger.warning(f"Failed to get API Gateway metrics: {e}")
        
        # Lambda metrics
        try:
            lambda_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            if lambda_metrics['Datapoints']:
                latest_errors = lambda_metrics['Datapoints'][-1]['Sum']
                metrics['lambda_errors'] = latest_errors
                
        except Exception as e:
            logger.warning(f"Failed to get Lambda metrics: {e}")
        
        # Lambda duration metrics
        try:
            duration_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if duration_metrics['Datapoints']:
                avg_duration = duration_metrics['Datapoints'][-1]['Average']
                metrics['lambda_avg_duration'] = round(avg_duration, 2)
                
        except Exception as e:
            logger.warning(f"Failed to get Lambda duration metrics: {e}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        return {}


def _generate_dashboard_links(alarm_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate CloudWatch dashboard and log links"""
    region = alarm_data.get('Region', 'us-east-1')
    account_id = alarm_data.get('AccountId', '')
    
    base_url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}"
    
    return {
        "cloudwatch_alarms": f"{base_url}#alarmsV2:alarm/{alarm_data.get('AlarmName', '')}",
        "cloudwatch_metrics": f"{base_url}#metricsV2:",
        "lambda_logs": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups",
        "api_gateway_logs": f"https://{region}.console.aws.amazon.com/apigateway/main/apis?region={region}"
    }


def _generate_issue_title(alarm_data: Dict[str, Any], safe_mode: str) -> str:
    """Generate GitHub issue title"""
    alarm_name = alarm_data.get('AlarmName', 'Unknown Alarm')
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    
    return f"🚨 System Alert: {alarm_name} - Safe Mode: {safe_mode.upper()} [{timestamp}]"


def _generate_issue_body(alarm_data: Dict[str, Any], safe_mode: str, 
                        metrics: Dict[str, Any], dashboard_links: Dict[str, str]) -> str:
    """Generate detailed GitHub issue body"""
    
    # Format timestamp
    state_change_time = alarm_data.get('StateChangeTime', datetime.utcnow().isoformat())
    try:
        dt = datetime.fromisoformat(state_change_time.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = state_change_time
    
    # Generate automatic actions based on safe mode
    auto_actions = _get_automatic_actions(safe_mode)
    
    issue_body = f"""# System Alert: {alarm_data.get('AlarmName', 'Unknown')}

## 📊 Incident Summary
- **Alert Time**: {formatted_time}
- **Alarm State**: {alarm_data.get('NewStateValue', 'UNKNOWN')}
- **Safe Mode Level**: {safe_mode.upper()}
- **Reason**: {alarm_data.get('NewStateReason', 'No reason provided')}

## 📈 Current Metrics
"""

    if metrics:
        for metric_name, value in metrics.items():
            formatted_name = metric_name.replace('_', ' ').title()
            issue_body += f"- **{formatted_name}**: {value}\n"
    else:
        issue_body += "- No metrics available at this time\n"

    issue_body += f"""
## 🔗 Dashboard Links
- [CloudWatch Alarm]({dashboard_links.get('cloudwatch_alarms', '#')})
- [CloudWatch Metrics]({dashboard_links.get('cloudwatch_metrics', '#')})
- [Lambda Logs]({dashboard_links.get('lambda_logs', '#')})
- [API Gateway]({dashboard_links.get('api_gateway_logs', '#')})

## 🤖 Automatic Actions Taken
"""

    for action in auto_actions:
        issue_body += f"- ✅ {action}\n"

    manual_actions = _get_manual_actions(safe_mode)
    if manual_actions:
        issue_body += "\n## 👤 Manual Actions Required\n"
        for action in manual_actions:
            issue_body += f"- ⚠️ {action}\n"

    issue_body += f"""
## 🔧 Safe Mode Configuration
- **Rate Limit Multiplier**: {_get_rate_limit_multiplier(safe_mode)}
- **Heavy Route Throttling**: {'Enabled' if safe_mode != 'normal' else 'Disabled'}
- **Max Concurrent Requests**: {_get_max_concurrent_requests(safe_mode)}

## 📋 Recovery Checklist
- [ ] Monitor system metrics for improvement
- [ ] Verify alarm state returns to OK
- [ ] Check application logs for errors
- [ ] Validate user experience
- [ ] Consider safe mode reduction if metrics improve
- [ ] Update incident documentation

## 🏷️ Labels
This issue was automatically created by the Petty alarm mitigation system.
"""

    return issue_body


def _get_automatic_actions(safe_mode: str) -> List[str]:
    """Get list of automatic actions taken based on safe mode"""
    actions = [
        f"Set system safe mode to {safe_mode.upper()}",
        "Updated Lambda function environment variables",
        "Enabled enhanced monitoring and logging"
    ]
    
    if safe_mode in ['elevated', 'critical', 'emergency']:
        actions.append("Enabled heavy route throttling (429 responses)")
    
    if safe_mode in ['critical', 'emergency']:
        actions.append("Reduced rate limits significantly")
        actions.append("Limited maximum concurrent requests")
    
    if safe_mode == 'emergency':
        actions.append("Enabled emergency throttling for all non-essential routes")
    
    return actions


def _get_manual_actions(safe_mode: str) -> List[str]:
    """Get list of manual actions required based on safe mode"""
    if safe_mode == 'emergency':
        return [
            "Investigate root cause immediately",
            "Consider scaling infrastructure",
            "Monitor for service degradation",
            "Prepare for potential service restart"
        ]
    elif safe_mode == 'critical':
        return [
            "Review system performance metrics",
            "Check for unusual traffic patterns",
            "Verify database connectivity and performance"
        ]
    else:
        return []


def _get_rate_limit_multiplier(safe_mode: str) -> str:
    """Get rate limit multiplier description for safe mode"""
    multipliers = {
        'normal': '1.0 (no throttling)',
        'elevated': '0.7 (30% throttling)',
        'critical': '0.3 (70% throttling)', 
        'emergency': '0.1 (90% throttling)'
    }
    return multipliers.get(safe_mode, '1.0 (unknown)')


def _get_max_concurrent_requests(safe_mode: str) -> int:
    """Get max concurrent requests for safe mode"""
    limits = {
        'normal': 100,
        'elevated': 70,
        'critical': 30,
        'emergency': 10
    }
    return limits.get(safe_mode, 100)


def _create_github_issue(github_token: str, title: str, body: str, safe_mode: str) -> str:
    """Create GitHub issue using the GitHub API"""
    try:
        repo = os.environ.get('GITHUB_REPO', 'kakashi3lite/Petty')
        url = f"https://api.github.com/repos/{repo}/issues"
        
        # Determine labels based on safe mode
        labels = ['alert', 'automated']
        if safe_mode == 'critical':
            labels.append('critical')
        elif safe_mode == 'emergency':
            labels.extend(['critical', 'emergency'])
        elif safe_mode == 'elevated':
            labels.append('high-priority')
        
        payload = {
            "title": title,
            "body": body,
            "labels": labels
        }
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            issue_data = response.json()
            return issue_data['html_url']
        
    except Exception as e:
        logger.error(f"Failed to create GitHub issue: {e}")
        raise