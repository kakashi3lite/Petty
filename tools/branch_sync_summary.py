#!/usr/bin/env python3
"""
Quick Branch Sync Summary

Provides a concise summary of branch synchronization status.
"""

import subprocess
import sys
import json
from datetime import datetime


def run_git_command(cmd):
    """Run a git command and return its output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd="."
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function."""
    print("🔍 Branch Sync Quick Summary")
    print("=" * 40)
    
    try:
        # Get branch status JSON
        result = subprocess.run(
            ["python", "tools/branch_sync_check.py", "--json"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        
        branches = data.get("branches", [])
        main_branch = data.get("main_branch", "main")
        
        # Calculate summary stats
        total = len([b for b in branches if b["name"] != main_branch])
        behind = len([b for b in branches if b["is_behind"] and not b["is_ahead"]])
        ahead = len([b for b in branches if b["is_ahead"] and not b["is_behind"]])
        diverged = len([b for b in branches if b["is_behind"] and b["is_ahead"]])
        up_to_date = total - behind - ahead - diverged
        
        print(f"📊 Total branches: {total}")
        print(f"✅ Up to date: {up_to_date}")
        print(f"🔴 Behind main: {behind}")
        print(f"🟢 Ahead of main: {ahead}")
        print(f"🟡 Diverged: {diverged}")
        print()
        
        # Action needed?
        action_needed = behind + diverged
        if action_needed > 0:
            print(f"⚠️  {action_needed} branches need attention!")
            print("   Run 'make branches-status' for details")
            print("   Run 'make branches-sync-commands' for sync instructions")
        else:
            print("🎉 All branches are in sync!")
        
        print()
        print(f"📅 Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Exit code indicates if action is needed
        sys.exit(1 if action_needed > 0 else 0)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running branch sync check: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing branch sync output: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()