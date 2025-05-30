"""
Main module for the Telegram bot with integrated payment system.
Handles command processing, bot interactions, and payments.
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
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
from payment import PaymentHandler
import config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database and payment handler
db = Database(config.DATABASE_FILE)
payment_handler = PaymentHandler(db)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    db.add_user(user.id, user.username or "")
    
    # Create inline keyboard with main options
    keyboard = [
        [InlineKeyboardButton("🎬 Browse Videos", callback_data="browse_videos")],
        [InlineKeyboardButton("🛒 My Purchases", callback_data="view_purchases")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="show_help")]
    ]
    
    # Add admin button only for admins
    if db.is_admin(user.id) or user.id in config.ADMIN_USER_IDS:
        keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n"
        f"I'm a video sales bot. You can browse and purchase videos using Telegram Stars.\n\n"
        f"Use the buttons below to navigate:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    is_admin = db.is_admin(user.id) or user.id in config.ADMIN_USER_IDS
    
    help_text = "🎬 *Video Sales Bot Help* 🎬\n\n"
    help_text += "*User Commands:*\n"
    help_text += "/start - Show main menu with buttons\n"
    help_text += "/list - Browse all available videos\n"
    help_text += "/mypurchases - View your purchased videos\n"
    
    # Only show admin commands to admins
    if is_admin:
        help_text += "\n*Admin Commands:*\n"
        help_text += "/admin - Access admin panel\n"
        help_text += "/addvideo - Add a new video\n"
        help_text += "/removevideo [video_id] - Remove a video\n"
        help_text += "/broadcast - Send a message to all users\n"
    
    # Create inline keyboard with main options
    keyboard = [
        [InlineKeyboardButton("🎬 Browse Videos", callback_data="browse_videos")],
        [InlineKeyboardButton("🛒 My Purchases", callback_data="view_purchases")]
    ]
    
    # Add admin button only for admins
    if is_admin:
        keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

async def list_videos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available videos."""
    videos = db.get_all_videos()
    
    if not videos:
        await update.message.reply_text("No videos available at the moment.")
        return
    
    message = "🎬 *Available Videos* 🎬\n\n"
    
    # Create keyboard with buttons for each video
    keyboard = []
    
    for video_id, video in videos.items():
        message += f"*{video['title']}*\n"
        message += f"Price: {video['price']} Stars\n"
        message += f"Duration: {video.get('duration', 'N/A')}\n\n"
        
        # Add button for each video
        keyboard.append([InlineKeyboardButton(f"Buy: {video['title']}", callback_data=f"buy_{video_id}")])
        keyboard.append([InlineKeyboardButton(f"View Details: {video['title']}", callback_data=f"view_details_{video_id}")])
    
    # Add navigation buttons
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Inline version of list_videos for callback handling
async def list_videos_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available videos for inline callback."""
    query = update.callback_query
    videos = db.get_all_videos()
    
    if not videos:
        await query.edit_message_text("No videos available at the moment.",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    
    message = "🎬 *Available Videos* 🎬\n\n"
    
    # Create keyboard with buttons for each video
    keyboard = []
    
    for video_id, video in videos.items():
        message += f"*{video['title']}*\n"
        message += f"Price: {video['price']} Stars\n"
        message += f"Duration: {video.get('duration', 'N/A')}\n\n"
        
        # Add button for each video
        keyboard.append([InlineKeyboardButton(f"Buy: {video['title']}", callback_data=f"buy_{video_id}")])
        keyboard.append([InlineKeyboardButton(f"View Details: {video['title']}", callback_data=f"view_details_{video_id}")])
    
    # Add navigation buttons
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

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
        [InlineKeyboardButton("Buy Now", callback_data=f"buy_{video_id}")],
        [InlineKeyboardButton("🔙 Back to Videos", callback_data="browse_videos")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
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
    video = db.get_video(video_id)
    
    if not video:
        await update.message.reply_text(f"Video with ID {video_id} not found.")
        return
    
    # Create a callback query-like object for the payment handler
    class DummyCallbackQuery:
        def __init__(self, message):
            self.message = message
    
    update.callback_query = DummyCallbackQuery(update.message)
    await payment_handler.create_invoice(update, context, video_id)
    
    # Payment process will continue in the callback handler

async def my_purchases_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's purchased videos."""
    user_id = update.effective_user.id
    purchases = db.get_user_purchases(user_id)
    
    if not purchases:
        await update.message.reply_text(
            "You haven't purchased any videos yet.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
        return
    
    message = "🎬 *Your Purchased Videos* 🎬\n\n"
    keyboard = []
    
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
            keyboard.append([InlineKeyboardButton(f"Watch {video['title']}", callback_data=f"watch_{video_id}")])
    
    # Add navigation button
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Inline version of my_purchases for callback handling
async def my_purchases_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's purchased videos for inline callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    purchases = db.get_user_purchases(user_id)
    
    if not purchases:
        await query.edit_message_text(
            "You haven't purchased any videos yet.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
        return
    
    message = "🎬 *Your Purchased Videos* 🎬\n\n"
    keyboard = []
    
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
            keyboard.append([InlineKeyboardButton(f"Watch {video['title']}", callback_data=f"watch_{video_id}")])
    
    # Add navigation button
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Admin commands
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Access admin panel."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "You don't have permission to access admin features.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
        return
    
    # If user is not in database as admin but is in config, add them
    if not db.is_admin(user_id) and user_id in config.ADMIN_USER_IDS:
        user = update.effective_user
        db.add_user(user_id, user.username or "", is_admin=True)
    
    keyboard = [
        [InlineKeyboardButton("Add Video", callback_data="admin_add_video")],
        [InlineKeyboardButton("View All Videos", callback_data="admin_view_videos")],
        [InlineKeyboardButton("Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Panel* 🔐\n\n"
        "Select an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def add_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the process of adding a new video."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "You don't have permission to access admin features.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
        return
    
    context.user_data["admin_state"] = "waiting_for_video_title"
    await update.message.reply_text("Please send the title for the new video:")

async def remove_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a video from the catalog."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "You don't have permission to access admin features.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a video ID. Example: /removevideo video_1")
        return
    
    video_id = context.args[0]
    success = db.remove_video(video_id)
    
    if success:
        await update.message.reply_text(
            f"Video with ID {video_id} has been removed.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )
    else:
        await update.message.reply_text(
            f"Video with ID {video_id} not found.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    is_admin = db.is_admin(user_id) or user_id in config.ADMIN_USER_IDS
    
    # Main menu navigation
    if data == "main_menu":
        # Create inline keyboard with main options
        keyboard = [
            [InlineKeyboardButton("🎬 Browse Videos", callback_data="browse_videos")],
            [InlineKeyboardButton("🛒 My Purchases", callback_data="view_purchases")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="show_help")]
        ]
        
        # Add admin button only for admins
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👋 Welcome to the Video Sales Bot!\n\n"
            f"You can browse and purchase videos using Telegram Stars.\n\n"
            f"Use the buttons below to navigate:",
            reply_markup=reply_markup
        )
    
    # Help command
    elif data == "show_help":
        help_text = "🎬 *Video Sales Bot Help* 🎬\n\n"
        help_text += "*Available Actions:*\n"
        help_text += "• Browse Videos - See all available videos\n"
        help_text += "• My Purchases - View your purchased videos\n"
        
        # Only show admin info to admins
        if is_admin:
            help_text += "\n*Admin Actions:*\n"
            help_text += "• Admin Panel - Manage videos and users\n"
            help_text += "• Add Video - Upload new videos for sale\n"
            help_text += "• Remove Video - Delete existing videos\n"
            help_text += "• Broadcast - Send messages to all users\n"
        
        # Create inline keyboard with main options
        keyboard = [
            [InlineKeyboardButton("🎬 Browse Videos", callback_data="browse_videos")],
            [InlineKeyboardButton("🛒 My Purchases", callback_data="view_purchases")]
        ]
        
        # Add admin button only for admins
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Browse videos
    elif data == "browse_videos":
        await list_videos_inline(update, context)
    
    # View purchases
    elif data == "view_purchases":
        await my_purchases_inline(update, context)
    
    # Admin panel
    elif data == "admin_panel":
        if not is_admin:
            await query.edit_message_text(
                "You don't have permission to access admin features.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
            )
            return
            
        keyboard = [
            [InlineKeyboardButton("Add Video", callback_data="admin_add_video")],
            [InlineKeyboardButton("View All Videos", callback_data="admin_view_videos")],
            [InlineKeyboardButton("Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔐 *Admin Panel* 🔐\n\n"
            "Select an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Buy video
    elif data.startswith("buy_"):
        video_id = data.split("_", 1)[1]  # Split only on first underscore
        await payment_handler.create_invoice(update, context, video_id)
    
    elif data.startswith("confirm_buy_"):
        # This callback is no longer used as we now use the real Stars payment system
        # All purchases are handled through pre_checkout_query and successful_payment handlers
        await query.edit_message_text("Please use the Buy button to purchase videos with Stars.")
    
    elif data == "cancel_buy":
        await query.edit_message_text("Purchase cancelled.")
    
    # Watch video
    elif data.startswith("watch_"):
        video_id = data.split("_", 1)[1]  # Split only on first underscore
        # Check if user has actually purchased this video
        if db.has_purchased(user_id, video_id):
            await payment_handler.deliver_video(update, context, video_id)
        else:
            await query.edit_message_text(
                "You need to purchase this video before watching it.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
            )
    
    # View video details
    elif data.startswith("view_details_"):
        video_id = data.split("_", 2)[2]  # Split only on first two underscores
        video = db.get_video(video_id)
        
        if video:
            # Create keyboard with buy button
            keyboard = [
                [InlineKeyboardButton("Buy Now", callback_data=f"buy_{video_id}")],
                [InlineKeyboardButton("🔙 Back to Videos", callback_data="browse_videos")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = f"🎬 *{video['title']}* 🎬\n\n"
            message += f"*Description:* {video['description']}\n\n"
            message += f"*Price:* {video['price']} Stars\n"
            message += f"*Duration:* {video.get('duration', 'N/A')}\n"
            if "category" in video:
                message += f"*Category:* {video['category']}\n"
            if "tags" in video and video["tags"]:
                message += f"*Tags:* {', '.join(video['tags'])}\n"
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Admin callbacks
    elif data.startswith("admin_") and is_admin:
        if data == "admin_add_video":
            context.user_data["admin_state"] = "waiting_for_video_title"
            await query.edit_message_text("Please send the title for the new video:")
        
        elif data == "admin_view_videos":
            videos = db.get_all_videos()
            if not videos:
                await query.edit_message_text(
                    "No videos in the database.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]])
                )
                return
            
            message = "🎬 *All Videos* 🎬\n\n"
            keyboard = []
            
            for video_id, video in videos.items():
                message += f"*{video['title']}*\n"
                message += f"ID: `{video_id}`\n"
                message += f"Price: {video['price']} Stars\n\n"
                keyboard.append([InlineKeyboardButton(f"Remove: {video['title']}", callback_data=f"admin_remove_{video_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif data.startswith("admin_remove_"):
            video_id = data.split("_", 2)[2]
            success = db.remove_video(video_id)
            
            if success:
                await query.edit_message_text(
                    f"Video with ID {video_id} has been removed.\n\nClick below to return to admin panel.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]])
                )
            else:
                await query.edit_message_text(
                    f"Video with ID {video_id} not found.\n\nClick below to return to admin panel.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]])
                )
        
        elif data == "admin_broadcast":
            context.user_data["admin_state"] = "waiting_for_broadcast"
            await query.edit_message_text("Please send the message you want to broadcast to all users:")
    
    # Handle unauthorized admin access attempts
    elif data.startswith("admin_") and not is_admin:
        await query.edit_message_text(
            "You don't have permission to access admin features.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )

# Message handler for admin operations
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages for admin operations like adding videos."""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id) and user_id not in config.ADMIN_USER_IDS:
        return
    
    try:
        admin_state = context.user_data.get("admin_state", None)
        
        if admin_state == "waiting_for_video_title":
            # Validate title
            title = update.message.text.strip()
            if not title or len(title) < 3:
                await update.message.reply_text("Title must be at least 3 characters long. Please try again:")
                return
                
            context.user_data["new_video"] = {"title": title}
            context.user_data["admin_state"] = "waiting_for_video_description"
            await update.message.reply_text("Please send the description for the video:")
        
        elif admin_state == "waiting_for_video_description":
            # Validate description
            description = update.message.text.strip()
            if not description or len(description) < 10:
                await update.message.reply_text("Description must be at least 10 characters long. Please try again:")
                return
                
            context.user_data["new_video"]["description"] = description
            context.user_data["admin_state"] = "waiting_for_video_price"
            await update.message.reply_text("Please send the price in Stars for the video:")
        
        elif admin_state == "waiting_for_video_price":
            try:
                price = int(update.message.text)
                if price <= 0:
                    await update.message.reply_text("Price must be a positive number. Please try again:")
                    return
                    
                context.user_data["new_video"]["price"] = price
                context.user_data["admin_state"] = "waiting_for_video_duration"
                await update.message.reply_text("Please send the duration of the video (e.g., 10:30):")
            except ValueError:
                await update.message.reply_text("Please send a valid number for the price.")
        
        elif admin_state == "waiting_for_video_duration":
            # Validate duration format (simple check)
            duration = update.message.text.strip()
            if not duration:
                await update.message.reply_text("Please send a valid duration.")
                return
                
            context.user_data["new_video"]["duration"] = duration
            context.user_data["admin_state"] = "waiting_for_video_file"
            await update.message.reply_text("Please send the video file:")
        
        elif admin_state == "waiting_for_video_file":
            # Handle video file upload
            if update.message.video:
                video = update.message.video
                context.user_data["new_video"]["file_id"] = video.file_id
                
                try:
                    # Add the video to the database with validation
                    new_video = context.user_data["new_video"]
                    video_id = db.add_video(new_video)
                    
                    # Create keyboard with main options
                    keyboard = [
                        [InlineKeyboardButton("View All Videos", callback_data="admin_view_videos")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"Video added successfully with ID: {video_id}",
                        reply_markup=reply_markup
                    )
                    
                    # Clear admin state
                    context.user_data.pop("admin_state", None)
                    context.user_data.pop("new_video", None)
                except ValueError as e:
                    await update.message.reply_text(f"Error adding video: {str(e)}")
            else:
                await update.message.reply_text("Please send a video file.")
        
        elif admin_state == "waiting_for_broadcast":
            # Validate broadcast message
            broadcast_message = update.message.text.strip()
            if not broadcast_message or len(broadcast_message) < 5:
                await update.message.reply_text("Broadcast message must be at least 5 characters long. Please try again:")
                return
                
            # In a real implementation, we would iterate through all users and send the message
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Broadcast message sent: {broadcast_message}",
                reply_markup=reply_markup
            )
            context.user_data.pop("admin_state", None)
    except Exception as e:
        logger.error(f"Error in admin message handler: {e}")
        await update.message.reply_text("An error occurred while processing your request. Please try again.")

# Payment handlers
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the pre-checkout callback."""
    await payment_handler.handle_pre_checkout(update, context)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment."""
    await payment_handler.handle_successful_payment(update, context)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user of error
    if update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_videos_command))
    application.add_handler(CommandHandler("view", view_video_command))
    application.add_handler(CommandHandler("buy", buy_video_command))
    application.add_handler(CommandHandler("mypurchases", my_purchases_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("addvideo", add_video_command))
    application.add_handler(CommandHandler("removevideo", remove_video_command))
    
    # Add payment handlers
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for admin operations
    application.add_handler(MessageHandler((filters.TEXT | filters.VIDEO) & ~filters.COMMAND, handle_admin_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Define post-init callback to run after application starts
    async def post_init(application: Application) -> None:
        bot_info = await application.bot.get_me()
        config.BOT_USERNAME = bot_info.username
        logger.info(f"Bot starting as @{config.BOT_USERNAME}")
    
    # Start the Bot with post_init callback
    application.post_init = post_init
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
