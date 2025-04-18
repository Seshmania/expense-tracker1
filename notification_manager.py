import os
from twilio.rest import Client
import datetime
import json
import db_manager

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms_notification(to_phone_number, message):
    """Send SMS notification using Twilio"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("Twilio credentials not configured. SMS notification not sent.")
        return False
    
    if not to_phone_number:
        print("No recipient phone number provided. SMS notification not sent.")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        print(f"SMS notification sent with SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS notification: {e}")
        return False

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f"₹{amount:.2f}"

def notify_new_expense(expense_user, expense_data):
    """Notify other users about a new expense"""
    notification_count = 0
    
    # Format expense amount
    total_amount = format_currency(expense_data["total"])
    
    # Create expense categories summary
    categories_list = ", ".join(expense_data["expenses"].keys())
    
    # Create message
    timestamp = datetime.datetime.now().strftime("%d-%b %H:%M")
    message = f"[Expense Tracker] {timestamp}: {expense_user} added a new expense of {total_amount} for {categories_list}."
    
    # Get users to notify from database
    users_to_notify = db_manager.get_users_to_notify_for_new_expense(expense_user)
    
    # Send notifications
    for username, phone_number in users_to_notify:
        if send_sms_notification(phone_number, message):
            notification_count += 1
            print(f"Notification sent to {username} about new expense from {expense_user}")
    
    return notification_count

def notify_status_change(expense_user, expense_data, new_status):
    """Notify users about expense status changes"""
    notification_count = 0
    
    # Format expense amount
    total_amount = format_currency(expense_data["total"])
    
    # Create message
    timestamp = datetime.datetime.now().strftime("%d-%b %H:%M")
    message = f"[Expense Tracker] {timestamp}: {expense_user} marked expense of {total_amount} as {new_status.upper()}."
    
    # Get users to notify from database
    users_to_notify = db_manager.get_users_to_notify_for_status_change(expense_user)
    
    # Send notifications
    for username, phone_number in users_to_notify:
        if send_sms_notification(phone_number, message):
            notification_count += 1
            print(f"Notification sent to {username} about status change from {expense_user}")
    
    return notification_count

def send_daily_summary(username=None):
    """Send daily summary of expenses to users"""
    notification_count = 0
    
    # Get all users from database
    session = db_manager.Session()
    try:
        # Query for all users with daily summary enabled
        users_with_prefs = (session.query(db_manager.User, db_manager.NotificationPreference)
                           .join(db_manager.NotificationPreference)
                           .filter(db_manager.NotificationPreference.notify_daily_summary == 1)
                           .filter(db_manager.NotificationPreference.phone_number.isnot(None)))
        
        # Filter to specific user if requested
        if username:
            users_with_prefs = users_with_prefs.filter(db_manager.User.username == username)
            
        users_with_prefs = users_with_prefs.all()
        
        # Generate and send summaries
        for user, prefs in users_with_prefs:
            # Get summary data for user
            summary = db_manager.get_user_summary(user.username)
            
            # Create message
            today = datetime.datetime.now().strftime("%d %b, %Y")
            message = f"[Expense Tracker] Daily Summary ({today})\n"
            message += f"Total Expenses: {format_currency(summary['total_spent'])}\n"
            message += f"Unpaid: {format_currency(summary['unpaid'])}\n"
            message += f"Paid: {format_currency(summary['paid'])}\n"
            message += f"Total Entries: {summary['entry_count']}"
            
            # Send notification
            if send_sms_notification(prefs.phone_number, message):
                notification_count += 1
                print(f"Daily summary sent to {user.username}")
            
    finally:
        session.close()
    
    return notification_count