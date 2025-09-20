#!/bin/bash

# Script to run start_all.py in the current worktree via tmux
# Usage: ./run_worktree.sh

set -e

# Get current working directory (the worktree path)
WORKTREE_PATH=$(pwd)
BRANCH_NAME=$(git branch --show-current)

echo "Current worktree: $WORKTREE_PATH"
echo "Current branch: $BRANCH_NAME"

# Check if start_all.py exists in current directory
if [ ! -f "start_all.py" ]; then
    echo "Error: start_all.py not found in current directory: $WORKTREE_PATH"
    exit 1
fi

# Create or attach to tmux session
SESSION_NAME=$(tmux display-message -p '#S' 2>/dev/null || echo "main")
WINDOW_NAME="run"

echo "Using tmux session: $SESSION_NAME"
echo "Target window: $WINDOW_NAME"

# Check if the window already exists
if tmux list-windows -t "$SESSION_NAME" -F "#{window_name}" 2>/dev/null | grep -q "^$WINDOW_NAME$"; then
    echo "Window '$WINDOW_NAME' already exists. Killing existing processes..."
    # Send Ctrl+C to stop any running processes
    tmux send-keys -t "$SESSION_NAME:$WINDOW_NAME" C-c
    sleep 1
    # Clear the window
    tmux send-keys -t "$SESSION_NAME:$WINDOW_NAME" "clear" Enter
else
    echo "Creating new window '$WINDOW_NAME'..."
    tmux new-window -t "$SESSION_NAME" -n "$WINDOW_NAME"
fi

# Change to the worktree directory and run start_all.py
echo "Running python3 start_all.py in worktree: $WORKTREE_PATH"
tmux send-keys -t "$SESSION_NAME:$WINDOW_NAME" "cd '$WORKTREE_PATH'" Enter
tmux send-keys -t "$SESSION_NAME:$WINDOW_NAME" "echo 'Starting in worktree: $WORKTREE_PATH (branch: $BRANCH_NAME)'" Enter
tmux send-keys -t "$SESSION_NAME:$WINDOW_NAME" "python3 start_all.py" Enter

# Switch to the window to show the output
tmux select-window -t "$SESSION_NAME:$WINDOW_NAME"

echo "Script launched in tmux window '$WINDOW_NAME'"
echo "Use 'tmux attach' to view the session if not already attached"