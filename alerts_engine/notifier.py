import logging

class AlertSystem:
    """
    Centralized Alert and Notification Engine for CleanCity AI.
    Handles SMS, Email, and In-App Push notifications.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AlertSystem")

    def trigger_critical_alert(self, bin_location, fill_level):
        message = f"🚨 CRITICAL ALERT: Bin at {bin_location} is {fill_level}% full. Dispatching nearest vehicle."
        self.logger.warning(message)
        # Here you would integrate Twilio or SendGrid
        return {"status": "sent", "channel": "Push/SMS", "message": message}

    def notify_citizen(self, complaint_id, status):
        message = f"✅ CleanCity Update: Your complaint #{complaint_id} has been marked as {status}. Thank you for helping us stay clean!"
        self.logger.info(message)
        return {"status": "sent", "channel": "In-App", "message": message}

notifier = AlertSystem()
