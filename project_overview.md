# Projektübersicht CO.RA.PAN

## 1. Projektstruktur
- `.cline.json`: Konfigurationsdatei mit Ausschlussliste für Indizierung.
- `app.py`: Haupt-Flask-Anwendung mit Authentifizierung, Audioverarbeitung, Datenbankzugriff und Routen.
- `requirements.txt`: Python-Abhängigkeiten.
- `Dockerfile`, `.dockerignore`: Containerisierung.
- `db/`, `db_public/`: Datenbanken (z.B. `stats_all.db`).
- `grabaciones/`: Audio- und JSON-Dateien mit Aufnahmen.
- `split/`, `temp-mp3/`: Temporäre und gesplittete Audiodateien.
- `keys/`: Schlüssel für JWT-Authentifizierung.
- `static/`: Statische Dateien (CSS, JS, Bilder).
- `templates/`: HTML-Templates für die Weboberfläche.

## 2. Hauptkomponenten

### app.py
- Flask-App mit JWT-Authentifizierung (Admin, Guest).
- Audioverarbeitung mit pydub, eyed3, ffprobe.
- Datenbankzugriffe auf SQLite-Datenbanken (`stats_all.db`, `transcription.db`).
- Routen für Startseite, Login, Logout, Player, Suche, Statistiken, etc.
- Hintergrund-Task zum Löschen alter temporärer Dateien.
- Audio-Split-Logik und Spektrogramm-Generierung.

### Benutzerverwaltung
- Benutzergruppen und Passwörter werden zentral in der Datei `passwords.env` im Root-Verzeichnis definiert.
- Neue Benutzer und Passwörter werden über das Script `LOKAL/security/hash_passwords.py` hinzugefügt, das Klartext-Passwörter sicher hasht und in die `.env` schreibt.
- Die Flask-App lädt beim Start automatisch alle Benutzer mit einem Passwort aus der `.env` und macht sie für die Authentifizierung verfügbar.
- Änderungen an Benutzergruppen erfordern kein Ändern von `app.py` mehr, sondern nur das Aktualisieren der `.env` und ggf. Neustart des Containers.

### Templates
- `index.html`: Startseite mit Login-Formular und Navigation.
- `corpus.html`: Suchseite mit Filteroptionen, Ergebnisanzeige, Audio-Player und Exportfunktionen.
- `player.html`: Detailseite mit Transkription, Metadaten und Audio-Steuerung.
- `proyecto.html`, `atlas.html`: Informationsseiten mit Projektbeschreibung und interaktiver Karte.
- `datenschutz.html`, `impressum.html`: Rechtliche Seiten.

## 3. Interaktionen
- Nutzer authentifizieren sich via JWT.
- Suche erfolgt über SQL-Abfragen auf `transcription.db`.
- Ergebnisse werden mit Kontext und Audio-Segmenten angezeigt.
- Audio-Segmente werden bei Bedarf aus gesplitteten MP3s generiert und temporär gespeichert.
- Spektrogramme werden dynamisch erzeugt und angezeigt.
- Frontend nutzt JavaScript für Audio-Steuerung, Suche und UI-Interaktionen.

## 4. Nutzung
- Projekt kann lokal mit Flask gestartet werden.
- Daten liegen in SQLite-Datenbanken und Audiodateien vor.
- Weboberfläche bietet Zugriff auf Suchfunktionen, Player und Projektinformationen.

---

Diese Übersicht kann bei neuen Tasks als Kontext geladen werden, um den Projektstand schnell zu erfassen.

## 5. Dokumentations-Konventionen

### JavaScript (.js)
- Einheitliches Block-Kommentar-Muster für Hauptabschnitte:
  ```js
  // ===========================================================================
  // Abschnittsname
  // ===========================================================================
  ```
- Funktionen und wichtige Codeblöcke werden mit JSDoc-Kommentaren dokumentiert.
- Inline-Kommentare werden auf ein Minimum reduziert, um Klarheit zu bewahren.

### HTML (.html)
- Hauptabschnitte werden mit HTML-Kommentaren markiert:
  ```html
  <!-- ===========================================================================
       Meta & Head
       =========================================================================== -->

  <!-- ===========================================================================
       Header
       =========================================================================== -->

  <!-- ===========================================================================
       Navigation
       =========================================================================== -->

  <!-- ===========================================================================
       Content
       =========================================================================== -->

  <!-- ===========================================================================
       Footer
       =========================================================================== -->
  ```
- Wichtige Bereiche und Blöcke erhalten kurze erklärende Kommentare.
- Keine Inline-Kommentare innerhalb von Tags, um Konflikte zu vermeiden.

### Python (.py)
- Hauptabschnitte mit Block-Kommentaren:
  ```python
  # ===========================================================================
  # Abschnittsname
  # ===========================================================================
  ```
- Funktionen und Klassen mit Docstrings im Google- oder NumPy-Stil.
- Inline-Kommentare sparsam und nur bei komplexer Logik.

### CSS (.css)
- Hauptabschnitte mit Block-Kommentaren:
  ```css
  /* ===========================================================================
     Abschnittsname
     =========================================================================== */
  ```
- Wichtige Stilregeln mit kurzen Kommentaren versehen.
- Keine Inline-Kommentare innerhalb von Selektoren oder Eigenschaften.

Diese Konventionen sind so gewählt, dass sie keine Konflikte in Visual Studio Code erzeugen und eine konsistente, klare Dokumentation über alle Dateitypen hinweg ermöglichen.
