# SprintMind API

AI-powered product priority synthesis engine built with FastAPI, PostgreSQL, and IBM WatsonX.

## Features

- **AI-Powered Analysis**: Synthesizes user research, JIRA backlog, and analytics data using IBM WatsonX
- **Feature Recommendations**: Generates prioritized feature recommendations with supporting evidence
- **Challenge Identification**: Identifies potential challenges for each recommended feature
- **Feedback System**: Collect and store user feedback on analysis results
- **History Tracking**: View past analyses by user email
- **Rate Limiting**: 3 analyses per 60 seconds per user
- **Comprehensive Testing**: Full test suite with pytest

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **AI**: IBM WatsonX
- **ORM**: SQLAlchemy
- **Testing**: pytest
- **Deployment**: Railway

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL database
- IBM WatsonX API credentials

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd sprintmind-backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
DATABASE_URL=postgresql://user:password@host:port/database
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

6. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check with database connectivity test
- `GET /docs` - Interactive API documentation

### Analysis

- `POST /api/v1/analyze` - Analyze user research data
  - Rate limited: 3 requests per 60 seconds per email
  - Timeout: 120 seconds

### Feedback

- `POST /api/v1/feedback` - Submit feedback for an analysis

### History

- `GET /api/v1/history/{user_email}` - Get analysis history for a user

## Deployment Instructions

### Step 1: Create Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Navigate to **Settings** > **Database** > **Connection string** > **URI**
3. Copy the connection string - this is your `DATABASE_URL`
4. The format will be: `postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres`

### Step 2: Install Railway CLI

```bash
npm install -g @railway/cli
```

Then login to Railway:
```bash
railway login
```

### Step 3: Initialize and Deploy

In your project directory, run:

```bash
railway init
```

Then deploy:
```bash
railway up
```

### Step 4: Configure Environment Variables

In the Railway dashboard, go to your project's **Variables** section and add:

```
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
DATABASE_URL=your_supabase_connection_string
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-url.replit.app
```

### Step 5: Test Your Deployment

1. Get your deployment URL from the Railway dashboard
2. Test the health endpoint:

```bash
curl https://your-railway-url/health
```

Expected response:
```json
{
  "status": "ok",
  "environment": "production",
  "database": "connected"
}
```

3. Access the API documentation at: `https://your-railway-url/docs`

## Project Structure

```
sprintmind-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── pipeline.py          # AI analysis pipeline
│   └── routers/
│       ├── __init__.py
│       ├── analyze.py       # Analysis endpoints
│       ├── feedback.py      # Feedback endpoints
│       └── history.py       # History endpoints
├── tests/
│   ├── test_analyze.py      # Analysis tests
│   └── test_feedback.py     # Feedback tests
├── init_db.py               # Database initialization
├── requirements.txt         # Python dependencies
├── Procfile                 # Deployment configuration
├── railway.toml             # Railway configuration
├── .env                     # Environment variables (local)
└── README.md               # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WATSONX_API_KEY` | IBM WatsonX API key | Yes |
| `WATSONX_PROJECT_ID` | IBM WatsonX project ID | Yes |
| `WATSONX_URL` | IBM WatsonX API URL | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `ENVIRONMENT` | Environment (development/production) | No (default: development) |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | No (default: http://localhost:3000) |

## Database Schema

### Analysis Table
- `id` (UUID, Primary Key)
- `created_at` (Timestamp)
- `user_email` (String)
- `raw_interviews` (Text)
- `raw_jira` (Text)
- `raw_analytics` (Text)
- `output_json` (JSON)
- `processing_time_ms` (Integer)
- `feedback_score` (Integer, nullable)
- `feedback_text` (Text, nullable)

### Session Table
- `id` (UUID, Primary Key)
- `user_email` (String)
- `created_at` (Timestamp)
- `last_active` (Timestamp, nullable)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

---

Made with ❤️ by Bob