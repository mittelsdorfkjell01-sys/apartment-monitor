import requests
import time
import random
import logging
from typing import List, Dict, Optional


class BaseScraper:
    def __init__(self, base_url: str, session: requests.Session = None,
                 max_price: float = 700.0, allowed_districts: List[str] = None):
        self.base_url = base_url
        self.session = session or requests.Session()
        self.max_price = max_price
        self.allowed_districts = allowed_districts or []
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.delay_min = 2
        self.delay_max = 5

    def _sleep(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def get_page(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                self._sleep()
                return response
            except requests.RequestException as e:
                logging.warning(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logging.error(f"Failed to fetch {url} after {retries} attempts")
                    return None

    def parse_price(self, price_str: str) -> float:
        try:
            cleaned = price_str.replace('.', '').replace(',', '.')
            price_clean = ''.join(c for c in cleaned if c.isdigit() or c == '.')
            return float(price_clean)
        except ValueError:
            return 0.0

    def is_valid_price(self, price: float) -> bool:
        return 0 < price <= self.max_price

    def is_valid_district(self, district: str, allowed_districts: List[str] = None) -> bool:
        districts = allowed_districts if allowed_districts is not None else self.allowed_districts
        if not districts:
            return True
        return any(d.lower() in district.lower() for d in districts)

    def get_listings(self) -> List[Dict]:
        raise NotImplementedError("Subclasses must implement get_listings method")
