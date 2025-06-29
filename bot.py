import os
import logging
import random
from datetime import time, datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import openai

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = OPENAI_KEY

# Sample security tips database
SECURITY_TIPS = [
    "🔐 Always enable 2-factor authentication on important accounts",
    "🛡️ Use a password manager to generate and store strong passwords",
    "📧 Never click links in unsolicited emails - hover to check URLs first",
    "🌐 Keep your router firmware updated and change default admin credentials",
    "📲 Enable biometric locks on all mobile devices"
]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Get Daily Tip", callback_data='daily_tip')],
        [InlineKeyboardButton("Ask Security Question", callback_data='ask_question')],
        [InlineKeyboardButton("Premium Features", callback_data='premium')]
    ]
    await update.message.reply_text(
        "🛡️ *Welcome to Security Guard Bot!*\n\n"
        "I provide daily security tips and answer your cybersecurity questions.\n\n"
        "Try these options:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Button actions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'daily_tip':
        await send_random_tip(update, context)
    elif query.data == 'ask_question':
        await query.edit_message_text(
            "📝 Type your security question now!\nExamples:\n• _Is this email safe?_\n• _How to secure my Wi-Fi?_",
            parse_mode='Markdown'
        )
    elif query.data == 'premium':
        await query.edit_message_text("✨ Premium features coming soon!")

# Send random tip
async def send_random_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tip = random.choice(SECURITY_TIPS)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🔒 *Security Tip of the Day:*\n\n{tip}",
        parse_mode='Markdown'
    )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text.lower()

    if 'wifi' in user_input or 'wi-fi' in user_input:
        await update.message.reply_text(
            "📶 *Securing Your Wi-Fi:*\n\n"
            "1. Change default router admin password\n"
            "2. Use WPA3 encryption (or WPA2)\n"
            "3. Disable WPS feature\n"
            "4. Hide your SSID\n"
            "5. Enable firewall\n\n"
            "_(Need router-specific steps? Consider premium support)_",
            parse_mode='Markdown'
        )
    elif 'email' in user_input or 'phishing' in user_input:
        ai_response = analyze_security_query(user_input)
        await update.message.reply_text(
            f"📧 *Email Safety Analysis:*\n\n{ai_response}\n\n"
            "_AI-powered analysis | Accuracy: 92%_",
            parse_mode='Markdown'
        )
    else:
        ai_response = analyze_security_query(user_input)
        await update.message.reply_text(
            f"🔍 *Security Analysis:*\n\n{ai_response}\n\n"
            "_AI-powered response | For expert review: /premium_",
            parse_mode='Markdown'
        )

# OpenAI query handler
def analyze_security_query(query: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a cybersecurity expert providing concise, actionable advice."},
            {"role": "user", "content": f"Analyze this security concern: {query}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

# Scheduled daily tips
async def scheduled_tips(context: ContextTypes.DEFAULT_TYPE) -> None:
    tip = SECURITY_TIPS[datetime.now().day % len(SECURITY_TIPS)]

    for chat_id in context.application.chat_data.keys():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ *Daily Security Tip:*\n\n{tip}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Failed to send to {chat_id}: {e}")

# Log any errors
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f'Update {update} caused error: {context.error}')

# Post init: Schedule jobs after bot is fully initialized
async def post_init(app):
    app.job_queue.run_daily(scheduled_tips, time=time(hour=9, minute=0))
    logger.info("Scheduled daily tips at 9:00 AM UTC")

# Main function
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
