import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    district TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def add_listing(self, title: str, price: float, district: str, url: str) -> bool:
        """Add a new listing to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO listings (title, price, district, url)
                VALUES (?, ?, ?, ?)
            ''', (title, price, district, url))
            
            conn.commit()
            conn.close()
            
            # Return True if new record was inserted
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error adding listing to database: {e}")
            return False
    
    def mark_as_notified(self, url: str):
        """Mark a listing as notified"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE listings
                SET notified = TRUE
                WHERE url = ?
            ''', (url,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error marking listing as notified: {e}")
    
    def get_new_listings(self) -> List[Tuple]:
        """Get all listings that haven't been notified yet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, price, district, url, timestamp
                FROM listings
                WHERE notified = FALSE
                ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logging.error(f"Error fetching new listings: {e}")
            return []
    
    def get_all_listings(self) -> List[Tuple]:
        """Get all listings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, price, district, url, timestamp, notified
                FROM listings
                ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logging.error(f"Error fetching all listings: {e}")
            return []
    
    def get_notified_listings(self) -> List[Tuple]:
        """Get all notified listings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, price, district, url, timestamp
                FROM listings
                WHERE notified = TRUE
                ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logging.error(f"Error fetching notified listings: {e}")
            return []
