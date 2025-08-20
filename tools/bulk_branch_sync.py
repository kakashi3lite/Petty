#!/usr/bin/env python3
"""
Bulk Branch Sync Tool

Safely synchronizes multiple branches at once with interactive and automatic modes.
Includes dry-run capability for safety and handles different branch states appropriately.
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class BranchSyncPlan:
    """Represents a plan for synchronizing a branch."""
    name: str
    status: str
    action: str
    safe: bool
    reason: str
    command: List[str]


class BulkBranchSync:
    """Bulk branch synchronization tool."""
    
    def __init__(self, main_branch: str = "main", dry_run: bool = False):
        self.main_branch = main_branch
        self.dry_run = dry_run
        self.original_branch = None
        
    def run_git_command(self, command: List[str], check: bool = True) -> str:
        """Execute a git command and return the output."""
        try:
            if self.dry_run:
                print(f"    [DRY RUN] Would run: {' '.join(command)}")
                return ""
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=check,
                cwd="."
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return ""
    
    def get_current_branch(self) -> str:
        """Get the currently checked out branch."""
        return self.run_git_command(["git", "branch", "--show-current"])
    
    def get_branch_status(self, branch: str) -> Dict[str, any]:
        """Get detailed status of a branch."""
        behind_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{branch}..origin/{self.main_branch}"
        ])
        ahead_output = self.run_git_command([
            "git", "rev-list", "--count", f"origin/{self.main_branch}..origin/{branch}"
        ])
        
        commits_behind = int(behind_output) if behind_output.isdigit() else 0
        commits_ahead = int(ahead_output) if ahead_output.isdigit() else 0
        
        if commits_behind == 0 and commits_ahead == 0:
            status = "up-to-date"
        elif commits_behind > 0 and commits_ahead == 0:
            status = "behind"
        elif commits_behind == 0 and commits_ahead > 0:
            status = "ahead"
        else:
            status = "diverged"
        
        return {
            "status": status,
            "commits_behind": commits_behind,
            "commits_ahead": commits_ahead
        }
    
    def create_sync_plan(self, branches: List[str], include_ahead: bool = False) -> List[BranchSyncPlan]:
        """Create a synchronization plan for the given branches."""
        print("🔍 Analyzing branches and creating sync plan...")
        self.run_git_command(["git", "fetch", "--all", "--prune"])
        
        plans = []
        
        for branch in branches:
            print(f"  📊 Analyzing {branch}...", end="", flush=True)
            
            try:
                status_info = self.get_branch_status(branch)
                status = status_info["status"]
                behind = status_info["commits_behind"]
                ahead = status_info["commits_ahead"]
                
                if status == "up-to-date":
                    plan = BranchSyncPlan(
                        name=branch,
                        status=status,
                        action="skip",
                        safe=True,
                        reason="Already up-to-date",
                        command=[]
                    )
                elif status == "behind":
                    plan = BranchSyncPlan(
                        name=branch,
                        status=status,
                        action="fast-forward",
                        safe=True,
                        reason=f"Can be safely fast-forwarded ({behind} commits behind)",
                        command=[
                            ["git", "checkout", branch],
                            ["git", "merge", f"origin/{self.main_branch}", "--ff-only"]
                        ]
                    )
                elif status == "ahead":
                    if include_ahead:
                        plan = BranchSyncPlan(
                            name=branch,
                            status=status,
                            action="skip",
                            safe=True,
                            reason=f"Ahead of main ({ahead} commits) - consider creating PR",
                            command=[]
                        )
                    else:
                        plan = BranchSyncPlan(
                            name=branch,
                            status=status,
                            action="skip",
                            safe=True,
                            reason=f"Ahead of main ({ahead} commits) - excluded from sync",
                            command=[]
                        )
                else:  # diverged
                    plan = BranchSyncPlan(
                        name=branch,
                        status=status,
                        action="manual-merge",
                        safe=False,
                        reason=f"Diverged ({behind} behind, {ahead} ahead) - needs manual resolution",
                        command=[
                            ["git", "checkout", branch],
                            ["git", "merge", f"origin/{self.main_branch}"]
                        ]
                    )
                
                plans.append(plan)
                print(f" {status}")
                
            except Exception as e:
                print(f" ERROR: {e}")
                plan = BranchSyncPlan(
                    name=branch,
                    status="error",
                    action="skip",
                    safe=False,
                    reason=f"Error analyzing branch: {e}",
                    command=[]
                )
                plans.append(plan)
        
        return plans
    
    def print_sync_plan(self, plans: List[BranchSyncPlan]) -> None:
        """Print the synchronization plan."""
        print(f"\n📋 SYNC PLAN SUMMARY")
        print(f"{'='*60}")
        
        action_counts = {}
        for plan in plans:
            action_counts[plan.action] = action_counts.get(plan.action, 0) + 1
        
        safe_count = sum(1 for plan in plans if plan.safe and plan.action != "skip")
        unsafe_count = sum(1 for plan in plans if not plan.safe and plan.action != "skip")
        skip_count = action_counts.get("skip", 0)
        
        print(f"✅ Safe operations: {safe_count}")
        print(f"⚠️  Requires attention: {unsafe_count}")
        print(f"⏭️  Will skip: {skip_count}")
        
        # Group by action
        by_action = {}
        for plan in plans:
            if plan.action not in by_action:
                by_action[plan.action] = []
            by_action[plan.action].append(plan)
        
        action_emojis = {
            "fast-forward": "⚡",
            "manual-merge": "⚠️",
            "skip": "⏭️",
            "error": "❌"
        }
        
        for action, action_plans in by_action.items():
            if not action_plans:
                continue
            
            emoji = action_emojis.get(action, "📁")
            print(f"\n{emoji} {action.upper().replace('-', ' ')} ({len(action_plans)} branches)")
            print("-" * 50)
            
            for plan in action_plans:
                safety_icon = "🟢" if plan.safe else "🔴"
                print(f"  {safety_icon} {plan.name}")
                print(f"     Status: {plan.status}")
                print(f"     Reason: {plan.reason}")
                if plan.command and not self.dry_run:
                    print(f"     Actions: {len(plan.command)} git commands")
                print()
    
    def confirm_execution(self, plans: List[BranchSyncPlan]) -> bool:
        """Ask user to confirm the execution plan."""
        safe_ops = [p for p in plans if p.safe and p.action != "skip"]
        unsafe_ops = [p for p in plans if not p.safe and p.action != "skip"]
        
        if not safe_ops and not unsafe_ops:
            print("ℹ️  No synchronization operations needed.")
            return False
        
        print(f"\n🤔 CONFIRMATION REQUIRED")
        print(f"{'='*40}")
        
        if safe_ops:
            print(f"✅ {len(safe_ops)} safe operations will be performed")
        
        if unsafe_ops:
            print(f"⚠️  {len(unsafe_ops)} operations require manual attention")
            print(f"   These will be skipped automatically for safety")
        
        if self.dry_run:
            print(f"\n🧪 This is a DRY RUN - no actual changes will be made")
            return True
        
        while True:
            response = input(f"\nProceed with synchronization? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please answer 'y' or 'n'")
    
    def execute_sync_plan(self, plans: List[BranchSyncPlan], interactive: bool = True) -> None:
        """Execute the synchronization plan."""
        if interactive and not self.confirm_execution(plans):
            print("❌ Synchronization cancelled by user")
            return
        
        # Save current branch
        self.original_branch = self.get_current_branch()
        print(f"💾 Current branch: {self.original_branch}")
        
        successful = 0
        failed = 0
        skipped = 0
        
        try:
            for plan in plans:
                if plan.action == "skip" or plan.action == "error":
                    skipped += 1
                    continue
                
                if not plan.safe:
                    print(f"⚠️  Skipping unsafe operation on {plan.name}: {plan.reason}")
                    skipped += 1
                    continue
                
                print(f"\n🔄 Synchronizing {plan.name}...")
                
                try:
                    for i, command in enumerate(plan.command, 1):
                        print(f"  Step {i}/{len(plan.command)}: {' '.join(command[2:])}")  # Skip 'git'
                        result = self.run_git_command(command)
                        if result:
                            print(f"    Output: {result}")
                    
                    successful += 1
                    print(f"  ✅ {plan.name} synchronized successfully")
                    
                except subprocess.CalledProcessError as e:
                    failed += 1
                    print(f"  ❌ Failed to sync {plan.name}: {e}")
                    print(f"     You may need to resolve conflicts manually")
                    
                    # Try to return to a clean state
                    try:
                        self.run_git_command(["git", "merge", "--abort"], check=False)
                        self.run_git_command(["git", "reset", "--hard", "HEAD"], check=False)
                    except:
                        pass
                
                time.sleep(0.5)  # Brief pause between operations
            
        finally:
            # Return to original branch
            if self.original_branch and not self.dry_run:
                try:
                    print(f"\n🔙 Returning to original branch: {self.original_branch}")
                    self.run_git_command(["git", "checkout", self.original_branch])
                except:
                    print(f"⚠️  Could not return to {self.original_branch}")
        
        # Print summary
        print(f"\n📊 SYNC RESULTS")
        print(f"{'='*40}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        
        if failed > 0:
            print(f"\n💡 For failed syncs, consider:")
            print(f"   1. Manual merge resolution")
            print(f"   2. Using git merge tools")
            print(f"   3. Consulting with branch authors")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk synchronization of branches with main"
    )
    parser.add_argument(
        "branches",
        nargs="*",
        help="Specific branches to sync (default: all remote branches)"
    )
    parser.add_argument(
        "--main-branch", 
        default="main", 
        help="Name of the main branch (default: main)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--auto", 
        action="store_true",
        help="Non-interactive mode (skip confirmation)"
    )
    parser.add_argument(
        "--include-ahead", 
        action="store_true",
        help="Include branches that are ahead of main (normally skipped)"
    )
    parser.add_argument(
        "--behind-only", 
        action="store_true",
        help="Only sync branches that are behind main (safe fast-forward)"
    )
    
    args = parser.parse_args()
    
    sync_tool = BulkBranchSync(args.main_branch, args.dry_run)
    
    try:
        # Get branches to sync
        if args.branches:
            branches = args.branches
            print(f"🎯 Targeting specific branches: {', '.join(branches)}")
        else:
            print("🔍 Discovering all remote branches...")
            all_output = sync_tool.run_git_command(["git", "branch", "-r"])
            branches = []
            for line in all_output.split('\n'):
                line = line.strip()
                if line and line.startswith('origin/') and not line.endswith(f'origin/{args.main_branch}'):
                    branch_name = line.replace('origin/', '')
                    if branch_name != args.main_branch:
                        branches.append(branch_name)
            print(f"📁 Found {len(branches)} branches to analyze")
        
        if not branches:
            print("ℹ️  No branches found to synchronize")
            return
        
        # Create and execute sync plan
        plans = sync_tool.create_sync_plan(branches, args.include_ahead)
        
        # Filter for behind-only if requested
        if args.behind_only:
            plans = [p for p in plans if p.status == "behind" or p.action == "skip"]
            print(f"🎯 Filtered to behind-only: {len([p for p in plans if p.action != 'skip'])} branches")
        
        sync_tool.print_sync_plan(plans)
        sync_tool.execute_sync_plan(plans, not args.auto)
        
    except KeyboardInterrupt:
        print("\n❌ Bulk sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during bulk sync: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()