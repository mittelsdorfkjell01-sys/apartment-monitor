import logging
from typing import List, Dict
from scraper.base_scraper import BaseScraper


class ImmobilienScout24Scraper(BaseScraper):
    """
    ImmoScout24 blockiert alle automatischen Anfragen von Cloud-Servern.
    Dieser Scraper ist deaktiviert bis eine funktionierende Lösung gefunden wird.
    """
    def __init__(self, session=None, max_price: float = 700.0, allowed_districts=None):
        super().__init__("https://www.immobilienscout24.de", session, max_price, allowed_districts)

    def get_listings(self) -> List[Dict]:
        logging.info("ImmoScout24: Scraper deaktiviert (Cloud-IP blockiert).")
        return []
