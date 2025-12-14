# LinkedIn Insights Microservice

A comprehensive FastAPI-based microservice for fetching, storing, and analyzing LinkedIn Page insights.

## Features

### Mandatory Features ✅
- **LinkedIn API Integration**: Fetch page details, posts, comments, and employees
- **Database Storage**: MySQL with proper relationships between entities
- **REST API Endpoints**:
  - Get pages with filters (follower range, name search, industry)
  - Get followers/following of a page
  - Get recent 10-15 posts
  - Pagination on all list endpoints
- **Postman Collection**: Complete API documentation

### Bonus Features ✅
- **AI Summary**: ChatGPT-powered analysis of pages
- **Async Programming**: Full async/await support throughout
- **S3 Storage**: Clone profile pictures and media to AWS S3
- **Redis Caching**: 5-minute TTL caching layer
- **Docker**: Complete containerization

## Quick Start

### 1. Clone and Setup

```bash
cd linkedin-insights-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```env
# LinkedIn API (from https://www.linkedin.com/developers/)
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# OpenAI (from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your-bucket
```

### 3. Run with Docker (Recommended)

```bash
docker-compose up -d
```

This starts:
- API server on http://localhost:8000
- MySQL on localhost:3306
- Redis on localhost:6379
- Adminer (DB admin) on http://localhost:8080

### 4. Run Locally (Alternative)

```bash
# Start MySQL and Redis first
# Then run:
python run.py
```

## API Documentation

### Interactive Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Postman Collection
Import `postman_collection.json` into Postman for complete API testing.

## API Endpoints

### Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/pages/` | List pages with filters |
| GET | `/api/v1/pages/{page_id}` | Get page details |
| POST | `/api/v1/pages/{page_id}/refresh` | Refresh from LinkedIn |
| GET | `/api/v1/pages/{page_id}/posts` | Get page posts |
| GET | `/api/v1/pages/{page_id}/followers` | Get followers/following |

**Filter Examples:**
```
GET /api/v1/pages/?min_followers=20000&max_followers=40000
GET /api/v1/pages/?name=google&industry=Technology
GET /api/v1/pages/?page=2&page_size=20
```

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/posts/` | List all posts |
| GET | `/api/v1/posts/{post_id}` | Get post with comments |
| GET | `/api/v1/posts/recent/{page_id}` | Get recent 10-15 posts |
| GET | `/api/v1/posts/{post_id}/comments` | Get post comments |

### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/employees/` | List employees |
| GET | `/api/v1/employees/{linkedin_id}` | Get employee details |
| GET | `/api/v1/employees/by-page/{page_id}` | Get employees by page |

### AI Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/summary/{page_id}` | Generate AI summary |
| GET | `/api/v1/ai/quick-summary/{page_id}` | Get quick stats |
| POST | `/api/v1/ai/compare` | Compare multiple pages |

## Database Schema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Pages     │────<│   Posts     │────<│  Comments   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id          │     │ id          │     │ id          │
│ page_id     │     │ post_id     │     │ comment_id  │
│ linkedin_id │     │ page_id(FK) │     │ post_id(FK) │
│ name        │     │ text        │     │ text        │
│ followers   │     │ likes       │     │ author_name │
│ ...         │     │ ...         │     │ ...         │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       │
       ▼
┌─────────────┐
│  Employees  │
├─────────────┤
│ id          │
│ linkedin_id │
│ page_id(FK) │
│ full_name   │
│ ...         │
└─────────────┘
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_pages.py -v
```

## Project Structure

```
linkedin-insights-backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── pages.py
│   │       ├── posts.py
│   │       ├── employees.py
│   │       └── ai_summary.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── cache.py
│   ├── models/
│   │   ├── page.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── employee.py
│   ├── schemas/
│   │   └── ...
│   ├── services/
│   │   ├── linkedin_service.py
│   │   ├── storage_service.py
│   │   └── ai_service.py
│   └── main.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── postman_collection.json
```

## LinkedIn API Setup

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. Request the following permissions:
   - `r_organization_social`
   - `r_organization_admin`
   - `rw_organization_admin`
4. Get your access token
5. Add credentials to `.env`

## Caching

Redis caching is implemented with 5-minute TTL:
- Page details
- Post lists
- AI summaries (30-minute TTL)

Cache is automatically invalidated on refresh operations.

## Storage

Profile pictures and post media are cloned to S3:
- Original URLs are preserved
- S3 URLs are used for serving
- Organized by page_id/post_id

## License

MIT License
