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

See `docs/architecture.md`, `docs/design-system.md`, and `docs/roadmap.md` for detailed plans and next steps.

### Key Resources
- **[Deployment Guide](docs/deployment.md)** - Production server setup and update workflow
- **[Git Security](docs/git-security-checklist.md)** - Security best practices for Git
- **[Architecture](docs/architecture.md)** - Technical architecture overview
- **[Design System](docs/design-system.md)** - Design tokens and components
- **[Database Maintenance](docs/database_maintenance.md)** - Database updates and optimization
- **[Documentation Summary](docs/DocumentationSummary.md)** - Complete documentation index

For all documentation, see the `docs/` directory.

## Features

- **Corpus Search**: Token-based search with morphological filters
- **Atlas**: Interactive geolinguistic map with Leaflet
- **Audio Player**: Segment playback with transcript synchronization
- **Authentication**: JWT-based auth with role-based access control
- **Admin Dashboard**: User and content management

## Styling

- Tailwind CDN in `templates/base.html` (build setup via `tailwind.config.js`)
- Custom utility classes: `card`, `badge`, `muted-link`, `font-condensed`
- Responsive navbar in `templates/partials/_navbar.html`

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

## Documentation

- `docs/architecture.md` - Technical architecture
- `docs/design-system.md` - Design tokens and components
- `docs/roadmap.md` - Development roadmap
