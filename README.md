# Socio Connect — Societal Innovation Collaboration Portal

A civic-tech platform connecting citizens, universities, industry, and government to solve community problems through collaborative innovation.

## Quick Start (Development)

### Prerequisites
- Node.js 20+
- Python 3.12+
- PostgreSQL (or Neon cloud DB)
- Docker & Docker Compose (for containerized deployment)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET, etc.

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file and configure
cp .env.example .env
# Edit .env with VITE_API_URL and VITE_GOOGLE_MAPS_API_KEY

# Start development server
npm run dev
```

### 3. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment (Production)

### Prerequisites
- Docker & Docker Compose
- Domain name with SSL certificates (for HTTPS)

### 1. Configure Environment

```bash
# Copy and edit environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with production values:
# - DATABASE_URL (Neon or local PostgreSQL)
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - CORS_ORIGINS (your frontend domain(s))
# - CLOUDFLARE_* (for AI features)
# - EMAIL_* (for OTP emails)

# Edit frontend/.env with production values:
# - VITE_API_URL=https://api.your-domain.com/api/v1
# - VITE_GOOGLE_MAPS_API_KEY=your-api-key
```

### 2. SSL Certificates (for HTTPS)

```bash
mkdir -p nginx/ssl
# Place your cert.pem and key.pem in nginx/ssl/
# Or use Let's Encrypt with certbot
```

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### 4. Access Production

- Application: https://your-domain.com
- API: https://api.your-domain.com/api/v1
- Health check: https://your-domain.com/health

---

## CORS Configuration

The backend CORS middleware is configured in `backend/app/main.py` to handle multiple deployment scenarios:

```python
# CORS origins from environment (comma-separated)
cors_origins = settings.cors_origins_list

# In production, if no explicit origins, allow all
if not cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### Common CORS Issues & Fixes

| Issue | Solution |
|-------|----------|
| `Access-Control-Allow-Origin` missing | Ensure `CORS_ORIGINS` in backend `.env` includes your frontend domain |
| `Credentials mode is 'include'` but origin is `*` | Set explicit origins in `CORS_ORIGINS`, not `*` |
| Works locally but fails on Vercel/Netlify | Frontend `VITE_API_URL` must point to backend domain; backend `CORS_ORIGINS` must include frontend domain |
| Cookies not sent cross-origin | Use `allow_credentials=True` and same-site cookies (configured) |

---

## Environment Variables Reference

### Backend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (Neon requires `sslmode=require`) |
| `JWT_SECRET` | Yes | 32+ char random string for JWT signing |
| `JWT_ALGORITHM` | No | Default: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: `60` |
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed frontend origins |
| `CLOUDFLARE_ACCOUNT_ID` | No | For AI categorization/transcription |
| `CLOUDFLARE_AI_API_KEY` | No | For AI categorization/transcription |
| `CLOUDFLARE_AI_MODEL` | No | Default: `@cf/moonshotai/kimi-k2.7-code` |
| `EMAIL_HOST` | No | SMTP host (default: smtp.gmail.com) |
| `EMAIL_PORT` | No | SMTP port (default: 587) |
| `EMAIL_USER` | No | Sender email address |
| `EMAIL_PASS` | No | Gmail app password (not normal password) |
| `EMAIL_FROM_NAME` | No | Default: "Socio Connect" |

### Frontend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API base URL |
| `VITE_GOOGLE_MAPS_API_KEY` | Yes | Google Maps JavaScript API key |

---

## Project Structure

```
societal-innovation-portal/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/            # API routers (auth, problems, evidence, AI, etc.)
│   │   ├── core/              # Config, security, database, dependencies
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic (AI, routing, storage, etc.)
│   │   ├── ml/                # Taxonomy, prompts for AI
│   │   └── utils/             # Helpers
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── api/               # Axios client & API functions
│   │   ├── components/        # Reusable UI components
│   │   │   ├── ui/            # Design system (Button, Card, Badge, etc.)
│   │   │   ├── common/        # Navbar, ProtectedRoute
│   │   │   ├── forms/         # VoiceRecorder, LocationPicker
│   │   │   ├── map/           # Map components
│   │   │   └── charts/        # Recharts components
│   │   ├── context/           # React context (Auth)
│   │   ├── pages/             # Page components by role
│   │   ├── routes/            # Route configuration
│   │   └── styles/            # Tailwind + custom CSS
│   ├── Dockerfile
│   ├── nginx.conf             # Frontend nginx config
│   ├── package.json
│   └── .env
├── nginx/                      # Root nginx (reverse proxy)
│   └── nginx.conf
├── docker-compose.yml          # Full stack deployment
└── README.md
```

---

## Features Implemented

### Phase 1-2: Foundation & Citizen Flow
- ✅ User authentication (JWT + OTP email verification)
- ✅ Role-based access control (Citizen, Student, Faculty, University Admin, Industry, Government, Admin)
- ✅ Problem submission with multi-step form
- ✅ Voice recorder with browser-based transcription (Puter.js)
- ✅ Evidence upload (image, video, audio, documents)
- ✅ Google Maps location picker with geocoding

### Phase 3: AI Pipeline
- ✅ AI categorization (Cloudflare Workers AI + heuristic fallback)
- ✅ Local sklearn classifier (12-category, offline, ~5ms — active when `category_classifier.joblib` is present)
- ✅ LoRA fine-tune path (Cloudflare BYO LoRA / Modal) with shadow-mode logging, safe defaults
- ✅ Classification status endpoint (`GET /classification/status`) + accuracy metrics
- ✅ Priority scoring (critical/high/medium/low)
- ✅ Duplicate detection (pgvector cosine similarity + Jaccard fallback)
- ✅ Routing engine (HEIs see all, Industry tag-matched)

### Phase 4: University Flow
- ✅ University dashboard (all problems feed)
- ✅ Team formation with faculty mentor
- ✅ Proposal editor with rich text + attachments

### Phase 5: Industry Flow
- ✅ Industry dashboard (tag-matched problems + proposals)
- ✅ Domain tag management
- ✅ Collaboration workspace (milestones, deliverables, IP)

### Phase 6: Government Dashboard
- ✅ KPI cards (problems, resolved, collaborations, patents, startups)
- ✅ Analytics charts (district, category, priority, trends)
- ✅ Impact reports with CSV/PDF export
- ✅ Heatmap of problems by district

### Phase 7: Admin & Polish
- ✅ User management
- ✅ Moderation queue
- ✅ AI configuration
- ✅ Broadcast notifications
- ✅ Audit logging

---

## API Documentation

- **Local**: http://localhost:8000/docs (Swagger UI)
- **Local**: http://localhost:8000/redoc (ReDoc)

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Login (returns OTP) |
| `/auth/login/verify` | POST | Verify OTP, get JWT |
| `/auth/me` | GET | Get current user |
| `/problems` | POST | Create problem (citizen) |
| `/problems` | GET | List problems (role-filtered) |
| `/problems/{id}/evidence` | POST | Upload evidence |
| `/ai/extract-tags` | POST | AI tag extraction |
| `/ai/analyze/{id}` | POST | Run full AI pipeline |
| `/classification/status` | GET | Provider health (gov/admin) — confirms prod wiring |
| `/classification/metrics` | GET | Per-category accuracy (gov/admin) |
| `/classification/feedback` | POST | Submit classification correction |
| `/government/analytics` | GET | Dashboard analytics |
| `/government/impact-reports` | GET | Exportable impact reports |

---

## Troubleshooting

### Backend won't start
- Check `DATABASE_URL` format (Neon needs `postgresql+psycopg://...`)
- Ensure `sslmode=require` for Neon
- Run `alembic upgrade head` for migrations

### Frontend can't connect to backend
- Verify `VITE_API_URL` in frontend `.env`
- Check backend `CORS_ORIGINS` includes frontend origin
- Check browser Network tab for CORS errors

### CORS errors in production
- Backend `CORS_ORIGINS` must include exact frontend domain (with protocol)
- Example: `CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com`
- Don't use `*` with `allow_credentials=True`

### AI features not working
- Set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AI_API_KEY`
- Check Cloudflare Workers AI quota
- Heuristic fallback works without AI keys
- Local sklearn path needs `scikit-learn` + `scipy` installed and `backend/app/ml/category_classifier.joblib` present (committed); check `GET /classification/status` as gov/admin to see which provider is actually active in a deployment
- LoRA path is off by default (`LORA_PROVIDER=off`); enable only after probe ≥80% + real-data eval, keep `LORA_SHADOW_MODE=True` until cutover

### Database connection issues
- For Neon: ensure IP allowlist includes your server IP (or 0.0.0.0/0 for testing)
- Check `sslmode=require` in connection string
- Verify PostgreSQL version supports pgvector

---

## License

MIT License — feel free to use for civic tech projects.