#!/usr/bin/env python3
"""
Branch Synchronization Checker for Petty Repository

This script checks which branches are out of sync with the main branch
and provides recommendations for syncing them.

Usage:
    python tools/branch_sync_check.py [--remote REMOTE] [--main-branch BRANCH]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional


class BranchInfo(NamedTuple):
    """Information about a branch."""
    name: str
    commit_sha: str
    commit_date: str
    commit_message: str
    is_ahead: bool
    is_behind: bool
    ahead_count: int
    behind_count: int


def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return its output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="."
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command {' '.join(cmd)}: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_remote_branches(remote: str = "origin") -> List[str]:
    """Get list of remote branches."""
    output = run_git_command(["git", "branch", "-r", "--format=%(refname:short)"])
    branches = []
    for line in output.split('\n'):
        if line.strip() and not line.endswith('/HEAD'):
            branch = line.strip()
            if branch.startswith(f"{remote}/"):
                branches.append(branch.replace(f"{remote}/", ""))
    return sorted(branches)


def get_branch_info(branch: str, main_branch: str, remote: str = "origin") -> BranchInfo:
    """Get detailed information about a branch relative to main."""
    # Get commit info for the branch
    commit_info = run_git_command([
        "git", "log", f"{remote}/{branch}", "-1", 
        "--format=%H|%ai|%s"
    ])
    commit_sha, commit_date, commit_message = commit_info.split('|', 2)
    
    # Check if branch is ahead/behind main
    try:
        ahead_behind = run_git_command([
            "git", "rev-list", "--left-right", "--count",
            f"{remote}/{main_branch}...{remote}/{branch}"
        ])
        behind_count, ahead_count = map(int, ahead_behind.split())
    except subprocess.CalledProcessError:
        # Branch might not exist or other issue
        behind_count = ahead_count = 0
    
    return BranchInfo(
        name=branch,
        commit_sha=commit_sha,
        commit_date=commit_date,
        commit_message=commit_message,
        is_ahead=ahead_count > 0,
        is_behind=behind_count > 0,
        ahead_count=ahead_count,
        behind_count=behind_count
    )


def format_date(date_str: str) -> str:
    """Format ISO date string for display."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return date_str


def print_branch_status(branches: List[BranchInfo], main_branch: str) -> None:
    """Print formatted branch status."""
    print(f"Branch Synchronization Status (relative to {main_branch})")
    print("=" * 80)
    
    # Categorize branches
    up_to_date = []
    behind_main = []
    ahead_of_main = []
    diverged = []
    
    for branch in branches:
        if branch.name == main_branch:
            continue
            
        if not branch.is_ahead and not branch.is_behind:
            up_to_date.append(branch)
        elif branch.is_behind and not branch.is_ahead:
            behind_main.append(branch)
        elif branch.is_ahead and not branch.is_behind:
            ahead_of_main.append(branch)
        else:
            diverged.append(branch)
    
    # Print summary
    total_branches = len(branches) - 1  # Exclude main branch
    print(f"\nSummary:")
    print(f"  Total branches: {total_branches}")
    print(f"  Up to date: {len(up_to_date)}")
    print(f"  Behind main: {len(behind_main)}")
    print(f"  Ahead of main: {len(ahead_of_main)}")
    print(f"  Diverged: {len(diverged)}")
    
    def print_branch_section(title: str, branch_list: List[BranchInfo]) -> None:
        if not branch_list:
            return
            
        print(f"\n{title}:")
        print("-" * len(title))
        for branch in sorted(branch_list, key=lambda b: b.commit_date, reverse=True):
            status = ""
            if branch.is_behind and branch.is_ahead:
                status = f"↕️  {branch.behind_count} behind, {branch.ahead_count} ahead"
            elif branch.is_behind:
                status = f"⬇️  {branch.behind_count} behind"
            elif branch.is_ahead:
                status = f"⬆️  {branch.ahead_count} ahead"
            else:
                status = "✅ up to date"
            
            print(f"  {branch.name:<40} {status:<20} {format_date(branch.commit_date)}")
            print(f"    {branch.commit_sha[:8]} {branch.commit_message[:60]}")
    
    print_branch_section("🔴 Branches Behind Main (need sync)", behind_main)
    print_branch_section("🟡 Diverged Branches (need manual merge)", diverged)
    print_branch_section("🟢 Branches Ahead of Main", ahead_of_main)
    print_branch_section("✅ Up-to-date Branches", up_to_date)


def generate_sync_commands(branches: List[BranchInfo], main_branch: str) -> None:
    """Generate sync commands for branches that need updating."""
    behind_branches = [b for b in branches if b.is_behind and not b.is_ahead]
    diverged_branches = [b for b in branches if b.is_behind and b.is_ahead]
    
    if not behind_branches and not diverged_branches:
        print("\n🎉 All branches are up to date!")
        return
    
    print(f"\nSync Commands:")
    print("=" * 40)
    
    if behind_branches:
        print("\n# Fast-forward branches (behind main):")
        for branch in behind_branches:
            print(f"git checkout {branch.name}")
            print(f"git merge {main_branch}")
            print(f"git push origin {branch.name}")
            print()
    
    if diverged_branches:
        print("\n# Diverged branches (manual merge required):")
        for branch in diverged_branches:
            print(f"git checkout {branch.name}")
            print(f"git merge {main_branch}  # May need conflict resolution")
            print(f"git push origin {branch.name}")
            print()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check branch synchronization status")
    parser.add_argument(
        "--remote", default="origin", help="Remote name (default: origin)"
    )
    parser.add_argument(
        "--main-branch", default="main", help="Main branch name (default: main)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    parser.add_argument(
        "--sync-commands", action="store_true", 
        help="Generate sync commands for out-of-date branches"
    )
    
    args = parser.parse_args()
    
    # Fetch latest remote data
    print("Fetching latest remote data...", file=sys.stderr)
    run_git_command(["git", "fetch", args.remote])
    
    # Get all remote branches
    remote_branches = get_remote_branches(args.remote)
    
    if not remote_branches:
        print("No remote branches found!", file=sys.stderr)
        sys.exit(1)
    
    # Get branch information
    print(f"Analyzing {len(remote_branches)} branches...", file=sys.stderr)
    branch_infos = []
    for branch in remote_branches:
        try:
            info = get_branch_info(branch, args.main_branch, args.remote)
            branch_infos.append(info)
        except Exception as e:
            print(f"Warning: Could not analyze branch {branch}: {e}", file=sys.stderr)
    
    if args.json:
        # Output as JSON
        output = {
            "main_branch": args.main_branch,
            "remote": args.remote,
            "timestamp": datetime.now().isoformat(),
            "branches": [branch._asdict() for branch in branch_infos]
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print_branch_status(branch_infos, args.main_branch)
        
        if args.sync_commands:
            generate_sync_commands(branch_infos, args.main_branch)


if __name__ == "__main__":
    main()