# Branch Synchronization Guide

This guide provides comprehensive documentation for managing branch synchronization in the Petty repository using the automated tools and workflows.

## 🎯 Overview

The Petty repository includes a complete toolset for ensuring all branches stay synchronized with the main branch. This prevents merge conflicts, maintains a clean repository structure, and helps maintainers stay on top of branch management.

### Key Benefits

- **Automated Monitoring**: Daily checks for branch synchronization status
- **Bulk Operations**: Safely sync multiple branches at once
- **Safety First**: Dry-run capabilities and interactive confirmations
- **Clear Reporting**: Detailed analysis with actionable recommendations
- **GitHub Integration**: Automatic issue creation for branches needing attention

## 🔧 Available Tools

### 1. Branch Sync Summary (`tools/branch_sync_summary.py`)

**Purpose**: Quick daily overview of branch synchronization status

**Usage**:
```bash
# Quick summary
python3 tools/branch_sync_summary.py

# Include health score
python3 tools/branch_sync_summary.py --health

# Show detailed breakdown (including zero counts)
python3 tools/branch_sync_summary.py --detailed
```

**Output**: Provides instant overview of how many branches need attention, categorized by status.

### 2. Branch Sync Analysis (`tools/branch_sync_check.py`)

**Purpose**: Comprehensive analysis of all branches with detailed sync commands

**Usage**:
```bash
# Full analysis
python3 tools/branch_sync_check.py

# Export to JSON
python3 tools/branch_sync_check.py --json report.json

# Summary only (no detailed report)
python3 tools/branch_sync_check.py --summary-only
```

**Output**: Detailed report showing:
- Branch status (behind, ahead, diverged, up-to-date)
- Commit counts and last commit info
- Specific sync commands for each branch
- JSON export for automation

### 3. Bulk Branch Sync (`tools/bulk_branch_sync.py`)

**Purpose**: Safely synchronize multiple branches with interactive and automatic modes

**Usage**:
```bash
# Interactive bulk sync (recommended)
python3 tools/bulk_branch_sync.py

# Dry run (preview only)
python3 tools/bulk_branch_sync.py --dry-run

# Automatic mode (no confirmation)
python3 tools/bulk_branch_sync.py --auto

# Only sync branches that are behind (safest)
python3 tools/bulk_branch_sync.py --behind-only --auto

# Sync specific branches
python3 tools/bulk_branch_sync.py branch1 branch2 branch3
```

**Safety Features**:
- Dry-run mode shows what would be done without making changes
- Interactive confirmation before executing operations
- Automatically skips unsafe operations (diverged branches)
- Returns to original branch after completion
- Handles errors gracefully with rollback

## 📋 Makefile Targets

The repository includes convenient Makefile targets for common operations:

### Quick Operations
```bash
# Daily quick check
make branches-summary

# Health score included
make branches-summary-health

# Detailed analysis
make branches-check

# Export analysis to JSON
make branches-check-json
```

### Bulk Sync Operations
```bash
# Preview bulk sync (dry run)
make branches-bulk-sync-dry

# Interactive bulk sync
make branches-bulk-sync

# Automatic sync of behind branches (safest)
make branches-bulk-sync-behind

# Automatic bulk sync (use with caution)
make branches-bulk-sync-auto
```

## 🤖 GitHub Actions Automation

### Branch Sync Monitor Workflow

**File**: `.github/workflows/branch-sync-monitor.yml`

**Schedule**: Daily at 8:00 AM UTC

**Features**:
- Analyzes all branches automatically
- Creates/updates GitHub issues for branches needing attention
- Provides detailed reports with sync commands
- Uploads analysis artifacts for review
- Can be triggered manually

**Manual Trigger**:
```bash
# Via GitHub UI: Actions -> Branch Sync Monitor -> Run workflow
# Or via CLI:
gh workflow run branch-sync-monitor.yml
```

### Issue Management

The workflow automatically:
1. **Creates issues** when branches need attention
2. **Updates existing issues** instead of creating duplicates
3. **Labels issues** with `branch-sync` and `maintenance`
4. **Provides detailed sync commands** in issue descriptions

## 📊 Understanding Branch States

### 🟢 Up-to-date
- **Meaning**: Branch is synchronized with main
- **Action**: None needed
- **Command**: `# No action needed`

### 🔴 Behind  
- **Meaning**: Branch is missing commits from main, but has no new commits
- **Action**: Safe to fast-forward
- **Command**: `git checkout <branch> && git merge origin/main --ff-only`
- **Safety**: ✅ Very safe, no conflicts possible

### 🟡 Ahead
- **Meaning**: Branch has new commits that main doesn't have
- **Action**: Consider creating a Pull Request
- **Command**: `# Review and consider creating PR`
- **Safety**: ✅ Safe to leave as-is or create PR

### 🟠 Diverged
- **Meaning**: Branch has both missing commits from main AND new commits
- **Action**: Manual merge required, may have conflicts
- **Command**: `git checkout <branch> && git merge origin/main`
- **Safety**: ⚠️ Requires manual attention, conflicts possible

## 🚀 Daily Workflows

### For Maintainers

**Morning Routine**:
```bash
# 1. Quick health check
make branches-summary-health

# 2. If issues found, get details
make branches-check

# 3. Safe bulk sync of behind branches
make branches-bulk-sync-behind

# 4. Review diverged branches individually
# (Check GitHub issues created by automation)
```

### For Contributors

**Before Starting Work**:
```bash
# 1. Check if your branch needs sync
python3 tools/branch_sync_check.py | grep your-branch-name

# 2. If behind, sync safely
git checkout your-branch-name
git merge origin/main --ff-only

# 3. If diverged, merge carefully
git checkout your-branch-name
git merge origin/main
# Resolve any conflicts
```

## 🔒 Security Considerations

### Safe Operations
- **Behind branches**: Always safe to fast-forward
- **Ahead branches**: Safe to leave as-is or create PRs
- **Up-to-date branches**: No action needed

### Caution Required
- **Diverged branches**: May have conflicts
- **Bulk operations**: Always use dry-run first
- **Force operations**: Never use --force in sync scripts

### Best Practices
1. **Always fetch first**: `git fetch --all --prune`
2. **Use dry-run**: Test bulk operations before executing
3. **Review diverged branches manually**: Don't auto-merge conflicted branches
4. **Backup important branches**: Create backup branches for experimental work
5. **Communicate**: Coordinate with branch authors before major syncs

## 🛠️ Troubleshooting

### Common Issues

**Script fails with permission denied**:
```bash
chmod +x tools/branch_sync_*.py tools/bulk_branch_sync.py
```

**Git commands fail**:
```bash
# Ensure you're in the repository root
cd /path/to/petty

# Ensure git remotes are properly configured
git remote -v
git fetch --all
```

**Python import errors**:
```bash
# Ensure Python 3.11+ is installed
python3 --version

# Scripts use only standard library, no external dependencies needed
```

### Recovery Procedures

**If bulk sync gets interrupted**:
```bash
# Check current state
git status

# If in middle of merge
git merge --abort  # or resolve conflicts and commit

# Return to main branch
git checkout main

# Re-run with dry-run to assess
make branches-bulk-sync-dry
```

**If branch gets corrupted**:
```bash
# Reset to last known good state
git checkout <branch-name>
git reset --hard origin/<branch-name>

# Or if that's problematic, create fresh branch
git checkout -b <branch-name>-backup origin/<branch-name>
```

## 📈 Monitoring and Metrics

### Health Metrics

The system tracks:
- **Total branches**: Overall count of remote branches
- **Synchronization percentage**: How many branches are up-to-date
- **Attention needed**: Count of branches requiring action
- **Historical trends**: Via GitHub Issues and workflow runs

### Health Score Interpretation

- **90-100%**: 🟢 Excellent - Most branches synchronized
- **75-89%**: 🟡 Good - Some cleanup needed
- **50-74%**: 🟠 Needs Attention - Regular maintenance required  
- **<50%**: 🔴 Critical - Immediate action required

### Automated Reporting

- **Daily GitHub Issues**: Automatic creation for branches needing attention
- **Workflow Artifacts**: JSON reports stored for 30 days
- **Summary Comments**: In workflow run summaries

## 🔄 Advanced Usage

### Custom Branch Filtering

**Sync specific branch patterns**:
```bash
# Sync all feature branches
git branch -r | grep 'origin/feature' | sed 's/origin\///' | xargs python3 tools/bulk_branch_sync.py

# Sync all branches by specific author
git for-each-ref --format='%(refname:short) %(authorname)' refs/remotes/origin | grep "John Doe" | cut -d' ' -f1 | sed 's/origin\///' | xargs python3 tools/bulk_branch_sync.py
```

### Integration with CI/CD

**Add to existing workflows**:
```yaml
- name: Check branch sync before deployment
  run: |
    BEHIND_COUNT=$(python3 tools/branch_sync_summary.py | grep "Behind" | grep -o '[0-9]\+' || echo "0")
    if [ "$BEHIND_COUNT" -gt 5 ]; then
      echo "Warning: $BEHIND_COUNT branches are behind main"
      exit 1
    fi
```

### Scheduling Variations

**Different schedule options**:
```yaml
# Weekly on Mondays
- cron: '0 8 * * 1'

# Twice daily
- cron: '0 8,20 * * *'

# Working days only
- cron: '0 8 * * 1-5'
```

## 📚 Reference

### Command Reference

| Command | Purpose | Safety |
|---------|---------|--------|
| `make branches-summary` | Quick daily check | ✅ Safe |
| `make branches-check` | Detailed analysis | ✅ Safe |
| `make branches-bulk-sync-dry` | Preview operations | ✅ Safe |
| `make branches-bulk-sync-behind` | Sync behind branches | ✅ Safe |
| `make branches-bulk-sync` | Interactive bulk sync | ⚠️ Caution |
| `make branches-bulk-sync-auto` | Automatic bulk sync | ⚠️ Caution |

### File Locations

| File | Purpose |
|------|---------|
| `tools/branch_sync_summary.py` | Quick summary tool |
| `tools/branch_sync_check.py` | Detailed analysis tool |
| `tools/bulk_branch_sync.py` | Bulk synchronization tool |
| `.github/workflows/branch-sync-monitor.yml` | Automation workflow |
| `docs/BRANCH_SYNC_GUIDE.md` | This documentation |

## 🤝 Contributing

### Improving the Tools

1. **Fork the repository**
2. **Create a feature branch** for your improvements
3. **Test thoroughly** with dry-run modes
4. **Update documentation** if needed
5. **Submit a Pull Request**

### Reporting Issues

Please include:
- **Tool version/commit hash**
- **Command that failed**
- **Error message**
- **Git status output**
- **Repository state** (number of branches, etc.)

---

## 📞 Support

For questions or issues with branch synchronization:

1. **Check this guide** first
2. **Review existing GitHub Issues** labeled `branch-sync`
3. **Run diagnostic commands**:
   ```bash
   make branches-summary
   git status
   git remote -v
   ```
4. **Create a new issue** with diagnostic output

**Remember**: The goal is to keep all branches synchronized with main while maintaining safety and avoiding data loss. When in doubt, use dry-run mode and ask for help!