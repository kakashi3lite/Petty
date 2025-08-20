#!/usr/bin/env python3
"""
Bulk Branch Sync Helper

Helps automate the syncing of multiple branches with main.
Only handles simple cases (branches behind main, not diverged).
"""

import argparse
import json
import subprocess
import sys
from typing import List, NamedTuple


class BranchSyncResult(NamedTuple):
    """Result of a branch sync operation."""
    branch: str
    success: bool
    message: str


def run_git_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=check, cwd="."
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def get_branches_behind_main() -> List[str]:
    """Get list of branches that are only behind main (not diverged)."""
    try:
        result = subprocess.run(
            ["python", "tools/branch_sync_check.py", "--json"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        
        behind_branches = []
        for branch in data.get("branches", []):
            if branch["is_behind"] and not branch["is_ahead"] and branch["name"] != "main":
                behind_branches.append(branch["name"])
        
        return behind_branches
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error getting branch status: {e}", file=sys.stderr)
        return []


def sync_branch(branch: str, dry_run: bool = False) -> BranchSyncResult:
    """Sync a single branch with main."""
    if dry_run:
        return BranchSyncResult(branch, True, "DRY RUN: Would sync with main")
    
    try:
        # Checkout the branch
        result = run_git_command(["git", "checkout", branch])
        if result.returncode != 0:
            return BranchSyncResult(branch, False, f"Failed to checkout: {result.stderr}")
        
        # Merge main
        result = run_git_command(["git", "merge", "main"], check=False)
        if result.returncode != 0:
            # Attempt to abort the merge
            run_git_command(["git", "merge", "--abort"], check=False)
            return BranchSyncResult(branch, False, f"Merge conflict: {result.stderr}")
        
        # Push the updated branch
        result = run_git_command(["git", "push", "origin", branch], check=False)
        if result.returncode != 0:
            return BranchSyncResult(branch, False, f"Failed to push: {result.stderr}")
        
        return BranchSyncResult(branch, True, "Successfully synced with main")
        
    except Exception as e:
        return BranchSyncResult(branch, False, f"Unexpected error: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bulk sync branches with main")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--branches", nargs="*",
        help="Specific branches to sync (default: all branches behind main)"
    )
    parser.add_argument(
        "--max-branches", type=int, default=10,
        help="Maximum number of branches to process at once (default: 10)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Ask for confirmation before syncing each branch"
    )
    
    args = parser.parse_args()
    
    if args.branches:
        branches_to_sync = args.branches
    else:
        print("🔍 Finding branches behind main...")
        branches_to_sync = get_branches_behind_main()
    
    if not branches_to_sync:
        print("✅ No branches need syncing!")
        return
    
    # Limit the number of branches
    if len(branches_to_sync) > args.max_branches:
        print(f"⚠️  Found {len(branches_to_sync)} branches, limiting to {args.max_branches}")
        print("   Use --max-branches to increase this limit")
        branches_to_sync = branches_to_sync[:args.max_branches]
    
    print(f"📋 Branches to sync: {', '.join(branches_to_sync)}")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    # Store current branch to restore later
    try:
        current_branch = run_git_command(["git", "branch", "--show-current"]).stdout.strip()
    except:
        current_branch = None
    
    results = []
    
    for i, branch in enumerate(branches_to_sync, 1):
        print(f"[{i}/{len(branches_to_sync)}] Processing: {branch}")
        
        if args.interactive and not args.dry_run:
            response = input(f"  Sync {branch} with main? [y/N/q]: ").strip().lower()
            if response == 'q':
                print("  Quitting...")
                break
            elif response != 'y':
                print("  Skipped")
                continue
        
        result = sync_branch(branch, dry_run=args.dry_run)
        results.append(result)
        
        if result.success:
            print(f"  ✅ {result.message}")
        else:
            print(f"  ❌ {result.message}")
        print()
    
    # Restore original branch
    if current_branch and not args.dry_run:
        try:
            run_git_command(["git", "checkout", current_branch])
        except:
            print(f"⚠️  Could not restore original branch: {current_branch}")
    
    # Summary
    print("=" * 50)
    print("📊 Summary:")
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"  ✅ Successful: {len(successful)}")
    print(f"  ❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ Failed branches:")
        for result in failed:
            print(f"  - {result.branch}: {result.message}")
        print("\nFor failed branches, try manual sync:")
        print("  make branches-sync-commands")
    
    if successful and not args.dry_run:
        print(f"\n🎉 Successfully synced {len(successful)} branches!")
    
    # Exit with error if any failures
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()