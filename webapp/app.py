from flask import Flask, render_template, jsonify
from database.database import Database
import os

def create_app(db_path: str):
    app = Flask(__name__)
    
    # Initialize database
    db = Database(db_path)
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        all_listings = db.get_all_listings()
        notified_listings = db.get_notified_listings()
        new_listings = db.get_new_listings()
        
        return render_template('index.html', 
                             all_listings=all_listings,
                             notified_listings=notified_listings,
                             new_listings=new_listings)
    
    @app.route('/api/listings')
    def api_listings():
        """API endpoint for all listings"""
        all_listings = db.get_all_listings()
        return jsonify(all_listings)
    
    @app.route('/api/new_listings')
    def api_new_listings():
        """API endpoint for new listings"""
        new_listings = db.get_new_listings()
        return jsonify(new_listings)
    
    @app.route('/api/notified_listings')
    def api_notified_listings():
        """API endpoint for notified listings"""
        notified_listings = db.get_notified_listings()
        return jsonify(notified_listings)
    
    return app
