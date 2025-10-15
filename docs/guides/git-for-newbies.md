# Git for Newbies - RMAgent Collaboration Guide

A practical guide to git collaboration for developers new to the RMAgent project.

## Table of Contents

- [git pull vs git fetch](#git-pull-vs-git-fetch)
- [Feature Branch Relationships](#feature-branch-relationships)
- [Multi-Developer Sync Strategy](#multi-developer-sync-strategy)
- [Common Scenarios](#common-scenarios)
- [Quick Reference](#quick-reference)

---

## git pull vs git fetch

### `git pull` (Recommended for Most Work)

```bash
git pull
# Equivalent to:
# git fetch origin <current-branch>
# git merge origin/<current-branch>
```

**What it does:**
- Fetches updates from remote for **current branch only**
- Automatically merges them into your local branch
- Fast and focused on what you're working on

**When to use:**
- Daily work on feature branches
- Updating develop before creating new features
- Most common operation (95% of the time)

**Example:**
```bash
git checkout develop
git pull                    # Get latest develop
git checkout -b feature/my-feature
# ... work on your feature ...
```

---

### `git fetch --all --tags` (Comprehensive Sync)

```bash
git fetch --all --tags
```

**What it does:**
- `--all`: Fetches from **all remotes** (origin, upstream, etc.)
- `--tags`: Fetches all tag information
- **Does NOT merge** - only updates your local cache of remote state

**When to use:**
- After being away from project for a while
- Want to see all branch activity without merging
- Need tag information (releases, versions)
- Working with multiple remotes (forks, upstreams)

**Example:**
```bash
git fetch --all --tags
git branch -r               # View all remote branches
git tag -l                  # View all tags
git log --all --graph       # Visualize repository state
```

---

## Feature Branch Relationships

### Understanding Branch Independence

**Key concept:** Feature branches are **NOT sub-branches** of develop. They are independent branches that **start from** develop and **merge back to** develop.

### Creating a Feature Branch

```bash
git checkout develop
git pull                              # Get latest develop
git checkout -b feature/my-feature    # Create new branch FROM develop
```

**What happens:**
- Git creates a new branch pointer at the **same commit** as develop
- The branches are now independent - neither is a "parent" or "child"
- They're like two roads that split from the same point

**Visual:**
```
main:     A---B---C
               \
develop:        D---E---F
                     \
feature/x:            G---H---I
```

At the moment you create `feature/x`, both `feature/x` and `develop` point to commit `F`. Then as you work, `feature/x` adds commits `G`, `H`, `I`.

---

### Feature Branch Diverges from Develop

While you're working on `feature/x`, other developers might merge features into develop:

```
main:     A---B---C
               \
develop:        D---E---F---J---K    (other features merged)
                     \
feature/x:            G---H---I      (your feature)
```

Now `feature/x` and `develop` have **diverged** - they're completely independent branches with different commits.

---

### Merging Feature Back to Develop

When your feature is done, you create a PR to merge it back:

```bash
gh pr create --base develop --head feature/x
gh pr merge --squash
```

**What happens with squash merge:**
```
main:     A---B---C
               \
develop:        D---E---F---J---K---L
                     \               ↑
feature/x:            G---H---I -----┘
                                (squashed into L)
```

Commits `G`, `H`, `I` get "squashed" into a single commit `L` on develop.

---

### Eventually Develop Merges to Main

When a milestone is complete:

```bash
gh pr create --base main --head develop
gh pr merge --merge  # Merge commit, NOT squash
```

**Result:**
```
main:     A---B---C-----------M
               \             /
develop:        D---E---F---J---K---L
```

Commit `M` is a **merge commit** that brings all of develop's changes into main.

---

## Multi-Developer Sync Strategy

### Sync Frequency Based on Activity

| Primary Dev Activity | Other Devs Should Pull | Reason |
|---------------------|------------------------|--------|
| Multiple PRs per day | Every 2-4 hours | Avoid large merge conflicts |
| 1-2 PRs per day | Morning + before PR | Stay reasonably current |
| Few PRs per week | Once daily | Minimal divergence |
| Inactive | Before starting work | No need for frequent checks |

---

### Primary Developer Workflow (Active Development)

**Starting your day:**
```bash
git checkout develop
git pull
git checkout -b feature/new-thing
# ... work ...
```

**Before creating PR:**
```bash
# Make sure develop hasn't changed
git fetch origin develop
git merge origin/develop  # Or rebase if you prefer
git push
gh pr create --base develop
```

**Frequency:** Pull `develop` before starting each new feature (once or twice daily)

---

### Other Developers Workflow (Collaborating)

**Starting their day:**
```bash
git checkout develop
git pull                  # Get latest develop
git checkout -b feature/their-feature
# ... work ...
```

**Mid-development check (if primary dev is actively merging PRs):**
```bash
# Every few hours or before taking a break
git checkout develop
git pull

# If they want their feature branch updated:
git checkout feature/their-feature
git merge develop         # Bring in latest changes
```

**Before creating PR:**
```bash
git checkout develop
git pull                  # Critical: get absolute latest
git checkout feature/their-feature
git merge develop         # Sync with latest
git push
gh pr create --base develop
```

**Frequency when primary is active:** Pull `develop` **every 2-4 hours** or **before each PR**

---

## Common Scenarios

### Scenario 1: Multiple Developers Working Simultaneously

**Primary Developer (You):**
```bash
# Monday morning
git checkout develop && git pull
git checkout -b feature/add-docs
# ... work for 2 hours ...
git push
gh pr create --base develop
gh pr merge --squash              # Merged at 10am

# Monday afternoon
git checkout develop && git pull
git checkout -b feature/fix-bug
# ... work for 1 hour ...
git push
gh pr create --base develop
gh pr merge --squash              # Merged at 2pm
```

**Other Developer:**
```bash
# Monday 9am - starts work
git checkout develop && git pull  # Gets your state from Sunday

# Works on their feature all morning
git checkout -b feature/new-parser
# ... 3 hours of work ...

# Monday 12pm - takes lunch break, syncs develop
git checkout develop && git pull  # Gets your 10am merge
git checkout feature/new-parser
git merge develop                 # Optional: bring changes into their feature

# Monday 3pm - ready to create PR
git checkout develop && git pull  # Gets your 2pm merge
git checkout feature/new-parser
git merge develop                 # Brings in both your merges
git push
gh pr create --base develop
```

**Key point:** They pulled develop **3 times** during a day when you were actively merging.

---

### Scenario 2: Working with Forks and Upstreams

If contributing from a fork:

```bash
# Add upstream remote (one time)
git remote add upstream git@github.com:original/rmagent.git

# Check your remotes
git remote -v
# origin    git@github.com:you/rmagent.git      (your fork)
# upstream  git@github.com:original/rmagent.git  (original repo)

# Sync your fork with upstream
git fetch upstream
git checkout develop
git merge upstream/develop
git push origin develop

# Now create feature from updated develop
git checkout -b feature/my-contribution
```

---

### Scenario 3: Keeping Feature Branch Updated

If develop has advanced while you're working on a long-running feature:

```bash
# You're on feature/long-feature
git checkout develop
git pull                          # Get latest develop

git checkout feature/long-feature
git merge develop                 # Merge latest develop into your feature

# Resolve any conflicts if they arise
git add .
git commit -m "merge: sync with latest develop"
git push
```

**Alternative using rebase (cleaner history):**
```bash
git checkout feature/long-feature
git rebase develop                # Replay your commits on top of latest develop

# If conflicts, resolve them then:
git add .
git rebase --continue

# Force push (only safe on your feature branch!)
git push --force
```

---

### Scenario 4: Viewing Repository State Without Merging

Want to see what's changed without affecting your working branch:

```bash
# Fetch all updates
git fetch --all

# View all branches
git branch -r

# Compare your branch with remote develop
git log HEAD..origin/develop      # What's in develop that you don't have
git log origin/develop..HEAD      # What you have that's not in develop

# View changes in a specific branch
git log origin/develop --oneline -10
git show origin/develop:path/to/file.py
```

---

### Scenario 5: Checking Tags and Releases

```bash
# Fetch tags
git fetch --all --tags

# List all tags
git tag -l

# View specific tag
git show v1.2.3

# Checkout a release
git checkout v1.2.3               # Detached HEAD at this tag
git checkout -b hotfix-v1.2.3     # Create branch from tag
```

---

## When You Actually Need `git fetch --all --tags`

### Use Case 1: Multiple Remotes

```bash
# You have a fork and upstream
git remote -v
# origin    git@github.com:you/rmagent.git
# upstream  git@github.com:original/rmagent.git

git fetch --all  # Gets from both origin AND upstream
```

### Use Case 2: Checking Tags/Releases

```bash
git fetch --all --tags
git tag -l              # See all version tags
git checkout v1.2.3     # Check out specific release
```

### Use Case 3: Viewing All Branch Activity

```bash
git fetch --all
git branch -r           # See all remote branches
git log --all --graph   # Visualize entire repository state
```

**For RMAgent** (single remote, team collaboration), these scenarios are rare.

---

## Quick Reference

### Daily Commands

```bash
# Start of day
git checkout develop && git pull

# Create new feature
git checkout -b feature/name

# Save work
git add . && git commit -m "message" && git push

# Sync with latest develop (mid-work)
git checkout develop && git pull
git checkout feature/name && git merge develop

# Before creating PR (CRITICAL)
git checkout develop && git pull
git checkout feature/name && git merge develop
gh pr create --base develop
```

---

### Understanding Branch State

```bash
# What branch am I on?
git branch

# What's changed locally?
git status
git diff

# What's different from remote?
git fetch
git log HEAD..origin/develop      # What's new in remote develop

# View recent history
git log --oneline -10
git log --all --graph --oneline
```

---

### Sync Checklist for Collaborators

**Before starting work:**
- [ ] `git checkout develop && git pull`

**Every 2-4 hours (if primary dev is active):**
- [ ] `git checkout develop && git pull`
- [ ] (Optional) Merge develop into your feature branch

**Before creating PR:**
- [ ] `git checkout develop && git pull`
- [ ] `git checkout feature/your-feature`
- [ ] `git merge develop` (resolve conflicts)
- [ ] `git push`
- [ ] `gh pr create --base develop`

---

## Key Takeaways

### ✅ Do This:
- **Use `git pull`** for 95% of your work
- **Pull develop frequently** when primary dev is active (every 2-4 hours)
- **Always pull develop before creating a PR**
- **Merge develop into your feature** if it's long-running
- **Delete feature branches after merge** (GitHub does this automatically with `--delete-branch`)

### ❌ Don't Do This:
- Don't assume feature branches are "sub-branches" of develop
- Don't go days without pulling if others are actively merging
- Don't create PRs without pulling develop first
- Don't force-push to develop or main (ever)
- Don't use `--admin` to bypass branch protection unless it's a genuine emergency

### 🎯 Remember:
- Feature branches are **independent** - they start from develop and merge back to develop
- `git pull` = fetch + merge for current branch
- `git fetch --all --tags` = comprehensive sync without merging
- Sync frequency depends on team activity level
- **When in doubt, pull develop before doing anything important**

---

## Getting Help

If you're stuck:

```bash
# Check your current state
git status

# View recent commits
git log --oneline -10

# See what's on remote
git fetch
git log origin/develop --oneline -10

# Undo local changes (if needed)
git checkout -- file.py           # Discard changes to file
git reset --hard origin/develop   # Reset to match remote (DESTRUCTIVE)
```

**Still stuck?** Check the full workflow guide: [git-workflow.md](git-workflow.md)

---

## Additional Resources

- [Pro Git Book](https://git-scm.com/book/en/v2) - Free comprehensive guide
- [Git Branching Model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) - Gitflow explained
- [GitHub CLI Manual](https://cli.github.com/manual/) - gh commands reference
- [RMAgent Git Workflow](git-workflow.md) - Project-specific workflow guide
