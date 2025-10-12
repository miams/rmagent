# CLI Setup Guide - Direct Access & Tab Completion

This guide shows you how to use `rmagent` commands directly (without `uv run`) and enable tab completion for all CLI commands.

## Quick Setup

Run the automated setup script:

```bash
./setup_cli.sh
```

Then follow the instructions to add configuration to your shell profile (see below).

## Manual Setup

If you prefer manual setup or want to understand what's happening:

### Step 1: Install Package in Editable Mode

```bash
uv pip install -e .
```

This installs the `rmagent` command into `.venv/bin/rmagent`.

### Step 2: Add to PATH

Add the virtual environment's bin directory to your PATH.

#### For zsh (macOS default):

Add to `~/.zshrc`:

```bash
# RMAgent CLI setup
export PATH="/Users/miams/Code/RM11/.venv/bin:$PATH"
```

#### For bash:

Add to `~/.bashrc`:

```bash
# RMAgent CLI setup
export PATH="/Users/miams/Code/RM11/.venv/bin:$PATH"
```

### Step 3: Enable Tab Completion

#### For zsh:

1. Generate the completion script:

```bash
mkdir -p ~/.zfunc
_RMAGENT_COMPLETE=zsh_source .venv/bin/rmagent > ~/.zfunc/_rmagent
```

2. Add to `~/.zshrc`:

```bash
# Enable completion
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit
```

3. Reload shell:

```bash
source ~/.zshrc
```

#### For bash:

1. Generate the completion script:

```bash
mkdir -p ~/.bash_completion.d
_RMAGENT_COMPLETE=bash_source .venv/bin/rmagent > ~/.bash_completion.d/rmagent
```

2. Add to `~/.bashrc`:

```bash
# RMAgent completion
source ~/.bash_completion.d/rmagent
```

3. Reload shell:

```bash
source ~/.bashrc
```

#### For fish:

1. Generate the completion script:

```bash
mkdir -p ~/.config/fish/completions
_RMAGENT_COMPLETE=fish_source .venv/bin/rmagent > ~/.config/fish/completions/rmagent.fish
```

2. Restart fish shell (completions load automatically)

## Verification

After setup, verify everything works:

```bash
# Check command is available
which rmagent
# Should output: /Users/miams/Code/RM11/.venv/bin/rmagent

# Test command works
rmagent --version
# Should output: rmagent, version 0.1.0

# Test tab completion
rmagent <TAB>
# Should show: ask  bio  completion  export  person  quality  search  timeline

# Test command options completion
rmagent bio <TAB>
# Should show available options and arguments
```

## Usage Examples

Now you can use `rmagent` directly without `uv run`:

```bash
# Query person
rmagent person 1 --events --family

# Generate biography
rmagent bio 1 --length standard --output bio.md

# Run quality checks
rmagent quality --severity critical

# Ask questions
rmagent ask "Who were John Smith's parents?"

# Generate timeline
rmagent timeline 1 --output timeline.json

# Export to Hugo
rmagent export hugo 1 --output-dir content/people

# Search database
rmagent search --name "Smith"
```

## Tab Completion Features

With tab completion enabled, you get:

1. **Command completion**: Type `rmagent <TAB>` to see all commands
2. **Option completion**: Type `rmagent bio --<TAB>` to see all options
3. **Choice completion**: Type `rmagent quality --severity <TAB>` to see severity levels
4. **File path completion**: File paths autocomplete when needed

## Troubleshooting

### Command not found

If `rmagent` command isn't found after setup:

1. Check PATH includes `.venv/bin`:
   ```bash
   echo $PATH | grep ".venv/bin"
   ```

2. Verify binary exists:
   ```bash
   ls -la .venv/bin/rmagent
   ```

3. Reload shell configuration:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

### Tab completion not working

1. Verify completion script exists:
   ```bash
   ls -la ~/.zfunc/_rmagent      # zsh
   ls -la ~/.bash_completion.d/rmagent  # bash
   ls -la ~/.config/fish/completions/rmagent.fish  # fish
   ```

2. Check `fpath` includes completion directory (zsh):
   ```bash
   echo $fpath | grep ".zfunc"
   ```

3. Verify `compinit` is called (zsh):
   ```bash
   grep compinit ~/.zshrc
   ```

4. Regenerate completion script if needed:
   ```bash
   ./setup_cli.sh
   ```

### Development workflow

When developing, you don't need to reinstall after code changes because the package is installed in editable mode (`-e`). Changes to Python code are immediately available.

However, if you change the CLI command structure (add/remove commands), you may want to regenerate the completion script:

```bash
# Regenerate completion
_RMAGENT_COMPLETE=zsh_source rmagent > ~/.zfunc/_rmagent

# Reload completions
source ~/.zshrc
```

## Alternative: Using Aliases

If you prefer not to modify PATH, you can create an alias:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias rmagent="/Users/miams/Code/RM11/.venv/bin/rmagent"
```

Note: Tab completion will still work with aliases once the completion script is sourced.

## Alternative: Activating Virtual Environment

Another approach is to activate the virtual environment in your shell session:

```bash
# Activate venv (one-time per session)
source .venv/bin/activate

# Now use commands directly
rmagent person 1

# Deactivate when done
deactivate
```

With this approach, the `rmagent` command is available for the duration of your shell session.

## See Also

- [USAGE.md](../USAGE.md) - Complete CLI reference with examples
- [README.md](../README.md) - Project overview and features
- [FAQ.md](../FAQ.md) - Common questions and troubleshooting
