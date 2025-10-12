#!/bin/bash
# Setup script for RMAgent CLI with shell completion
# This script configures direct CLI access and tab completion

set -e

echo "Setting up RMAgent CLI..."

# Ensure package is installed in editable mode
echo "Installing rmagent in editable mode..."
uv pip install -e .

# Detect shell
SHELL_NAME=$(basename "$SHELL")

# Create completion directory if needed
if [ "$SHELL_NAME" = "zsh" ]; then
    COMPLETION_DIR="$HOME/.zfunc"
    mkdir -p "$COMPLETION_DIR"

    echo "Generating zsh completion script..."
    _RMAGENT_COMPLETE=zsh_source .venv/bin/rmagent > "$COMPLETION_DIR/_rmagent"

    echo ""
    echo "✓ Completion script saved to $COMPLETION_DIR/_rmagent"
    echo ""
    echo "Add the following to your ~/.zshrc:"
    echo ""
    echo "  # RMAgent CLI setup"
    echo "  export PATH=\"$PWD/.venv/bin:\$PATH\""
    echo "  fpath=(~/.zfunc \$fpath)"
    echo "  autoload -Uz compinit && compinit"
    echo ""
    echo "Then run: source ~/.zshrc"

elif [ "$SHELL_NAME" = "bash" ]; then
    COMPLETION_DIR="$HOME/.bash_completion.d"
    mkdir -p "$COMPLETION_DIR"

    echo "Generating bash completion script..."
    _RMAGENT_COMPLETE=bash_source .venv/bin/rmagent > "$COMPLETION_DIR/rmagent"

    echo ""
    echo "✓ Completion script saved to $COMPLETION_DIR/rmagent"
    echo ""
    echo "Add the following to your ~/.bashrc:"
    echo ""
    echo "  # RMAgent CLI setup"
    echo "  export PATH=\"$PWD/.venv/bin:\$PATH\""
    echo "  source ~/.bash_completion.d/rmagent"
    echo ""
    echo "Then run: source ~/.bashrc"

elif [ "$SHELL_NAME" = "fish" ]; then
    COMPLETION_DIR="$HOME/.config/fish/completions"
    mkdir -p "$COMPLETION_DIR"

    echo "Generating fish completion script..."
    _RMAGENT_COMPLETE=fish_source .venv/bin/rmagent > "$COMPLETION_DIR/rmagent.fish"

    echo ""
    echo "✓ Completion script saved to $COMPLETION_DIR/rmagent.fish"
    echo ""
    echo "Add the following to your ~/.config/fish/config.fish:"
    echo ""
    echo "  # RMAgent CLI setup"
    echo "  set -gx PATH \"$PWD/.venv/bin\" \$PATH"
    echo ""
    echo "Fish will automatically load completions on next shell start"
fi

echo ""
echo "================================================================"
echo "Setup complete!"
echo ""
echo "After updating your shell configuration, you can use:"
echo "  rmagent --help          # Show help"
echo "  rmagent person 1        # Query person"
echo "  rmagent bio 1           # Generate biography"
echo "  rmagent <TAB>           # See all commands with tab completion"
echo "================================================================"
