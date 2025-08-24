#!/usr/bin/env python3
"""
Branch Sync Summary Tool

Provides a quick overview of branch synchronization status.
Perfect for daily maintainer checks and CI/CD integration.
"""

import argparse
import subprocess
import sys
from collections import Counter
from typing import Dict, List


class BranchSyncSummary:
    """Quick branch synchronization summary tool."""
    
    def __init__(self, main_branch: str = "main"):
        self.main_branch = main_branch
    
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
        except subprocess.CalledProcessError:
            return ""
    
    def get_branch_status_quick(self, branch: str) -> str:
        """Quickly determine branch status without detailed analysis."""
        # Get commit counts
        behind_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{branch}..origin/{self.main_branch}"
        ])
        ahead_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{self.main_branch}..origin/{branch}"
        ])
        
        commits_behind = int(behind_output) if behind_output.isdigit() else 0
        commits_ahead = int(ahead_output) if ahead_output.isdigit() else 0
        
        if commits_behind == 0 and commits_ahead == 0:
            return "up-to-date"
        elif commits_behind > 0 and commits_ahead == 0:
            return "behind"
        elif commits_behind == 0 and commits_ahead > 0:
            return "ahead"
        else:
            return "diverged"
    
    def get_remote_branches(self) -> List[str]:
        """Get list of all remote branches except main."""
        all_output = self.run_git_command(["git", "branch", "-r"])
        branches = []
        
        for line in all_output.split('\n'):
            line = line.strip()
            if line and line.startswith('origin/') and not line.endswith(f'origin/{self.main_branch}'):
                branch_name = line.replace('origin/', '')
                if branch_name != self.main_branch:
                    branches.append(branch_name)
        return sorted(set(branches))
    
    def generate_summary(self) -> Dict[str, int]:
        """Generate a quick summary of branch statuses."""
        print("🔄 Fetching latest remote information...")
        self.run_git_command(["git", "fetch", "--all", "--prune", "--quiet"])
        
        branches = self.get_remote_branches()
        print(f"⚡ Quick analysis of {len(branches)} branches...")
        
        status_counts = Counter()
        
        for i, branch in enumerate(branches, 1):
            if i % 10 == 0 or i == len(branches):
                print(f"  Progress: {i}/{len(branches)}", end="\r", flush=True)
            
            status = self.get_branch_status_quick(branch)
            status_counts[status] += 1
        
        print()  # Clear progress line
        return dict(status_counts)
    
    def print_summary(self, status_counts: Dict[str, int], show_details: bool = False) -> None:
        """Print the branch synchronization summary."""
        total = sum(status_counts.values())
        needs_attention = sum(
            count for status, count in status_counts.items() 
            if status != "up-to-date"
        )
        
        print(f"\n📊 BRANCH SYNC SUMMARY")
        print(f"{'='*40}")
        print(f"📁 Total branches: {total}")
        print(f"⚠️  Need attention: {needs_attention}")
        print(f"✅ Up to date: {status_counts.get('up-to-date', 0)}")
        print()
        
        # Status breakdown
        status_emojis = {
            "behind": "🔴",
            "ahead": "🟡", 
            "diverged": "🟠",
            "up-to-date": "🟢"
        }
        
        status_labels = {
            "behind": "Behind (can fast-forward)",
            "ahead": "Ahead (ready for review)",
            "diverged": "Diverged (needs manual merge)",
            "up-to-date": "Up to date"
        }
        
        for status in ["behind", "diverged", "ahead", "up-to-date"]:
            count = status_counts.get(status, 0)
            if count > 0 or show_details:
                emoji = status_emojis.get(status, "⚪")
                label = status_labels.get(status, status)
                print(f"{emoji} {label:<30} {count:>3}")
        
        # Action recommendations
        print(f"\n💡 QUICK ACTIONS")
        print(f"{'='*40}")
        
        if status_counts.get("behind", 0) > 0:
            print(f"🔄 Fast-forward {status_counts['behind']} behind branches:")
            print(f"   make branches-bulk-sync-behind")
        
        if status_counts.get("diverged", 0) > 0:
            print(f"⚠️  Review {status_counts['diverged']} diverged branches manually")
        
        if status_counts.get("ahead", 0) > 0:
            print(f"🔍 Consider PRs for {status_counts['ahead']} ahead branches")
        
        if needs_attention == 0:
            print(f"🎉 All branches are synchronized! Great job!")
        
        print(f"\n🔧 DETAILED ANALYSIS")
        print(f"{'='*40}")
        print(f"📋 Full report: make branches-check")
        print(f"📄 Export JSON:  make branches-check-json")
        print(f"🔄 Bulk sync:    make branches-bulk-sync")
    
    def print_health_score(self, status_counts: Dict[str, int]) -> None:
        """Print a health score for the repository."""
        total = sum(status_counts.values())
        if total == 0:
            return
        
        up_to_date = status_counts.get("up-to-date", 0)
        health_percentage = (up_to_date / total) * 100
        
        print(f"\n🏥 REPOSITORY HEALTH")
        print(f"{'='*40}")
        
        if health_percentage >= 90:
            emoji = "🟢"
            status = "EXCELLENT"
        elif health_percentage >= 75:
            emoji = "🟡" 
            status = "GOOD"
        elif health_percentage >= 50:
            emoji = "🟠"
            status = "NEEDS ATTENTION"
        else:
            emoji = "🔴"
            status = "CRITICAL"
        
        print(f"{emoji} Health Score: {health_percentage:.1f}% ({status})")
        print(f"   {up_to_date}/{total} branches are synchronized")
        
        if health_percentage < 75:
            print(f"\n💊 Recommended actions:")
            print(f"   1. Run daily branch sync checks")
            print(f"   2. Consider branch cleanup for stale branches")
            print(f"   3. Implement automated sync policies")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Quick branch synchronization summary"
    )
    parser.add_argument(
        "--main-branch", 
        default="main", 
        help="Name of the main branch (default: main)"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed breakdown including zero counts"
    )
    parser.add_argument(
        "--health", 
        action="store_true",
        help="Show repository health score"
    )
    
    args = parser.parse_args()
    
    summary = BranchSyncSummary(args.main_branch)
    
    try:
        status_counts = summary.generate_summary()
        summary.print_summary(status_counts, args.detailed)
        
        if args.health:
            summary.print_health_score(status_counts)
        
    except KeyboardInterrupt:
        print("\n❌ Summary interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating summary: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()