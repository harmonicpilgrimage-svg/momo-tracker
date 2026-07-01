# MoMo Tracker

A personal finance management app for tracking mobile money (MoMo) and bank transactions, particularly targeting users in Rwanda. Built with offline-first principles and intelligent SMS message parsing.

## Features

- 📱 **SMS Parsing**: Automatically parse and categorize bank/MoMo messages
- 📊 **Dashboard**: Real-time balance and spending overview
- 📈 **Analytics**: Visual breakdown of spending by category and time
- 💾 **Offline-First**: Works without internet using localStorage and service worker
- 🔄 **Sync**: Automatic sync with server when online
- 📥 **Export**: Download transactions as CSV
- 🎨 **Mobile-Optimized**: Responsive design for mobile-first usage

## Stack

- **Frontend**: HTML5, Vanilla JavaScript (no frameworks)
- **Backend**: Python 3 + Flask 3.0.0
- **Server**: Gunicorn 21.2.0
- **Database**: SQLite (local persistence)
- **Deployment**: Heroku-compatible (Procfile included)

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/harmonicpilgrimage-svg/momo-tracker.git
   cd momo-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   python db.py
   ```

4. **Run the server**
   ```bash
   python app.py
   ```

   Server runs on `http://localhost:8080`

5. **Run tests** (optional)
   ```bash
   pytest tests/ -v
   ```

### Environment Variables

Optional. Create a `.env` file in the project root:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///momo_tracker.db
```

If not set, defaults are used:
- `FLASK_ENV=development`
- `SECRET_KEY=dev-key` (use a secure key in production)
- `DATABASE_URL=sqlite:///momo_tracker.db`

## Project Structure

```
├── app.py                 Flask application (routes, API)
├── db.py                 Database initialization & schema
├── models.py             SQLAlchemy models (Transaction)
├── parser.py             SMS parsing logic
├── categories.py         Category auto-detection
├── logger.py             Logging configuration
├── requirements.txt      Python dependencies
├── Procfile              Heroku deployment config
├── index.html            Single-page application
├── static/
│   ├── style.css         Extracted CSS
│   ├── state.js          State management & sync
│   ├── ui.js             UI rendering & navigation
│   ├── charts.js         Chart rendering
│   ├── parser.js         Client-side parser (fallback)
│   ├── sw.js             Service worker (offline support)
│   └── manifest.json     PWA manifest
└── tests/
    ├── test_parser.py    Parser unit tests
    ├── test_categories.py Category detection tests
    └── conftest.py       Pytest configuration
```

## API Reference

### GET `/api/sync`

Fetch all transactions from server.

**Response:**
```json
{
  "txns": [
    {
      "id": "uuid",
      "type": "expense",
      "amount": 5000,
      "currency": "RWF",
      "category": "Food",
      "description": "Restaurant",
      "notes": "Lunch",
      "source": "MoMo",
      "created_at": "2024-01-15T10:30:00Z",
      "date": "2024-01-15T00:00:00Z"
    }
  ]
}
```

### POST `/api/sync`

Save transactions to server.

**Request:**
```json
{
  "txns": [
    { "id": "uuid", "type": "expense", "amount": 5000, ... }
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "count": 1
}
```

### POST `/api/parse`

Parse an SMS or bank message.

**Request:**
```json
{
  "message": "You have sent 5000 RWF to Jean 2507812345 on 01/15/2024"
}
```

**Response:**
```json
{
  "type": "expense",
  "amount": 5000,
  "currency": "RWF",
  "category": "Transfer",
  "source": "MoMo",
  "receiver": "2507812345",
  "date": "2024-01-15T00:00:00Z",
  "description": null,
  "parse_error": null
}
```

### POST `/api/transactions`

Add a new transaction (manual entry).

**Request:**
```json
{
  "type": "expense",
  "amount": 5000,
  "currency": "RWF",
  "category": "Food",
  "description": "Restaurant",
  "notes": "Lunch"
}
```

**Response:**
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET `/api/transactions`

List transactions with pagination and filtering.

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 50, max: 100)
- `type` (filter by "income" or "expense")
- `category` (filter by category)
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)

**Response:**
```json
{
  "txns": [...],
  "total": 150,
  "page": 1,
  "pages": 3
}
```

### DELETE `/api/transactions/:id`

Delete a transaction.

**Response:**
```json
{
  "ok": true
}
```

## Configuration

### Categories

Auto-detection patterns are defined in `categories.py`. Customize by editing the category regex patterns:

```python
CATEGORY_PATTERNS = {
    'Food': r'restaurant|food|eat|lunch|dinner|...',
    'Transport': r'taxi|moto|bus|fuel|...',
    # Add more categories as needed
}
```

### Service Worker & PWA

The app includes a service worker (`static/sw.js`) for offline support:

- Caches static assets (HTML, CSS, JS)
- Queues sync requests when offline
- Shows offline indicator when network unavailable

To customize cache strategy, edit `static/sw.js`.

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# Parser tests only
pytest tests/test_parser.py -v

# Category detection tests only
pytest tests/test_categories.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

Tests cover:
- Message parsing (various SMS formats, currency detection, date parsing)
- Category auto-detection
- Data validation
- API responses

## Deployment

### Heroku

```bash
# Create Heroku app
heroku create momo-tracker

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main

# Initialize database
heroku run python db.py

# View logs
heroku logs --tail
```

### Docker

```bash
docker build -t momo-tracker .
docker run -p 8080:8080 momo-tracker
```

### Manual Server

```bash
gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 30
```

## Data Backup

Export all transactions as CSV:

1. Open the app
2. Click **History** → **Export CSV**
3. Save `momo-transactions.csv`

To import back, paste the CSV content in the **Add** tab.

## Browser Compatibility

- Chrome/Edge 60+
- Firefox 55+
- Safari 11+
- Mobile browsers (iOS Safari, Chrome Mobile)

Requires:
- ES6 JavaScript support
- LocalStorage API
- Service Worker API (for offline support)

## Roadmap

- [ ] Budget tracking and alerts
- [ ] Recurring transaction templates
- [ ] Multi-user support with authentication
- [ ] Cloud backup (Google Drive, Dropbox)
- [ ] Mobile app (React Native)
- [ ] Open API for integrations

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for new code
4. Commit with clear messages
5. Push and open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the FAQ below

## FAQ

**Q: Where is my data stored?**
A: Locally in browser localStorage and on the server in SQLite database. No data is shared with third parties.

**Q: Can I access my data offline?**
A: Yes! The app works offline using a service worker. Changes sync when you're back online.

**Q: How do I reset my data?**
A: Browser: Open DevTools → Application → LocalStorage → Clear. Server: Contact admin or delete database.

**Q: Can I import data from another app?**
A: Yes. Export as CSV from your current app and paste the CSV in the MoMo Tracker import tool.

**Q: Is my data secure?**
A: Data is stored in your browser and on the server. Use HTTPS in production. Sensitive data is encrypted at rest.
