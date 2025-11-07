# GitLab Setup & Konfiguration

## Repository
- **URL**: `git@gitlab.uni-marburg.de:tackef/corapan-new.git`
- **Branch**: `main` (protected)

## CI/CD Pipeline

Die Pipeline ist in `.gitlab-ci.yml` konfiguriert und umfasst:

### Stages

1. **Test**
   - `test:python` - Python Tests mit pytest und Coverage
   - `lint:python` - Code-Qualität mit flake8, black, isort
   - `test:frontend` - Node.js Build-Test
   - `security:trivy` - Security Scan (optional)

2. **Build**
   - `build:docker` - Docker Image bauen und in Registry pushen

3. **Deploy**
   - `deploy:staging` - Manuelles Deployment zu Staging (konfigurierbar)

### Pipeline-Variablen

In GitLab unter **Settings → CI/CD → Variables** konfigurieren:

```bash
# Deployment (optional)
SSH_PRIVATE_KEY=<staging-server-key>
STAGING_HOST=staging.corapan.example.com
STAGING_USER=deploy

# Datenbank Credentials (für Tests)
TEST_DB_PATH=/tmp/test.db

# Optional: Notifications
SLACK_WEBHOOK_URL=<webhook-url>
```

### Docker Registry

Das Projekt nutzt die GitLab Container Registry:
```bash
docker pull registry.gitlab.uni-marburg.de/tackef/corapan-new:main
```

## Branch Protection

Empfohlene Einstellungen unter **Settings → Repository → Protected Branches**:

- **Branch**: `main`
- **Allowed to push**: Maintainers
- **Allowed to merge**: Developers + Maintainers
- **Require approval from code owners**: ✓
- **Pipelines must succeed**: ✓

## Issue Templates

Verfügbar beim Erstellen neuer Issues:
- **Bug Report** - Fehlerberichte mit Reproduktionsschritten
- **Feature Request** - Neue Features mit User Stories

## Merge Request Workflow

1. Feature-Branch erstellen: `git checkout -b feature/your-feature`
2. Änderungen committen und pushen
3. Merge Request in GitLab erstellen
4. Pipeline muss erfolgreich durchlaufen
5. Code Review abwarten
6. Nach Approval: Merge in `main`

## Labels

Empfohlene Labels in GitLab erstellen:

### Status
- `status::todo` - Noch nicht begonnen
- `status::in-progress` - In Arbeit
- `status::review` - Wartet auf Review
- `status::blocked` - Blockiert

### Type
- `type::bug` - Bug Fix
- `type::feature` - Neues Feature
- `type::enhancement` - Verbesserung
- `type::documentation` - Dokumentation

### Priority
- `priority::high` - Hohe Priorität
- `priority::medium` - Mittlere Priorität
- `priority::low` - Niedrige Priorität

### Component
- `component::backend` - Backend/Python
- `component::frontend` - Frontend/JavaScript
- `component::database` - Datenbank
- `component::infrastructure` - Infrastructure/DevOps

## Notifications

Einstellungen unter **Settings → Integrations**:

### Slack (optional)
- Webhook URL konfigurieren
- Events: Pushes, Merge Requests, Pipeline Status

### Email
- Automatische Benachrichtigungen bei:
  - Failed Pipelines
  - Merge Request Updates
  - Issue Mentions

## Security

### Secrets Management
- NIEMALS Secrets in Code committen
- Nutze GitLab CI/CD Variables (masked & protected)
- Rotate Secrets regelmäßig

### Dependency Scanning
- Automatisch via Trivy in Pipeline
- Manuelle Überprüfung: `trivy fs .`

### Access Control
- SSH-Keys für Zugriff erforderlich
- Personal Access Tokens für API-Zugriff
- 2FA empfohlen für alle Maintainer

## Monitoring

### Pipeline Status
Badge in README:
```markdown
[![pipeline status](https://gitlab.uni-marburg.de/tackef/corapan-new/badges/main/pipeline.svg)](https://gitlab.uni-marburg.de/tackef/corapan-new/-/commits/main)
```

### Coverage Report
Badge in README:
```markdown
[![coverage report](https://gitlab.uni-marburg.de/tackef/corapan-new/badges/main/coverage.svg)](https://gitlab.uni-marburg.de/tackef/corapan-new/-/commits/main)
```

## Troubleshooting

### Pipeline Failures

**Python Tests schlagen fehl:**
```bash
# Lokal testen
python -m pytest tests/ -v
```

**Docker Build schlägt fehl:**
```bash
# Lokal bauen
docker build -t corapan-test .
docker run -it corapan-test /bin/bash
```

**Frontend Build schlägt fehl:**
```bash
# Dependencies aktualisieren
npm ci
npm run build
```

### SSH-Probleme

```bash
# SSH-Verbindung testen
ssh -T git@gitlab.uni-marburg.de

# SSH-Agent prüfen
ssh-add -l
```

## Weitere Ressourcen

- [GitLab CI/CD Docs](https://docs.gitlab.com/ee/ci/)
- [Docker Build Optimization](https://docs.docker.com/build/building/best-practices/)
- [Python Testing with pytest](https://docs.pytest.org/)
