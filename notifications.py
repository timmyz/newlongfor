import logging
from dingtalkchatbot.chatbot import DingtalkChatbot

logging.basicConfig(level=logging.INFO)

def send_notification(webhook: str, secret: str, message: str):
    """Sends a notification to DingTalk."""
    if not webhook or not secret:
        logging.warning("DingTalk webhook or secret not configured. Skipping notification.")
        return

    try:
        # Initialize chatbot
        bot = DingtalkChatbot(webhook, secret=secret)
        
        # Send message
        bot.send_text(msg=f"[龙湖签到通知]\n\n{message}", is_at_all=False)
        logging.info("Successfully sent DingTalk notification.")
    except Exception as e:
        logging.error(f"Failed to send DingTalk notification: {e}")
