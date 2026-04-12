import time
import logging
import yaml
import os
import random
from datetime import datetime
from database.database import Database
from notifier.email_notifier import EmailNotifier
from notifier.telegram_notifier import TelegramNotifier
from scraper.immoscout_scraper import ImmobilienScout24Scraper
from scraper.immonet_scraper import ImmonetScraper
from scraper.wggesucht_scraper import WGGesuchtScraper
from scraper.ebay_scraper import EbayScraper
from scraper.imap_scraper import IMAPScraper
from webapp.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs.txt'),
        logging.StreamHandler()
    ]
)

def load_config():
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        # Environment Variables überschreiben config.yaml
        # (Passwörter nicht auf GitHub → in Railway Variables setzen)
        if os.environ.get('FRIEND_EMAIL'):
            config['email']['friend_email'] = os.environ.get('FRIEND_EMAIL')
        if os.environ.get('FRIEND_PASSWORD'):
            config['email']['friend_password'] = os.environ.get('FRIEND_PASSWORD')
        if os.environ.get('IMAP_EMAIL'):
            config.setdefault('imap', {})['email'] = os.environ.get('IMAP_EMAIL')
        if os.environ.get('IMAP_PASSWORD'):
            config.setdefault('imap', {})['password'] = os.environ.get('IMAP_PASSWORD')
            config['telegram']['bot_token'] = os.environ.get('TELEGRAM_TOKEN')
        if os.environ.get('TELEGRAM_CHAT_ID'):
            config['telegram']['chat_id'] = os.environ.get('TELEGRAM_CHAT_ID')

        logging.info(f"Config geladen: max_price={config.get('max_price')}, "
                     f"districts={len(config.get('districts', []))} Stadtteile")
        return config
    except Exception as e:
        logging.error(f"Fehler beim Laden der Config: {e}")
        return None

def run_monitoring_loop(config, db):
    email_notifier    = EmailNotifier(config.get('email', {}))
    telegram_notifier = TelegramNotifier(config.get('telegram', {}))

    max_price         = config.get('max_price', 700.0)
    allowed_districts = config.get('districts', [])

    scrapers = [
        ImmobilienScout24Scraper(max_price=max_price, allowed_districts=allowed_districts),
        ImmonetScraper(max_price=max_price, allowed_districts=allowed_districts),
        WGGesuchtScraper(max_price=max_price, allowed_districts=allowed_districts),
        EbayScraper(max_price=max_price, allowed_districts=allowed_districts),
    ]

    # IMAP-Scraper nur hinzufügen wenn konfiguriert
    imap_config = config.get('imap', {})
    if imap_config.get('email') and imap_config.get('password'):
        scrapers.append(IMAPScraper(
            imap_config=imap_config,
            max_price=max_price,
            allowed_districts=allowed_districts,
        ))
        logging.info("IMAPScraper aktiviert – liest Alert-Emails von ImmoScout/Immonet/Immowelt.")
    else:
        logging.info("IMAPScraper nicht konfiguriert (imap.email / imap.password fehlt).")

    logging.info("Apartment-Monitor gestartet.")

    while True:
        try:
            all_listings = []
            for scraper in scrapers:
                try:
                    listings = scraper.get_listings()
                    all_listings.extend(listings)
                    logging.info(f"Retrieved {len(listings)} listings from {scraper.__class__.__name__}")
                except Exception as e:
                    logging.error(f"Fehler beim Scrapen ({scraper.__class__.__name__}): {e}")
                    continue

            new_listings = []
            for listing in all_listings:
                if db.add_listing(listing['title'], listing['price'],
                                  listing['district'], listing['url']):
                    new_listings.append(listing)

            if new_listings:
                logging.info(f"{len(new_listings)} neue Listings gefunden – sende Benachrichtigungen...")
                for listing in new_listings:
                    email_ok = email_notifier.send_notification(listing)
                    telegram_notifier.send_notification(listing)
                    if email_ok:
                        db.mark_as_notified(listing['url'])
            else:
                logging.info("Keine neuen Listings gefunden.")

            poll_min      = config.get('polling_interval_min', 60)
            poll_max      = config.get('polling_interval_max', 600)
            poll_interval = random.randint(poll_min, poll_max)
            logging.info(f"Warte {poll_interval} Sekunden bis zum nächsten Poll...")
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            logging.info("Monitor gestoppt.")
            break
        except Exception as e:
            logging.error(f"Unerwarteter Fehler: {e}")
            time.sleep(60)

def main():
    config = load_config()
    if not config:
        logging.error("Konnte Config nicht laden. Abbruch.")
        return

    # Datenbankpfad: Railway Volume falls vorhanden, sonst lokal
    db_path = os.environ.get('DB_PATH', config.get('database_path', 'database.db'))
    db = Database(db_path)

    app = create_app(db_path)

    from threading import Thread
    port = int(os.environ.get('PORT', 5000))
    web_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False))
    web_thread.daemon = True
    web_thread.start()
    logging.info(f"Web-Dashboard läuft auf Port {port}")

    run_monitoring_loop(config, db)

if __name__ == "__main__":
    main()
