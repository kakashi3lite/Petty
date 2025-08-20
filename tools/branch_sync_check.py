#!/usr/bin/env python3
"""
Branch Sync Check Tool

Analyzes all branches against the main branch to determine sync status.
Categorizes branches as: behind, ahead, diverged, or up-to-date.
Provides specific sync commands for each case.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class BranchStatus:
    """Represents the sync status of a branch relative to main."""
    name: str
    status: str  # "behind", "ahead", "diverged", "up-to-date"
    commits_behind: int
    commits_ahead: int
    last_commit_date: str
    last_commit_author: str
    last_commit_hash: str
    sync_command: str
    description: str


class BranchSyncChecker:
    """Main class for analyzing branch synchronization status."""
    
    def __init__(self, main_branch: str = "main"):
        self.main_branch = main_branch
        self.branches: List[BranchStatus] = []
        
    def run_git_command(self, command: List[str]) -> str:
        """Execute a git command and return the output."""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd="."
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running git command {' '.join(command)}: {e}", file=sys.stderr)
            return ""
    
    def get_remote_branches(self) -> List[str]:
        """Get list of all remote branches except main."""
        output = self.run_git_command(["git", "branch", "-r", "--no-merged", f"origin/{self.main_branch}"])
        if not output:
            # Also get merged branches to check if they're up-to-date
            all_output = self.run_git_command(["git", "branch", "-r"])
        else:
            all_output = output
            
        branches = []
        for line in all_output.split('\n'):
            line = line.strip()
            if line and line.startswith('origin/') and not line.endswith(f'origin/{self.main_branch}'):
                branch_name = line.replace('origin/', '')
                if branch_name != self.main_branch:
                    branches.append(branch_name)
        return sorted(set(branches))
    
    def get_branch_commit_info(self, branch: str) -> Dict[str, str]:
        """Get the last commit information for a branch."""
        commit_hash = self.run_git_command([
            "git", "log", f"origin/{branch}", "-1", "--format=%H"
        ])
        commit_date = self.run_git_command([
            "git", "log", f"origin/{branch}", "-1", "--format=%ci"
        ])
        commit_author = self.run_git_command([
            "git", "log", f"origin/{branch}", "-1", "--format=%an"
        ])
        
        return {
            "hash": commit_hash,
            "date": commit_date,
            "author": commit_author
        }
    
    def analyze_branch(self, branch: str) -> BranchStatus:
        """Analyze a single branch against main."""
        # Get commit counts
        behind_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{branch}..origin/{self.main_branch}"
        ])
        ahead_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{self.main_branch}..origin/{branch}"
        ])
        
        commits_behind = int(behind_output) if behind_output.isdigit() else 0
        commits_ahead = int(ahead_output) if ahead_output.isdigit() else 0
        
        # Get commit info
        commit_info = self.get_branch_commit_info(branch)
        
        # Determine status and sync command
        if commits_behind == 0 and commits_ahead == 0:
            status = "up-to-date"
            sync_command = "# No action needed - branch is up-to-date"
            description = "Branch is synchronized with main"
        elif commits_behind > 0 and commits_ahead == 0:
            status = "behind"
            sync_command = f"git checkout {branch} && git merge origin/{self.main_branch}"
            description = f"Can be fast-forwarded ({commits_behind} commits behind)"
        elif commits_behind == 0 and commits_ahead > 0:
            status = "ahead"
            sync_command = f"# Review and consider creating PR for {branch}"
            description = f"Ready for review ({commits_ahead} commits ahead)"
        else:
            status = "diverged"
            sync_command = f"git checkout {branch} && git merge origin/{self.main_branch}  # Manual conflict resolution may be needed"
            description = f"Needs manual merge ({commits_behind} behind, {commits_ahead} ahead)"
        
        return BranchStatus(
            name=branch,
            status=status,
            commits_behind=commits_behind,
            commits_ahead=commits_ahead,
            last_commit_date=commit_info["date"],
            last_commit_author=commit_info["author"],
            last_commit_hash=commit_info["hash"][:8],
            sync_command=sync_command,
            description=description
        )
    
    def analyze_all_branches(self) -> None:
        """Analyze all remote branches."""
        print("🔍 Fetching latest remote information...")
        self.run_git_command(["git", "fetch", "--all", "--prune"])
        
        branches = self.get_remote_branches()
        print(f"📊 Analyzing {len(branches)} branches against {self.main_branch}...")
        
        for i, branch in enumerate(branches, 1):
            print(f"  [{i:2d}/{len(branches)}] {branch}", end="", flush=True)
            status = self.analyze_branch(branch)
            self.branches.append(status)
            print(f" - {status.status}")
    
    def print_summary(self) -> None:
        """Print a summary of branch statuses."""
        status_counts = {}
        for branch in self.branches:
            status_counts[branch.status] = status_counts.get(branch.status, 0) + 1
        
        print(f"\n📈 Branch Sync Summary")
        print(f"{'='*50}")
        print(f"Total branches analyzed: {len(self.branches)}")
        
        for status, count in sorted(status_counts.items()):
            emoji = {
                "up-to-date": "🟢",
                "behind": "🔴", 
                "ahead": "🟡",
                "diverged": "🟠"
            }.get(status, "⚪")
            print(f"{emoji} {status.replace('-', ' ').title()}: {count}")
        
        # Calculate attention needed
        needs_attention = sum(
            count for status, count in status_counts.items() 
            if status != "up-to-date"
        )
        print(f"\n⚠️  Branches needing attention: {needs_attention}")
    
    def print_detailed_report(self) -> None:
        """Print detailed status for each branch."""
        print(f"\n📋 Detailed Branch Status Report")
        print(f"{'='*80}")
        
        # Group by status
        by_status = {}
        for branch in self.branches:
            if branch.status not in by_status:
                by_status[branch.status] = []
            by_status[branch.status].append(branch)
        
        # Print each group
        status_order = ["behind", "diverged", "ahead", "up-to-date"]
        for status in status_order:
            if status not in by_status:
                continue
                
            emoji = {
                "up-to-date": "🟢",
                "behind": "🔴", 
                "ahead": "🟡",
                "diverged": "🟠"
            }.get(status, "⚪")
            
            print(f"\n{emoji} {status.replace('-', ' ').upper()} BRANCHES ({len(by_status[status])})")
            print("-" * 60)
            
            for branch in sorted(by_status[status], key=lambda x: x.name):
                print(f"  📁 {branch.name}")
                print(f"     Last commit: {branch.last_commit_hash} by {branch.last_commit_author}")
                print(f"     Date: {branch.last_commit_date}")
                print(f"     Status: {branch.description}")
                print(f"     Sync: {branch.sync_command}")
                print()
    
    def export_json(self, filename: Optional[str] = None) -> None:
        """Export analysis results to JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"branch_sync_analysis_{timestamp}.json"
        
        data = {
            "analysis_date": datetime.now().isoformat(),
            "main_branch": self.main_branch,
            "total_branches": len(self.branches),
            "summary": {},
            "branches": [asdict(branch) for branch in self.branches]
        }
        
        # Add summary counts
        for branch in self.branches:
            status = branch.status
            if status not in data["summary"]:
                data["summary"][status] = 0
            data["summary"][status] += 1
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Analysis exported to: {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze branch synchronization status against main branch"
    )
    parser.add_argument(
        "--main-branch", 
        default="main", 
        help="Name of the main branch (default: main)"
    )
    parser.add_argument(
        "--json", 
        metavar="FILENAME",
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--summary-only", 
        action="store_true",
        help="Show only summary, not detailed report"
    )
    
    args = parser.parse_args()
    
    checker = BranchSyncChecker(args.main_branch)
    
    try:
        checker.analyze_all_branches()
        checker.print_summary()
        
        if not args.summary_only:
            checker.print_detailed_report()
        
        if args.json:
            checker.export_json(args.json)
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()