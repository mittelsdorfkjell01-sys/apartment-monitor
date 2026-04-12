import imaplib
import email
import logging
import re
from email.header import decode_header
from typing import List, Dict, Optional
from scraper.base_scraper import BaseScraper


class IMAPScraper(BaseScraper):
   

    def __init__(self, imap_config: Dict, session=None,
                 max_price: float = 700.0, allowed_districts=None):
        super().__init__("", session, max_price, allowed_districts)
        self.imap_email    = imap_config.get('email', '')
        self.imap_password = imap_config.get('password', '')
        self.imap_server   = imap_config.get('server', 'imap.gmail.com')
        self.imap_port     = imap_config.get('port', 993)
        self.senders       = imap_config.get('senders', [
            'no-reply@immobilienscout24.de',
            'noreply@immonet.de',
            'noreply@immowelt.de',
        ])

    def is_configured(self) -> bool:
        return bool(self.imap_email and self.imap_password)

    # ------------------------------------------------------------------ #
    #  Hauptmethode                                                        #
    # ------------------------------------------------------------------ #

    def get_listings(self) -> List[Dict]:
        if not self.is_configured():
            logging.error("IMAPScraper: E-Mail oder Passwort fehlt in der Config.")
            return []

        listings = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.imap_email, self.imap_password)
            mail.select('INBOX')

            for sender in self.senders:
                found = self._fetch_from_sender(mail, sender)
                listings.extend(found)
                logging.info(f"IMAP [{sender}]: {len(found)} neue Listings gefunden.")

            mail.logout()
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP Login fehlgeschlagen: {e}")
        except Exception as e:
            logging.error(f"IMAPScraper Fehler: {e}")

        return listings

    # ------------------------------------------------------------------ #
    #  Interne Methoden                                                    #
    # ------------------------------------------------------------------ #

    def _fetch_from_sender(self, mail: imaplib.IMAP4_SSL, sender: str) -> List[Dict]:
        """Holt alle UNGELESENEN Mails von 'sender' und parst sie."""
        listings = []
        try:
            # Nur ungelesene Mails vom jeweiligen Absender suchen
            status, data = mail.search(None, f'(UNSEEN FROM "{sender}")')
            if status != 'OK' or not data[0]:
                return []

            mail_ids = data[0].split()
            logging.info(f"IMAP: {len(mail_ids)} ungelesene Mails von {sender}")

            for mail_id in mail_ids:
                try:
                    status, msg_data = mail.fetch(mail_id, '(RFC822)')
                    if status != 'OK':
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    body = self._get_body(msg)
                    source = self._sender_to_source(sender)
                    parsed = self._parse_listings_from_body(body, source)
                    listings.extend(parsed)

                    # Mail als gelesen markieren, damit sie nicht doppelt verarbeitet wird
                    mail.store(mail_id, '+FLAGS', '\\Seen')

                except Exception as e:
                    logging.error(f"Fehler beim Verarbeiten einer Mail von {sender}: {e}")
                    continue

        except Exception as e:
            logging.error(f"IMAP Suche fehlgeschlagen für {sender}: {e}")

        return listings

    def _get_body(self, msg: email.message.Message) -> str:
        """Extrahiert den Text-Body einer E-Mail (plain text bevorzugt)."""
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
                elif ctype == 'text/html' and not body:
                    # HTML-Fallback: Tags entfernen
                    charset = part.get_content_charset() or 'utf-8'
                    html = part.get_payload(decode=True).decode(charset, errors='replace')
                    body = re.sub(r'<[^>]+>', ' ', html)
        else:
            charset = msg.get_content_charset() or 'utf-8'
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors='replace')
                if msg.get_content_type() == 'text/html':
                    body = re.sub(r'<[^>]+>', ' ', body)
        return body

    def _parse_listings_from_body(self, body: str, source: str) -> List[Dict]:
        """
        Parst mehrere Listings aus einem E-Mail-Body.
        Unterstützt ImmoScout24, Immonet und Immowelt Alert-Formate.
        """
        listings = []

        # ---- URLs extrahieren ----
        # ImmoScout:  https://www.immobilienscout24.de/expose/XXXXXXX
        # Immonet:    https://www.immonet.de/angebot/XXXXXXX
        # Immowelt:   https://www.immowelt.de/expose/XXXXXXX
        url_patterns = [
            r'https://www\.immobilienscout24\.de/expose/\d+[^\s"<>]*',
            r'https://www\.immonet\.de/angebot/\d+[^\s"<>]*',
            r'https://www\.immowelt\.de/expose/[A-Za-z0-9]+[^\s"<>]*',
        ]

        urls = []
        for pattern in url_patterns:
            urls.extend(re.findall(pattern, body))
        urls = list(dict.fromkeys(urls))  # Duplikate entfernen, Reihenfolge behalten

        if not urls:
            logging.warning(f"IMAP [{source}]: Keine Listing-URLs in Mail gefunden.")
            return []

        # ---- Body in Blöcke um jede URL aufteilen ----
        # Wir suchen Preis und Titel in der Nähe der URL
        for url in urls:
            url_pos = body.find(url)
            # Kontext: 500 Zeichen vor und nach der URL
            context = body[max(0, url_pos - 500): url_pos + len(url) + 200]

            title    = self._extract_title(context, source)
            price    = self._extract_price_from_text(context)
            district = self._extract_district(context)

            if not self.is_valid_price(price) and price > 0:
                continue
            if district and not self.is_valid_district(district):
                continue

            listings.append({
                'title':    title or f'Angebot von {source}',
                'price':    price,
                'district': district or 'Unbekannt',
                'url':      url,
                'source':   source,
            })

        return listings

    # ------------------------------------------------------------------ #
    #  Extraktion                                                          #
    # ------------------------------------------------------------------ #

    def _extract_title(self, text: str, source: str) -> str:
        """Versucht einen Titel aus dem Kontext zu extrahieren."""
        # Typische Muster in Alert-Mails:
        # ImmoScout: "2-Zimmer-Wohnung in Hamburg-Winterhude"
        # Immonet:   "Schöne 2-ZKB Wohnung..."
        patterns = [
            r'(\d[\-\s]?Zimmer[^\n\r]{5,60})',
            r'(\d[\-\s]?ZKB[^\n\r]{5,60})',
            r'(\d[\-\s]?Raum[^\n\r]{5,60})',
            r'((?:Wohnung|Apartment|Studio|Loft)[^\n\r]{5,60})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:120]
        return ''

    def _extract_price_from_text(self, text: str) -> float:
        """Extrahiert den Mietpreis aus einem Textblock."""
        patterns = [
            r'(\d{3,4}[.,]\d{2})\s*(?:€|EUR)',
            r'(\d{3,4})\s*(?:€|EUR)',
            r'Kaltmiete[:\s]+(\d{3,4})',
            r'Warmmiete[:\s]+(\d{3,4})',
            r'Miete[:\s]+(\d{3,4})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    raw = m.group(1).replace('.', '').replace(',', '.')
                    return float(raw)
                except ValueError:
                    continue
        return 0.0

    def _extract_district(self, text: str) -> str:
        """Versucht einen Hamburger Stadtteil aus dem Text zu erkennen."""
        # Häufige Muster: "in Hamburg-Winterhude", "Hamburg Eimsbüttel"
        m = re.search(r'Hamburg[- ]([A-ZÄÖÜ][a-zäöüß\-]+)', text)
        if m:
            return m.group(1)

        # Direkten Stadtteilnamen suchen
        if self.allowed_districts:
            for district in self.allowed_districts:
                if district.lower() in text.lower():
                    return district
        return ''

    @staticmethod
    def _sender_to_source(sender: str) -> str:
        mapping = {
            'immobilienscout24': 'ImmoScout24',
            'immonet':           'Immonet',
            'immowelt':          'Immowelt',
        }
        for key, name in mapping.items():
            if key in sender.lower():
                return name
        return 'Unbekannt'
