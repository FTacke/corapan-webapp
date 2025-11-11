# CO.RA.PAN Web App

Redesigned CO.RA.PAN portal with modular Flask backend, Vite-powered frontend, and separated media/data mounts.

## Repository

GitLab: `git@gitlab.uni-marburg.de:tackef/corapan-new.git`

## Structure

- `src/app/` - Flask application (routes, services, auth, models)
- `templates/` - Jinja templates (pages, partials)
- `static/` - CSS, JS, images (built via Vite)
- `config/` - Configuration files (keys excluded via .gitignore)
- `docs/` - Architecture, design system, roadmap
- `media/` - Audio files and transcripts (not in repo)
- `data/` - SQLite databases (not in repo)

## Environment

- Python 3.12+, Node 20+, FFmpeg, and libsndfile are required locally.
- Secrets (Flask key, JWT keys, hashed passwords) are provided via environment variables or mounted files.
- The `ALLOW_PUBLIC_TEMP_AUDIO` flag controls whether anonymous users can access generated snippets (they remain available to authenticated roles).

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
npm install
npm run build
FLASK_SECRET_KEY=change-me python -m src.app.main
```

## Documentation

**📚 [Start here: Documentation Index](docs/index.md)**

The documentation follows "Docs as Code" principles with a clear 8-category taxonomy:

- **[Concepts](docs/concepts/)** - Architecture, authentication flow
- **[How-To Guides](docs/how-to/)** - Step-by-step tutorials
- **[Reference](docs/reference/)** - API docs, database schema, technical specs
- **[Operations](docs/operations/)** - Deployment, CI/CD, security
- **[Design](docs/design/)** - Design system, tokens, accessibility
- **[Decisions](docs/decisions/)** - ADRs, roadmap
- **[Troubleshooting](docs/troubleshooting/)** - Common problems & solutions

### Quick Links
- **[Deployment Guide](docs/operations/deployment.md)** - Production server setup
- **[Architecture Overview](docs/concepts/architecture.md)** - Technical architecture
- **[Database Maintenance](docs/reference/database-maintenance.md)** - DB operations
- **[Troubleshooting](docs/troubleshooting/)** - Problem solutions by domain

## Features

### Core Search Capabilities
- **Basic Corpus Search**: Token-based search with morphological filters (form, lemma, POS)
  - Multi-token query support with wildcards
  - Country/region filtering with national/regional toggle
  - Speaker metadata filtering (type, sex, mode, discourse)
  - Results with context (left/match/right) and audio snippet links
  
- **Advanced Search** (BlackLab Integration): 
  - CQL (Corpus Query Language) support for complex queries
  - Pattern-based search (exact, lemma-based)
  - Server-side DataTables with pagination and filtering
  - CSV/TSV export with streaming (up to 50,000 rows)
  - Rate limiting and security hardening

### Audio & Visualization
- **Audio Player**: Segment playback with transcript synchronization
  - Full audio and split segment playback
  - Interactive transcript with time-synchronized highlighting
  - Temporary snippet generation for search results
  
- **Atlas**: Interactive geolinguistic map with Leaflet
  - Country/region markers with metadata
  - File counts and speaker statistics per location
  - Integrated with corpus data

- **Statistics Dashboard**: Data visualization with ECharts
  - Speaker distribution by country, sex, type
  - Word frequency analysis
  - Interactive charts with filtering

### Content Management
- **Editor Interface** (Editor/Admin roles):
  - JSON transcript editing with live preview
  - Version tracking and edit history
  - File management per country/region
  
- **Admin Dashboard** (Admin role):
  - User management and role assignment
  - Content moderation capabilities

### Authentication & Security
- **JWT-based Authentication**: Cookie-based JWT tokens with CSRF protection
- **Role-Based Access Control**: Three tiers (user, editor, admin)
- **Public Access Mode**: Configurable public/private audio snippet access
- **Security Features**: Rate limiting, CQL injection prevention, input validation

## Technology Stack

### Backend
- **Flask 3.x** with application factory pattern
- **SQLite** databases for corpus data and statistics
- **BlackLab Server** for advanced corpus search (Java-based)
- **FFmpeg** and **libsndfile** for audio processing
- **JWT** for authentication with cookie-based tokens

### Frontend
- **Vite** for asset bundling and build process
- **Material Design 3** principles with custom CSS architecture
- **DataTables** for interactive result tables
- **ECharts** for data visualization
- **Leaflet** for geolinguistic mapping
- **HTMX** for dynamic UI interactions

### Styling
- Material Design 3 design system with custom tokens
- BEM naming convention for CSS classes
- Design tokens in `static/css/md3/tokens.css`
- Responsive, mobile-first layouts
- WCAG 2.1 AA accessibility compliance

## Development

**Requirements**: Python 3.12+, Node 20+, FFmpeg, libsndfile

**Setup**:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
npm install
npm run build
```

**Run**:
```bash
set FLASK_SECRET_KEY=your-secret-key
python -m src.app.main
```

**Environment Variables**:
- `FLASK_SECRET_KEY` - Flask session secret
- `JWT_SECRET` - JWT signing key
- `ALLOW_PUBLIC_TEMP_AUDIO` - Allow anonymous audio snippet access (default: false)

## Current Status (November 2025)

### ✅ Production-Ready Features
- **Basic Corpus Search**: Fully operational with token-based queries
- **Advanced Search**: BlackLab integration complete (Stage 1-3), UI deployed
- **Authentication System**: JWT-based auth with GET/POST logout support
- **Audio Player**: Full playback with transcript synchronization
- **Atlas**: Interactive map with country/region data
- **Statistics**: ECharts-based visualization dashboard
- **Editor**: JSON transcript editing interface for authorized roles
- **Security**: CSRF protection, rate limiting, CQL injection prevention

### 🔧 Configuration
- **Database**: SQLite (`data/transcription.db`, `data/stats_all.db`)
- **Media Files**: Organized by country in `media/` directory
- **BlackLab Index**: 146 documents, 1.49M tokens, 15.89 MB index
- **Access Control**: Public access configurable via `ALLOW_PUBLIC_TEMP_AUDIO`

### 📊 System Metrics
- **Corpus Size**: 146 JSON documents across 20+ countries/regions
- **Total Tokens**: ~1.5 million indexed tokens
- **Search Performance**: <100ms for basic queries, <1s for complex CQL
- **Export Capability**: Up to 50,000 rows with streaming
