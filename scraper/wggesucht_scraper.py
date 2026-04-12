import logging
from bs4 import BeautifulSoup
from typing import List, Dict
from scraper.base_scraper import BaseScraper


class WGGesuchtScraper(BaseScraper):
    def __init__(self, session=None, max_price: float = 620.0, allowed_districts=None):
        super().__init__("https://www.wg-gesucht.de", session, max_price, allowed_districts)
        self.search_url = "https://www.wg-gesucht.de/wohnungen-in-hamburg.12.2.1.0.html"

    def get_listings(self) -> List[Dict]:
        listings = []
        try:
            response = self.get_page(self.search_url)
            if not response:
                return listings

            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_='offer_list_item')

            for item in items:
                try:
                    title_elem = item.find('h3', class_='truncate_title')
                    if not title_elem:
                        continue
                    link = title_elem.find('a')
                    if not link:
                        continue
                    title = link.get_text(strip=True)
                    url   = self.base_url + link['href']

                    price_elem = item.find('div', class_='col-xs-3')
                    price_text = price_elem.get_text(strip=True) if price_elem else '0'
                    price      = self.parse_price(price_text)

                    district_elem = item.find('span', class_='col-xs-11')
                    district      = district_elem.get_text(strip=True) if district_elem else 'Unknown'

                    if self.is_valid_price(price) and self.is_valid_district(district):
                        listings.append({
                            'title':    title,
                            'price':    price,
                            'district': district,
                            'url':      url,
                            'source':   'WG-Gesucht',
                        })

                except Exception as e:
                    logging.error(f"Fehler beim Parsen eines WG-Gesucht-Listings: {e}")
                    continue

        except Exception as e:
            logging.error(f"Fehler beim Abrufen von WG-Gesucht: {e}")

        return listings
