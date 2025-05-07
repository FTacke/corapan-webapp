## CO.RA.PAN Übersicht
Dieses Repository enthält **ausschließlich** den Quellcode der CO.RA.PAN Web-App. Die zugehörigen Datensätze (Full Corpus, Sample Corpus) sind separat über Zenodo verfügbar.

### Komponenten

1. **Web-App (Code)**
   - `app.py`, `static/`, `templates/`, `Dockerfile`, CI-Konfiguration
   - Dokumentation: `README.md`, `requirements.txt`, `project_overview.md`
   - Lizenz: MIT
   - DOI über Zenodo: **CO.RA.PAN Web-App (Code)**

2. **Full Corpus (Restricted)**
   - Vollständiges Daten-Korpus (Audio & Transkription)
   - Zenodo-Upload mit **Restricted** Visibility (Zugriff auf Anfrage)
   - DOI: **CO.RA.PAN Full Corpus (Restricted)**

3. **Sample Corpus (Public)**
   - Kleines Beispielpaket mit ausgewählten Audios & JSONs
   - Zenodo-Upload **Public**
   - DOI: **CO.RA.PAN Sample Corpus (Public)**

### Zusammenspiel
- Die Web-App konsumiert die Korpus-Daten (`db/`, `grabaciones/`, `split/`) und greift im Produktivbetrieb auf das Full Corpus zu.  
- Für erste Tests kann das Sample Corpus lokal geladen werden.  
- Die Code-Releases (Tags) lösen in Zenodo automatisiert DOI-Vergaben für die Web-App aus.

### Verwendung

1. **Code klonen**
   ```bash
   git clone https://gitlab.uni-marburg.de/tackef/corapan-webapp.git
   ```
2. **Environment & Abhängigkeiten**
   - `passwords.env` lokal anlegen (nicht versioniert)
   - `pip install -r requirements.txt`
3. **Container starten**
   ```bash
   docker build -t corapan-app:latest .
   docker run --rm --name corapan-app -p 8080:5000 --env-file passwords.env \
     -v "$(pwd)/grabaciones:/app/grabaciones" \
     -v "$(pwd)/split:/app/split" \
     -v "$(pwd)/db:/app/db" \
     corapan-app:latest
   ```
4. **App im Browser**
   `http://localhost:8080`

### DOIs & Links
- Web-App (Code): https://doi.org/…
- Full Corpus (Restricted): https://doi.org/…
- Sample Corpus (Public): https://doi.org/…

---
*Hinweis:* Dieses Repository enthält **keine** Korpus-Daten. Zur Nutzung der Daten bitte die oben genannten DOIs verwenden.
