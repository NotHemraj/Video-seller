#!/bin/bash

# Kill any existing bot instances to prevent conflicts
pkill -f "python.*main.py" || true

# Wait a moment to ensure processes are terminated
sleep 2

# Start the bot in the background
cd "$(dirname "$0")"
nohup python3 main.py > bot.log 2>&1 &

# Get the process ID
BOT_PID=$!

# Check if the bot started successfully
if ps -p $BOT_PID > /dev/null; then
    echo "Bot started successfully with PID: $BOT_PID"
    echo "Log file: $(pwd)/bot.log"
else
    echo "Failed to start the bot. Check the log file for errors."
    exit 1
fi
