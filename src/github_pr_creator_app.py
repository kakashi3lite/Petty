"""
AWS Lambda function for creating GitHub PRs with optimized configuration.
Triggered by Step Functions after threshold optimization completes.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

import boto3
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Create GitHub PR with optimized behavioral interpreter configuration.
    
    Expected input from Step Functions:
    {
        "optimization_report": {...},
        "config_content": "...",
        "dry_run": false
    }
    """
    try:
        # Extract inputs from Step Functions
        optimization_report = event.get("optimization_report", {})
        config_content = event.get("config_content", "")
        dry_run = event.get("dry_run", False)
        
        if not optimization_report or not config_content:
            raise ValueError("Missing required inputs: optimization_report and config_content")
        
        # GitHub configuration from environment
        github_token = os.environ.get("GITHUB_TOKEN")
        github_repo = os.environ.get("GITHUB_REPO", "kakashi3lite/Petty")
        base_branch = os.environ.get("BASE_BRANCH", "main")
        
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        # Create PR content
        pr_title, pr_body, branch_name = generate_pr_content(optimization_report)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would create PR: {pr_title}")
            return {
                "statusCode": 200,
                "dry_run": True,
                "pr_title": pr_title,
                "branch_name": branch_name,
                "message": "Dry run completed successfully"
            }
        
        # Create GitHub PR
        github_client = GitHubClient(github_token, github_repo)
        
        # Create new branch
        branch_sha = github_client.create_branch(branch_name, base_branch)
        logger.info(f"Created branch {branch_name} from {base_branch}")
        
        # Update configuration file
        config_file_path = "src/behavioral_interpreter/config.py"
        github_client.update_file(
            file_path=config_file_path,
            content=config_content,
            branch=branch_name,
            commit_message=f"feat(mlops): auto-tune interpreter thresholds\n\n{generate_commit_details(optimization_report)}"
        )
        logger.info(f"Updated {config_file_path} in branch {branch_name}")
        
        # Create pull request
        pr_url = github_client.create_pull_request(
            title=pr_title,
            head=branch_name,
            base=base_branch,
            body=pr_body
        )
        logger.info(f"Created PR: {pr_url}")
        
        return {
            "statusCode": 200,
            "pr_url": pr_url,
            "branch_name": branch_name,
            "message": "PR created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create PR: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e),
            "message": "Failed to create PR"
        }

def generate_pr_content(optimization_report: Dict[str, Any]) -> tuple[str, str, str]:
    """Generate PR title, body, and branch name from optimization report"""
    timestamp = optimization_report.get("timestamp", "").replace(":", "-").replace(".", "-")
    branch_name = f"auto-tune/behavioral-thresholds-{timestamp[:16]}"
    
    summary = optimization_report.get("summary", {})
    applied_changes = optimization_report.get("applied_changes", {})
    
    # Count successful optimizations
    successful_behaviors = [behavior for behavior, applied in applied_changes.items() if applied]
    
    pr_title = f"feat(mlops): auto-tune interpreter thresholds ({len(successful_behaviors)} behaviors)"
    
    pr_body = f"""## Automated Threshold Optimization

This PR contains automatically optimized behavioral interpreter thresholds based on user feedback data.

### Summary
- **Feedback data processed**: {optimization_report.get('feedback_data_count', 0)}
- **Behaviors optimized**: {summary.get('successful_optimizations', 0)}/{summary.get('total_behaviors', 0)}
- **Changes applied**: {summary.get('applied_changes_count', 0)}
- **Configuration version**: {optimization_report.get('config_version', 'unknown')}

### Optimized Behaviors
"""
    
    optimization_results = optimization_report.get("optimization_results", {})
    for behavior_type, applied in applied_changes.items():
        if applied and behavior_type in optimization_results:
            results = optimization_results[behavior_type]
            if 'error' not in results:
                pr_body += f"""
#### {behavior_type.replace('_', ' ').title()}
- **F1 Score**: {results.get('f1_score', 0):.3f}
- **Confidence Threshold**: {results.get('confidence_threshold', 0):.3f}
- **Min Data Points**: {results.get('min_data_points', 0)}
- **Heart Rate Range**: ({results.get('min_hr', 0)}, {results.get('max_hr', 0)})
"""
    
    pr_body += f"""
### Safety Measures
- ✅ All thresholds enforced within safety bounds
- ✅ Minimum improvement threshold applied ({optimization_report.get('min_improvement_threshold', 0.05)})
- ✅ Cross-validation used for robust evaluation
- ✅ Rollback available if performance degrades

### Testing
- [ ] Review optimization metrics
- [ ] Verify safety bounds compliance
- [ ] Test behavioral detection accuracy
- [ ] Monitor production performance

**Generated at**: {optimization_report.get('timestamp', 'unknown')}
**Pipeline**: Automated threshold optimization via Step Functions
"""
    
    return pr_title, pr_body, branch_name

def generate_commit_details(optimization_report: Dict[str, Any]) -> str:
    """Generate detailed commit message from optimization report"""
    summary = optimization_report.get("summary", {})
    applied_changes = optimization_report.get("applied_changes", {})
    
    details = f"""Optimized {summary.get('applied_changes_count', 0)} behavioral interpreter thresholds using Bayesian optimization.

Processed {optimization_report.get('feedback_data_count', 0)} feedback items with cross-validation.

Changes applied:"""
    
    optimization_results = optimization_report.get("optimization_results", {})
    for behavior_type, applied in applied_changes.items():
        if applied and behavior_type in optimization_results:
            results = optimization_results[behavior_type]
            if 'error' not in results:
                details += f"\n- {behavior_type}: F1={results.get('f1_score', 0):.3f}"
    
    return details

class GitHubClient:
    """GitHub API client for creating branches and PRs"""
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_ref(self, ref: str) -> Dict[str, Any]:
        """Get reference SHA"""
        url = f"{self.base_url}/repos/{self.repo}/git/ref/heads/{ref}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, branch_name: str, base_branch: str) -> str:
        """Create a new branch from base branch"""
        # Get base branch SHA
        base_ref = self.get_ref(base_branch)
        base_sha = base_ref["object"]["sha"]
        
        # Create new branch
        url = f"{self.base_url}/repos/{self.repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return base_sha
    
    def get_file_content(self, file_path: str, branch: str) -> Optional[Dict[str, Any]]:
        """Get file content and SHA"""
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        params = {"ref": branch}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        
        return response.json()
    
    def update_file(self, file_path: str, content: str, branch: str, commit_message: str):
        """Update or create file content"""
        import base64
        
        # Get existing file to get SHA (required for updates)
        existing_file = self.get_file_content(file_path, branch)
        
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch
        }
        
        if existing_file:
            data["sha"] = existing_file["sha"]
        
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def create_pull_request(self, title: str, head: str, base: str, body: str) -> str:
        """Create a pull request"""
        url = f"{self.base_url}/repos/{self.repo}/pulls"
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        pr_data = response.json()
        return pr_data["html_url"]