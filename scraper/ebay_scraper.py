import logging
import re
from bs4 import BeautifulSoup
from typing import List, Dict
from scraper.base_scraper import BaseScraper


class EbayScraper(BaseScraper):
    def __init__(self, session=None, max_price: float = 620.0, allowed_districts=None):
        super().__init__("https://www.kleinanzeigen.de", session, max_price, allowed_districts)
        self.search_url = (
            "https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/"
            "anzeige:angebote/c203l9409+wohnung_mieten.swap_s:nein"
        )

    def get_listings(self) -> List[Dict]:
        listings = []
        try:
            response = self.get_page(self.search_url)
            if not response:
                return listings

            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('article', class_='aditem')

            for item in items:
                try:
                    title_elem = item.find('a', class_='ellipsis')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    url   = self.base_url + title_elem['href']

                    price_elem = item.find('p', class_='aditem-main--middle--price-shipping--price')
                    price_text = price_elem.get_text(strip=True) if price_elem else '0'
                    price      = self.parse_price(price_text)

                    location_elem = item.find('div', class_='aditem-main--top--left')
                    district      = location_elem.get_text(strip=True) if location_elem else 'Unknown'
                    if ',' in district:
                        district = district.split(',')[-1].strip()

                    if self.is_valid_price(price) and self.is_valid_district(district):
                        listings.append({
                            'title':    title,
                            'price':    price,
                            'district': district,
                            'url':      url,
                            'source':   'Kleinanzeigen',
                        })

                except Exception as e:
                    logging.error(f"Fehler beim Parsen eines Kleinanzeigen-Listings: {e}")
                    continue

        except Exception as e:
            logging.error(f"Fehler beim Abrufen von Kleinanzeigen: {e}")

        return listings
