# Branch Synchronization Guide

This document explains how to keep all branches in sync with the main branch in the Petty repository.

## Overview

The Petty repository uses automated tools to monitor and help maintain branch synchronization. This ensures that:

- Feature branches don't drift too far from main
- Security updates and bug fixes are propagated to all active branches
- Merge conflicts are minimized when branches are eventually merged
- The development workflow remains smooth and predictable

## Tools Available

### 1. Branch Sync Check Script

The `tools/branch_sync_check.py` script analyzes all remote branches and compares them with main.

**Usage:**
```bash
# Basic status check
python tools/branch_sync_check.py

# Generate sync commands
python tools/branch_sync_check.py --sync-commands

# Output as JSON for automation
python tools/branch_sync_check.py --json
```

### 2. Makefile Targets

Convenient Make targets are available:

```bash
# Check branch status
make branches-status

# Quick summary
make branches-summary

# Get sync commands
make branches-sync-commands

# JSON output
make branches-status-json

# Fetch all remote branches
make branches-fetch

# Bulk sync operations
make branches-bulk-sync-dry     # See what would be synced
make branches-bulk-sync         # Interactive bulk sync
make branches-bulk-sync-auto    # Automatic bulk sync
```

### 3. Automated Monitoring

The `.github/workflows/branch-sync-monitor.yml` workflow:

- Runs daily at 8:00 AM UTC
- Checks all branches against main
- Creates/updates GitHub issues when branches are out of sync
- Can be triggered manually from GitHub Actions

## Branch Status Categories

### ✅ Up to Date
Branches that are exactly in sync with main. No action needed.

### 🔴 Behind Main
Branches that are missing commits from main. These can usually be fast-forwarded.

**Action:** Merge main into the branch
```bash
git checkout <branch-name>
git merge main
git push origin <branch-name>
```

### 🟢 Ahead of Main
Branches with new commits that aren't in main yet. These might be:
- Feature branches ready for merge
- Experimental branches
- Release preparation branches

**Action:** Review if ready to merge to main, or keep as-is if still in development.

### 🟡 Diverged
Branches that are both behind and ahead of main. These require careful merging to resolve potential conflicts.

**Action:** Manual merge with conflict resolution
```bash
git checkout <branch-name>
git merge main  # May require conflict resolution
git push origin <branch-name>
```

## Sync Process

### For Repository Maintainers

1. **Quick Status Check**
   ```bash
   make branches-summary
   ```

2. **Detailed Analysis**
   ```bash
   make branches-status
   ```

3. **Bulk Sync Operations**
   ```bash
   # See what would be synced
   make branches-bulk-sync-dry
   
   # Interactive sync (recommended)
   make branches-bulk-sync
   
   # Automatic sync (use with caution)
   make branches-bulk-sync-auto
   ```

4. **Manual Sync Commands**
   ```bash
   make branches-sync-commands
   ```

3. **Prioritize Syncing:**
   - Critical/security branches first
   - Active feature branches second
   - Experimental/old branches last

4. **Batch Operations**
   For multiple branches behind main:
   ```bash
   # Get the commands
   make branches-sync-commands > sync_commands.sh
   # Review and execute selectively
   ```

### For Branch Owners

If you own a branch that's flagged as out of sync:

1. **For Simple Cases (behind main):**
   ```bash
   git checkout your-branch
   git merge main
   git push origin your-branch
   ```

2. **For Complex Cases (diverged):**
   ```bash
   git checkout your-branch
   git merge main
   # Resolve any conflicts
   git commit
   git push origin your-branch
   ```

3. **Test After Sync:**
   Always test your branch after syncing to ensure functionality wasn't broken.

## Best Practices

### Branch Management

1. **Keep Branches Short-Lived**
   - Merge feature branches quickly to minimize drift
   - Delete branches after merging

2. **Regular Sync**
   - Sync your active branches with main weekly
   - Sync before starting new work on a branch

3. **Clear Naming**
   - Use descriptive branch names
   - Include ticket/issue numbers when applicable

### Automation Integration

1. **CI/CD Consideration**
   - Sync branches before important CI runs
   - Consider branch protection rules for main

2. **Release Management**
   - Ensure release branches are synced before cutting releases
   - Tag synchronized states for rollback capability

## Troubleshooting

### Common Issues

1. **Merge Conflicts**
   ```bash
   # When git merge main fails
   git status  # See conflicted files
   # Edit files to resolve conflicts
   git add .
   git commit
   ```

2. **Large Drifts**
   For branches very far behind:
   ```bash
   # Consider rebasing instead of merging
   git checkout your-branch
   git rebase main
   # Or create a fresh branch from main and cherry-pick changes
   ```

3. **Script Errors**
   ```bash
   # Ensure all remotes are fetched
   git fetch --all
   # Check git repository state
   git status
   ```

### Getting Help

1. **Check workflow logs** in GitHub Actions for automated monitoring
2. **Review GitHub issues** labeled `branch-sync-alert`
3. **Run diagnostics:**
   ```bash
   make branches-status-json | jq '.branches[] | select(.name == "your-branch")'
   ```

## Configuration

### Customizing the Script

Edit `tools/branch_sync_check.py` to:
- Change the main branch name (if not "main")
- Modify output formatting
- Add custom analysis rules

### Adjusting Automation

Edit `.github/workflows/branch-sync-monitor.yml` to:
- Change the schedule frequency
- Modify issue creation rules
- Add notifications to Slack/email

### Makefile Integration

The Makefile can be extended with additional targets:
```makefile
branches-cleanup: ## Delete merged branches
	git branch --merged main | grep -v main | xargs -n 1 git branch -d

branches-stale: ## List stale branches (older than 30 days)
	git for-each-ref --format='%(refname:short) %(committerdate)' refs/remotes/origin | 
	awk '$$2 < "'$$(date -d '30 days ago' -I)'"'
```

## Security Considerations

- Branch sync operations should be done by authorized maintainers
- Review changes before pushing to shared branches
- Use branch protection rules to prevent force-pushes to main
- Consider signing commits for critical sync operations

---

This guide helps maintain a clean, synchronized repository where all branches stay reasonably current with the main development line.