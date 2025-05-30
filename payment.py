"""
Payment module for the Telegram bot.
Handles Telegram Stars payment integration for digital goods and services.
"""

from telegram import (
    Update, 
    LabeledPrice, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
from database import Database
import config
import logging

logger = logging.getLogger(__name__)

class PaymentHandler:
    def __init__(self, database: Database):
        self.db = database
    
    async def create_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str) -> bool:
        """Create a payment invoice for a video using Telegram Stars."""
        user_id = update.effective_user.id
        video = self.db.get_video(video_id)
        
        if not video:
            await update.callback_query.message.reply_text(f"Video with ID {video_id} not found.")
            return False
        
        # Check if user already purchased this video
        if self.db.has_purchased(user_id, video_id):
            keyboard = [
                [InlineKeyboardButton("View My Purchases", callback_data="view_purchases")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                f"You've already purchased this video. Check your purchases to view it.",
                reply_markup=reply_markup
            )
            return False
        
        # Create the invoice using Telegram Stars (XTR)
        title = f"Purchase: {video['title']}"
        description = video['description'][:255]  # Telegram limits description to 255 chars
        payload = f"video_{video_id}"
        currency = "XTR"  # Using Telegram Stars currency
        prices = [LabeledPrice("Video", video['price'])]  # For Stars, don't multiply by 100
        
        try:
            # For digital goods, provider_token is left empty as per Telegram documentation
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=title,
                description=description,
                payload=payload,
                provider_token="",  # Empty for digital goods using Stars
                currency=currency,
                prices=prices,
                start_parameter=f"buy-{video_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            await update.callback_query.message.reply_text(
                "Sorry, there was an error processing your payment request. Please try again later."
            )
            return False
    
    async def handle_pre_checkout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the pre-checkout callback."""
        query = update.pre_checkout_query
        
        # Check if the payload is valid
        if not query.invoice_payload.startswith("video_"):
            await query.answer(ok=False, error_message="Invalid payment payload")
            return
        
        # Extract video_id from payload
        video_id = query.invoice_payload.split("_", 1)[1]
        video = self.db.get_video(video_id)
        
        if not video:
            await query.answer(ok=False, error_message="Video not found")
            return
        
        # Check if user already purchased this video
        if self.db.has_purchased(query.from_user.id, video_id):
            await query.answer(ok=False, error_message="You already own this video")
            return
        
        # Everything is fine, approve the payment
        await query.answer(ok=True)
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle successful payment."""
        payment = update.message.successful_payment
        
        if not payment.invoice_payload.startswith("video_"):
            logger.error(f"Invalid payment payload: {payment.invoice_payload}")
            await update.message.reply_text("There was an error processing your payment.")
            return
        
        # Extract video_id from payload
        video_id = payment.invoice_payload.split("_", 1)[1]
        video = self.db.get_video(video_id)
        
        if not video:
            logger.error(f"Video not found for payment: {video_id}")
            await update.message.reply_text("There was an error processing your payment.")
            return
        
        # Record the purchase
        user_id = update.effective_user.id
        price = payment.total_amount  # Don't divide by 100 for Stars payments
        success = self.db.add_purchase(user_id, video_id, int(price))
        
        if success:
            # Send the purchased video
            await self.deliver_video(update, context, video_id)
            
            # Confirm purchase
            keyboard = [
                [InlineKeyboardButton("View My Purchases", callback_data="view_purchases")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Thank you for your purchase of '{video['title']}'!\n\n"
                f"You can access your purchased videos anytime using /mypurchases",
                reply_markup=reply_markup
            )
        else:
            logger.error(f"Failed to record purchase for user {user_id}, video {video_id}")
            await update.message.reply_text(
                "Your payment was successful, but there was an error recording your purchase. "
                "Please contact support."
            )
    
    async def deliver_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str) -> None:
        """Deliver the purchased video to the user."""
        video = self.db.get_video(video_id)
        
        if not video or "file_id" not in video:
            logger.error(f"Cannot deliver video {video_id}: Video not found or file_id missing")
            
            # Determine how to send the error message based on the update type
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "There was an error delivering your video. Please contact support."
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    "There was an error delivering your video. Please contact support."
                )
            return
        
        # Verify the user has purchased this video
        user_id = update.effective_user.id
        if not self.db.has_purchased(user_id, video_id):
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    "You need to purchase this video before watching it."
                )
            elif hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "You need to purchase this video before watching it."
                )
            return
        
        # Send the video using the stored file_id
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video["file_id"],
                caption=f"🎬 {video['title']}\n\nEnjoy your video!"
            )
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "There was an error delivering your video. Please try accessing it from /mypurchases"
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    "There was an error delivering your video. Please try accessing it from /mypurchases"
                )
