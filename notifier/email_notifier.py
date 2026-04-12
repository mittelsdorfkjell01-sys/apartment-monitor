import logging
import os
from typing import Dict


class EmailNotifier:
    def __init__(self, config: Dict):
        self.to_email      = config.get('friend_email', '')
        self.from_email    = config.get('friend_email', '')  # Absender = Empfänger
        self.sendgrid_key  = os.environ.get('SENDGRID_API_KEY', '')

        if self.to_email:
            logging.info(f"EmailNotifier bereit: {self.to_email}")
        else:
            logging.error("EmailNotifier: Keine Email konfiguriert!")

        if not self.sendgrid_key:
            logging.error("EmailNotifier: SENDGRID_API_KEY fehlt in Railway Variables!")

    def is_configured(self) -> bool:
        return bool(self.to_email and self.sendgrid_key)

    def send_notification(self, listing: Dict) -> bool:
        if not self.is_configured():
            logging.error("Email kann nicht gesendet werden: Konfiguration unvollständig.")
            return False

        try:
            import urllib.request
            import json

            body = (
                f"Ey du dumme Pic, ich habe eine neue Wohnung für dich. Check das mal aus!\n\n"
                f"Titel:      {listing['title']}\n"
                f"Preis:      {listing['price']} EUR\n"
                f"Stadtteil:  {listing['district']}\n"
                f"Quelle:     {listing['source']}\n"
                f"Link:       {listing['url']}\n\n"
                f"Klick den Link und bewirb dich du fauler Gammler"
            )

            payload = json.dumps({
                "personalizations": [{"to": [{"email": self.to_email}]}],
                "from": {"email": self.from_email},
                "subject": f"🏠 Neue Wohnung: {listing['title']}",
                "content": [{"type": "text/plain", "value": body}]
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=payload,
                headers={
                    "Authorization": f"Bearer {self.sendgrid_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(req) as response:
                if response.status == 202:
                    logging.info(f"✅ Email gesendet: {listing['title']}")
                    return True
                else:
                    logging.error(f"❌ SendGrid Fehler: Status {response.status}")
                    return False

        except Exception as e:
            logging.error(f"❌ Email-Fehler: {e}")
            return False
