"""
Main module for the Telegram bot.
Handles command processing and bot interactions.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters,
    PreCheckoutQueryHandler
)
from database import Database
import config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database(config.DATABASE_FILE)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    db.add_user(user.id, user.username or "")
    
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n"
        f"I'm a video sales bot. You can browse and purchase videos using Telegram Stars.\n\n"
        f"Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🎬 *Video Sales Bot Commands* 🎬\n\n"
        "*User Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/list - List all available videos\n"
        "/view [video_id] - View details of a specific video\n"
        "/buy [video_id] - Purchase a specific video\n"
        "/mypurchases - View your purchased videos\n\n"
        "*Admin Commands:*\n"
        "/admin - Access admin panel\n"
        "/addvideo - Add a new video\n"
        "/removevideo [video_id] - Remove a video\n"
        "/updatevideo [video_id] - Update video details\n"
        "/sales - View sales statistics\n"
        "/broadcast - Send a message to all users"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def list_videos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available videos."""
    videos = db.get_all_videos()
    
    if not videos:
        await update.message.reply_text("No videos available at the moment.")
        return
    
    message = "🎬 *Available Videos* 🎬\n\n"
    
    for video_id, video in videos.items():
        message += f"*{video['title']}*\n"
        message += f"ID: `{video_id}`\n"
        message += f"Price: {video['price']} Stars\n"
        message += f"Duration: {video.get('duration', 'N/A')}\n\n"
        message += f"Use /view {video_id} for more details\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def view_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View details of a specific video."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a video ID. Example: /view video_1")
        return
    
    video_id = context.args[0]
    video = db.get_video(video_id)
    
    if not video:
        await update.message.reply_text(f"Video with ID {video_id} not found.")
        return
    
    # Create keyboard with buy button
    keyboard = [
        [InlineKeyboardButton("Buy Now", callback_data=f"buy_{video_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send video preview if available
    if "preview_url" in video and video["preview_url"]:
        # This would send a preview image or video clip
        # Implementation depends on how previews are stored
        pass
    
    message = f"🎬 *{video['title']}* 🎬\n\n"
    message += f"*Description:* {video['description']}\n\n"
    message += f"*Price:* {video['price']} Stars\n"
    message += f"*Duration:* {video.get('duration', 'N/A')}\n"
    if "category" in video:
        message += f"*Category:* {video['category']}\n"
    if "tags" in video and video["tags"]:
        message += f"*Tags:* {', '.join(video['tags'])}\n"
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def buy_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiate purchase of a specific video."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a video ID. Example: /buy video_1")
        return
    
    video_id = context.args[0]
    await process_buy_request(update, context, video_id)

async def process_buy_request(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str) -> None:
    """Process a buy request for a specific video."""
    user_id = update.effective_user.id
    video = db.get_video(video_id)
    
    if not video:
        await update.message.reply_text(f"Video with ID {video_id} not found.")
        return
    
    # Check if user already purchased this video
    if db.has_purchased(user_id, video_id):
        keyboard = [
            [InlineKeyboardButton("View My Purchases", callback_data="view_purchases")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"You've already purchased this video. Check your purchases to view it.",
            reply_markup=reply_markup
        )
        return
    
    # This is where we would integrate with Telegram's payment system
    # For now, we'll just simulate the payment process
    
    await update.message.reply_text(
        f"To purchase '{video['title']}' for {video['price']} Stars, please confirm:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Confirm Purchase", callback_data=f"confirm_buy_{video_id}"),
                InlineKeyboardButton("Cancel", callback_data="cancel_buy")
            ]
        ])
    )

async def my_purchases_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's purchased videos."""
    user_id = update.effective_user.id
    purchases = db.get_user_purchases(user_id)
    
    if not purchases:
        await update.message.reply_text("You haven't purchased any videos yet.")
        return
    
    message = "🎬 *Your Purchased Videos* 🎬\n\n"
    
    for purchase in purchases:
        video_id = purchase["video_id"]
        video = db.get_video(video_id)
        
        if video:
            import datetime
            purchase_date = datetime.datetime.fromtimestamp(purchase["purchase_date"]).strftime('%Y-%m-%d')
            
            message += f"*{video['title']}*\n"
            message += f"Purchased on: {purchase_date}\n"
            message += f"Price paid: {purchase['price_paid']} Stars\n\n"
            
            # Add button to view this video
            keyboard = [
                [InlineKeyboardButton(f"Watch {video['title']}", callback_data=f"watch_{video_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Admin commands
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Access admin panel."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text("You don't have permission to access admin features.")
        return
    
    # If user is not in database as admin but is in config, add them
    if not db.is_admin(user_id) and user_id in config.ADMIN_USER_IDS:
        user = update.effective_user
        db.add_user(user_id, user.username or "", is_admin=True)
    
    keyboard = [
        [InlineKeyboardButton("Add Video", callback_data="admin_add_video")],
        [InlineKeyboardButton("View All Videos", callback_data="admin_view_videos")],
        [InlineKeyboardButton("Sales Statistics", callback_data="admin_sales")],
        [InlineKeyboardButton("Broadcast Message", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Panel* 🔐\n\n"
        "Select an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("buy_"):
        video_id = data.split("_")[1]
        await process_buy_request(update, context, video_id)
    
    elif data.startswith("confirm_buy_"):
        video_id = data.split("_")[2]
        video = db.get_video(video_id)
        
        if video:
            user_id = update.effective_user.id
            
            # Simulate successful payment
            success = db.add_purchase(user_id, video_id, video["price"])
            
            if success:
                # Here we would actually send the video
                await query.edit_message_text(
                    f"✅ Payment successful! You've purchased '{video['title']}'.\n\n"
                    f"Use /mypurchases to access your videos."
                )
            else:
                await query.edit_message_text("❌ Error processing your purchase. Please try again.")
    
    elif data == "cancel_buy":
        await query.edit_message_text("Purchase cancelled.")
    
    elif data == "view_purchases":
        await my_purchases_command(update, context)
    
    elif data.startswith("watch_"):
        video_id = data.split("_")[1]
        video = db.get_video(video_id)
        user_id = update.effective_user.id
        
        if video and db.has_purchased(user_id, video_id):
            # Here we would send the actual video file
            await query.message.reply_text(f"Here's your video: {video['title']}")
            # In a real implementation, we would use context.bot.send_video with the file_id
    
    # Admin callbacks
    elif data.startswith("admin_") and (db.is_admin(update.effective_user.id) or update.effective_user.id in config.ADMIN_USER_IDS):
        if data == "admin_add_video":
            context.user_data["admin_state"] = "waiting_for_video_title"
            await query.edit_message_text("Please send the title for the new video:")
        
        elif data == "admin_view_videos":
            videos = db.get_all_videos()
            if not videos:
                await query.edit_message_text("No videos in the database.")
                return
            
            message = "🎬 *All Videos* 🎬\n\n"
            for video_id, video in videos.items():
                message += f"*{video['title']}*\n"
                message += f"ID: `{video_id}`\n"
                message += f"Price: {video['price']} Stars\n\n"
            
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif data == "admin_sales":
            # Implement sales statistics
            await query.edit_message_text("Sales statistics feature coming soon.")
        
        elif data == "admin_broadcast":
            context.user_data["admin_state"] = "waiting_for_broadcast"
            await query.edit_message_text("Please send the message you want to broadcast to all users:")

# Message handler for admin operations
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages for admin operations like adding videos."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        return
    
    admin_state = context.user_data.get("admin_state", None)
    
    if admin_state == "waiting_for_video_title":
        context.user_data["new_video"] = {"title": update.message.text}
        context.user_data["admin_state"] = "waiting_for_video_description"
        await update.message.reply_text("Please send the description for the video:")
    
    elif admin_state == "waiting_for_video_description":
        context.user_data["new_video"]["description"] = update.message.text
        context.user_data["admin_state"] = "waiting_for_video_price"
        await update.message.reply_text("Please send the price in Stars for the video:")
    
    elif admin_state == "waiting_for_video_price":
        try:
            price = int(update.message.text)
            context.user_data["new_video"]["price"] = price
            context.user_data["admin_state"] = "waiting_for_video_duration"
            await update.message.reply_text("Please send the duration of the video (e.g., 10:30):")
        except ValueError:
            await update.message.reply_text("Please send a valid number for the price.")
    
    elif admin_state == "waiting_for_video_duration":
        context.user_data["new_video"]["duration"] = update.message.text
        context.user_data["admin_state"] = "waiting_for_video_file"
        await update.message.reply_text("Please send the video file:")
    
    elif admin_state == "waiting_for_video_file":
        # Handle video file upload
        if update.message.video:
            video = update.message.video
            context.user_data["new_video"]["file_id"] = video.file_id
            
            # Add the video to the database
            new_video = context.user_data["new_video"]
            video_id = db.add_video(new_video)
            
            await update.message.reply_text(f"Video added successfully with ID: {video_id}")
            
            # Clear admin state
            context.user_data.pop("admin_state", None)
            context.user_data.pop("new_video", None)
        else:
            await update.message.reply_text("Please send a video file.")
    
    elif admin_state == "waiting_for_broadcast":
        # Implement broadcast functionality
        broadcast_message = update.message.text
        # In a real implementation, we would iterate through all users and send the message
        await update.message.reply_text(f"Broadcast message sent: {broadcast_message}")
        context.user_data.pop("admin_state", None)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user of error
    if update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Get bot info and update config
    async def update_bot_info(application):
        bot = application.bot
        bot_info = await bot.get_me()
        config.BOT_USERNAME = bot_info.username
        logger.info(f"Bot started as @{config.BOT_USERNAME}")
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_videos_command))
    application.add_handler(CommandHandler("view", view_video_command))
    application.add_handler(CommandHandler("buy", buy_video_command))
    application.add_handler(CommandHandler("mypurchases", my_purchases_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for admin operations
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    application.job_queue.run_once(update_bot_info, 0)

if __name__ == '__main__':
    main()
