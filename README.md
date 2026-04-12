
# Apartment Monitoring System for Hamburg

A production-ready apartment monitoring system that continuously monitors rental listings in Hamburg, Germany.

## Features

- Monitors multiple real estate platforms (Immobilienscout24, Immonet, WG-Gesucht, eBay Kleinanzeigen)
- Filters by maximum rent (700 EUR) and specific Hamburg districts
- Sends email and Telegram notifications for new listings
- Web dashboard to view all listings
- SQLite database for persistent storage
- Configurable through YAML file
- 24/7 monitoring with retry logic
- Optimized for low resource usage

## Setup Instructions

### Prerequisites

1. Ubuntu server (Oracle Cloud free tier recommended)
2. Python 3.7+
3. pip

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd apartment-monitor
