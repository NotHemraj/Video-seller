# Telegram Video Sales Bot - User Documentation

## Overview

This Telegram bot allows you to sell videos using Telegram's built-in Stars currency. Users can browse available videos, purchase them using Stars, and receive the purchased videos directly in their chat.

## Features

- **Video Listing**: Users can browse available videos with descriptions and prices
- **Stars Payment**: Integrated with Telegram's Stars payment system
- **Video Delivery**: Automatic delivery of purchased videos
- **Admin Controls**: Add, remove, and update videos in the catalog
- **User Management**: Track user purchases and interactions

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Telegram bot token (already configured)
- A Telegram account with Stars payment enabled (for production use)

### Installation

1. Clone or download the bot files to your server
2. Install the required dependencies:
   ```
   pip install python-telegram-bot python-dotenv
   ```
3. Configure your environment variables:
   - The bot comes with a `.env` file containing your bot token
   - For production, you may want to add admin user IDs and payment provider token

### Configuration

The bot uses environment variables for sensitive information:

- `BOT_TOKEN`: Your Telegram bot token (already configured)
- `PAYMENT_PROVIDER_TOKEN`: Token for Telegram payments (required for real payments)
- `ADMIN_USER_IDS`: Comma-separated list of Telegram user IDs who have admin access

### Running the Bot

To start the bot, navigate to the bot directory and run:

```
python main.py
```

For production deployment, consider using a process manager like `systemd` or `supervisor` to keep the bot running continuously.

## User Commands

- `/start` - Start the bot and receive a welcome message
- `/help` - Display available commands and their descriptions
- `/list` - List all available videos
- `/view [video_id]` - View details of a specific video
- `/buy [video_id]` - Purchase a specific video
- `/mypurchases` - View your purchased videos

## Admin Commands

- `/admin` - Access admin panel
- `/addvideo` - Add a new video to the catalog
- `/removevideo [video_id]` - Remove a video from the catalog
- `/updatevideo [video_id]` - Update video information (not yet implemented)
- `/sales` - View sales statistics (not yet implemented)
- `/broadcast` - Send a message to all users

## Adding Videos

As an admin, you can add videos using the `/addvideo` command. The bot will guide you through the process:

1. Send the video title
2. Send the video description
3. Send the price in Stars
4. Send the video duration
5. Upload the video file

## Security Features

- Bot token and payment credentials are stored securely in environment variables
- Admin access is restricted to authorized users only
- Input validation prevents invalid data from being processed
- Error handling ensures the bot remains stable

## Troubleshooting

- If the bot doesn't respond, check if it's running on your server
- If payments don't work, ensure your payment provider token is correctly configured
- For admin access issues, make sure your Telegram user ID is added to the ADMIN_USER_IDS list

## Support

For additional support or feature requests, please contact the developer who provided this bot.

## License

This bot is provided for your personal use only and is not to be redistributed without permission.
