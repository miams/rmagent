# Git Workflow Guide - RMAgent

## Overview

RMAgent uses a **gitflow** workflow to manage development. This guide will walk you through the daily workflow, from starting a new feature to merging it into production.

## Branch Structure

```
main              Production-ready code (protected)
  ↑
  PR (merge commit)
  |
develop           Integration branch (default)
  ↑
  PR (squash merge)
  |
feature/*         Individual features
```

### Branches Explained

- **main**: Production-ready code only. Protected - no direct commits allowed.
- **develop**: Default working branch. All features merge here first.
- **feature/**: Individual features. Branch from develop, PR back to develop.

## Daily Workflow

### 1. Starting a New Feature

Always start from an up-to-date `develop` branch:

```bash
# Make sure you're on develop
git checkout develop

# Get latest changes
git pull origin develop

# Create a new feature branch
git checkout -b feature/my-feature-name

# Push the branch to GitHub
git push -u origin feature/my-feature-name
```

**Branch Naming Convention**: `feature/description-with-dashes`

Examples:
- `feature/census-extraction`
- `feature/add-source-validation`
- `feature/fix-date-parsing`

### 2. Working on Your Feature

Make commits as you normally would:

```bash
# Make changes to your files
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add census extraction parser"

# Push to GitHub
git push
```

**Commit Message Convention**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 3. Creating a Pull Request

When your feature is ready:

```bash
# Make sure all changes are committed and pushed
git status
git push

# Create PR using GitHub CLI
gh pr create --base develop --title "feat: add census extraction" --body "Description of changes"
```

Or create the PR through GitHub web interface.

**PR Checklist**:
- [ ] All tests pass locally (`uv run pytest`)
- [ ] Code is formatted (`uv run black .`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Changes are documented (if needed)

### 4. Merging Your PR

Once tests pass on GitHub Actions:

```bash
# Merge using GitHub CLI (squash merge)
gh pr merge --squash --delete-branch

# Or use GitHub web interface with "Squash and merge" button
```

Then update your local develop:

```bash
git checkout develop
git pull origin develop
```

### 5. Releasing to Main (Milestone Complete)

When you've completed a milestone from AI_AGENT_TODO.md:

```bash
# Make sure develop is up to date
git checkout develop
git pull origin develop

# Create PR to main
gh pr create --base main --title "Release: Milestone X Complete" --body "Summary of changes"

# Review and merge with "Create a merge commit" (not squash)
gh pr merge --merge
```

## Common Scenarios

### Switching Between Features

```bash
# Save your current work
git add .
git commit -m "wip: partial implementation"
git push

# Switch to different feature
git checkout feature/other-feature

# Or start a new one
git checkout develop
git pull
git checkout -b feature/new-feature
```

### Updating Feature Branch with Latest Develop

If develop has new changes you need:

```bash
# On your feature branch
git checkout feature/my-feature

# Get latest develop
git fetch origin develop

# Merge develop into your feature
git merge origin/develop

# Resolve any conflicts, then push
git push
```

### Abandoning a Feature

```bash
# Switch back to develop
git checkout develop

# Delete local branch
git branch -D feature/unwanted-feature

# Delete remote branch
git push origin --delete feature/unwanted-feature
```

### Fixing a Mistake in Your Last Commit

```bash
# Make the fix
git add .

# Amend the last commit
git commit --amend --no-edit

# Force push (only safe on feature branches!)
git push --force
```

## GitHub Actions CI/CD

Every PR automatically runs:
1. **Linting** - `ruff check` and `black --check`
2. **Tests** - Full test suite with coverage
3. **Coverage Check** - Must maintain 80%+ coverage

**If tests fail**:
1. Check the Actions tab on GitHub for error details
2. Fix the issues locally
3. Push the fixes (CI runs again automatically)

```bash
# Run the same checks locally before pushing
uv run black .
uv run ruff check .
uv run pytest --cov=rmagent --cov-fail-under=80
```

## Cheat Sheet

### Quick Commands

```bash
# Start new feature
git checkout develop && git pull && git checkout -b feature/name

# Save and push work
git add . && git commit -m "message" && git push

# Create PR to develop
gh pr create --base develop

# Merge PR and update local
gh pr merge --squash --delete-branch && git checkout develop && git pull

# Check status
git status
git log --oneline -10
git branch -a
```

### Useful Git Commands

```bash
# See what changed
git diff                    # Uncommitted changes
git diff --staged          # Staged changes
git log --oneline -10      # Recent commits

# Undo changes
git checkout -- file.py    # Discard changes to file
git reset HEAD file.py     # Unstage file
git reset --soft HEAD~1    # Undo last commit (keep changes)

# Branch info
git branch -a              # List all branches
git branch -vv             # Show tracking info
git remote -v              # Show remotes
```

## Troubleshooting

### "Your branch is behind origin/develop"

```bash
git pull origin develop
```

### "Your branch has diverged from origin/develop"

```bash
git fetch origin
git rebase origin/develop
git push --force
```

### "Merge conflict"

1. Git will mark conflicts in files with `<<<<<<<` markers
2. Edit files to resolve conflicts (remove markers, keep desired code)
3. Stage resolved files: `git add file.py`
4. Complete merge: `git commit` (or `git rebase --continue` if rebasing)
5. Push: `git push`

### PR Tests Failing

```bash
# Run tests locally to debug
uv run pytest -v

# Check specific test
uv run pytest tests/unit/test_file.py::test_name -v

# Run with more output
uv run pytest -vv -s
```

### Need Help?

- Check git status: `git status`
- View recent history: `git log --oneline --graph --all -10`
- See what branch you're on: `git branch`
- GitHub CLI help: `gh pr --help`

## Best Practices

1. **Keep features small** - Easier to review and merge
2. **Commit often** - Small, logical commits are better than large ones
3. **Write good commit messages** - Future you will thank you
4. **Pull before push** - Stay up to date with develop
5. **Test before PR** - Don't rely on CI to catch basic issues
6. **One feature per branch** - Don't mix unrelated changes
7. **Delete merged branches** - Keep your branch list clean

## Resources

- [Understanding Git Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Gitflow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
