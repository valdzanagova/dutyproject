from slack_sdk import WebClient


class Slack:

    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def send_verify_code(self, email: str, code: str):
        try:
            username = email.split('@')[0] if email else ''
            message = f"Your confirmation code: *{code}*"
            self.client.chat_postMessage(channel=f"@{username}", text=message)
        except Exception: 
            return "An error has occurred. Please try again later."
