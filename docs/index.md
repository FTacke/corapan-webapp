# CO.RA.PAN Webapp — Dokumentation

**Version:** 1.0.0  
**Status:** Produktion ([https://corapan.hispanistica.com/](https://corapan.hispanistica.com/))

Diese Dokumentation beschreibt den **aktuellen Produktionsstand** der CO.RA.PAN Webplattform — eine moderne Flask-basierte Webanwendung für linguistische Korpusanalyse mit Material Design 3 UI.

## Was ist CO.RA.PAN?

CO.RA.PAN ist eine Webplattform für die Analyse und Exploration des CO.RA.PAN-Korpus (Corpus Oral de Referencia del Español Actual - Variación Panhispánica). Sie ermöglicht:
- **Korpussuche** via BlackLab (einfach und CQL-basiert)
- **Audio-Wiedergabe** synchron zum Transkript
- **Statistische Auswertungen** und geografische Visualisierungen
- **Metadaten-Verwaltung** mit Rollen-basierter Zugriffskontrolle

## Dokumentations-Struktur

### Architektur
- [Überblick](architecture/overview.md) — Tech Stack, Module, High-Level Architektur
- [Request-Flow](architecture/request-flow.md) — Wie Requests durch die Anwendung fließen
- [Verzeichnisstruktur](architecture/directory-structure.md) — Repo-Layout und Organisation
- [Konfiguration](architecture/configuration.md) — ENV-Variablen, Secrets, Config-Layering
- [Deployment & Runtime](architecture/deployment-runtime.md) — Docker, Gunicorn, Nginx, Health Checks
- [Sicherheit & Auth](architecture/security-auth.md) — JWT, Sessions, CSRF, Rollen
- [Datenmodell](architecture/data-model.md) — Datenbank-Schema (Auth, Analytics)

### UI-System
- [Design System](ui/design-system.md) — Material Design 3 Prinzipien und Tokens
- [Layout Shell](ui/layout-shell.md) — Base Template, NavDrawer, TopAppBar
- [Komponenten](ui/components.md) — Buttons, Cards, Dialoge, Inputs, etc.
- [Theming & Tokens](ui/theming-tokens.md) — CSS Custom Properties, Dark/Light Mode

### Module
- [Suche (Search)](modules/search.md) — Korpussuche, CQL, Pattern Builder
- [Audio-Player](modules/player.md) — Segmentgenaue Wiedergabe
- [Atlas/Statistik](modules/atlas-stats.md) — Karten, Charts, Export
- [Editor](modules/editor.md) — JSON-Transkript-Editor
- [Auth & Admin](modules/auth-admin.md) — User Management, Login/Logout, Rollen
- [Analytics](modules/analytics.md) — DSGVO-konformes Tracking

### Operations
- [Lokale Entwicklung](operations/local-dev.md) — Setup, venv, Docker, Dev-Server
- [Produktion](operations/production.md) — Deploy, Environment, Monitoring
- [Troubleshooting](operations/troubleshooting.md) — Häufige Probleme und Lösungen

## Clone-Ready Checklist

Wenn du dieses Repo als Template nutzen oder für ein eigenes Projekt klonen möchtest, müssen folgende Punkte angepasst werden:

### 1. Branding & Identity
- [ ] **Logo & Favicon:** `static/img/logo.svg`, `static/img/favicon.ico`
- [ ] **App-Name:** In `templates/base.html`, `templates/partials/_navigation_drawer.html`
- [ ] **Titel/Meta:** `templates/base.html` (`{% block page_title %}`)
- [ ] **Footer:** `templates/partials/_footer.html` (Links, Kontakt, Impressum)

### 2. Theme & Design
- [ ] **Color Tokens:** `static/css/md3/tokens.css` (Primary, Secondary, Tertiary)
- [ ] **App-spezifische Overrides:** `static/css/app-tokens.css`
- [ ] **Typography:** `static/css/md3/typography.css` (falls abweichend)

### 3. Secrets & Config
- [ ] **FLASK_SECRET_KEY:** ENV-Variable setzen (mind. 32 Zeichen)
- [ ] **JWT_SECRET_KEY:** ENV-Variable setzen (separates Secret empfohlen)
- [ ] **AUTH_DATABASE_URL:** PostgreSQL DSN für Produktion konfigurieren
- [ ] **Datenbank-Migration:** `migrations/0001_create_auth_schema_postgres.sql` ausführen
- [ ] **Initial Admin:** `python scripts/create_initial_admin.py` ausführen

### 4. Domain & Infrastruktur
- [ ] **Domain:** Nginx/Reverse Proxy auf richtige Domain konfigurieren
- [ ] **HTTPS:** SSL-Zertifikate (Let's Encrypt) einrichten
- [ ] **Docker Compose:** `docker-compose.yml` Ports/Volumes anpassen
- [ ] **Email/SMTP:** Falls Password-Reset genutzt wird (optional)

### 5. Navigation & Content
- [ ] **Nav Items:** `templates/partials/_navigation_drawer.html` (Links anpassen)
- [ ] **Static Pages:** `templates/pages/impressum.html`, `templates/pages/privacy.html` (Rechtstexte!)
- [ ] **Homepage:** `templates/home/index.html` (Inhalt anpassen)

### 6. Feature-Module (Optional)
- [ ] **BlackLab:** Falls keine Korpussuche benötigt, Modul entfernen (siehe `docs/modules/search.md`)
- [ ] **Analytics:** Falls nicht benötigt, `src/app/analytics/` entfernen
- [ ] **Audio-Player:** Falls nicht benötigt, `src/app/routes/player.py` entfernen

### 7. Lokale Entwicklung
- [ ] **venv einrichten:** `python -m venv .venv` + `pip install -r requirements.txt`
- [ ] **Docker starten:** `docker-compose -f docker-compose.dev-postgres.yml up -d`
- [ ] **DB migrieren:** `flask auth-migrate` (oder manuell SQL ausführen)
- [ ] **Dev-Server:** `python -m src.app.main` oder `.\scripts\dev-start.ps1`

## Weiterführende Links

- **Produktion:** [https://corapan.hispanistica.com/](https://corapan.hispanistica.com/)
- **Repo:** Siehe README.md
- **Quick Start:** Siehe `startme.md`
- **Architekturbeschreibung:** [architecture/overview.md](architecture/overview.md)
