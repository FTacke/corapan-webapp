# Welle 2.1 Summary

Datum: 2026-03-20
Umgebung: Development lokal
Scope: Media-Zugriffe der Web-App gegen den kanonischen Dev-Medienpfad
Zielpfad:

- MEDIA_ROOT -> `C:\dev\corapan\media`

## 7.1 Ursache

Die gemeldete Fehlfunktion liess sich auf einem frischen aktuellen Dev-Prozess nicht reproduzieren.

Die aktuelle Laufzeitverifikation zeigt:

- `CORAPAN_MEDIA_ROOT` wird korrekt auf `C:\dev\corapan\media` gesetzt
- `AUDIO_FULL_DIR` wird korrekt auf `C:\dev\corapan\media\mp3-full` gesetzt
- `TRANSCRIPTS_DIR` wird korrekt auf `C:\dev\corapan\media\transcripts` gesetzt
- flache Media-URLs werden weiterhin auf die kanonische Subfolder-Struktur aufgeloest
- bereits verschachtelte Media-URLs werden direkt aus derselben kanonischen Struktur bedient

Die belegte Aufloesung im Test-Client-Log war:

- `/media/full/2023-08-10_ARG_Mitre.mp3` -> `C:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3`
- `/media/full/ARG/2023-08-10_ARG_Mitre.mp3` -> `C:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3`

Die naheliegendste technische Ursache fuer die beobachtete Abweichung ausserhalb dieser Reproduktion ist daher ein aelterer lokaler Dev-Prozess oder eine veraltete Verifikationssituation, nicht die aktuelle Pfadauflogik in `media.py` oder `media_store.py`.

## 7.2 Fix

Es wurde kein risikoreicher Verhaltensumbau vorgenommen, weil die aktuelle Media-Aufloesung gegen den kanonischen Dev-Pfad bereits korrekt funktioniert.

Stattdessen wurde der Media-Bereich gezielt abgesichert:

- `src/app/routes/media.py` loggt nun auch fuer Transcript-Anfragen explizit Request-Pfad, Basisverzeichnis und aufgeloesten Dateipfad
- ein neuer Regressionstest deckt fuer Audio und Transkripte jeweils beide Faelle ab:
  - flache URL ohne Laender-Subfolder im Request
  - verschachtelte URL mit explizitem Laender-Subfolder im Request

Damit wird die reale Anforderung festgeschrieben, dass Dev-Media-Dateien unter `C:\dev\corapan\media\...\<COUNTRY>\...` liegen duerfen, ohne dass flache historische URL-Formen brechen.

## 7.3 Verifikation

Live-Verifikation auf frischem isoliertem Dev-Prozess (`127.0.0.1:8002`):

- `/media/full/2023-08-10_ARG_Mitre.mp3` -> `200`, `audio/mpeg`, `89432109` Bytes
- `/media/full/ARG/2023-08-10_ARG_Mitre.mp3` -> `200`, `audio/mpeg`, `89432109` Bytes
- `/media/transcripts/2023-08-10_ARG_Mitre.json` -> `200`, `application/json`, `7494093` Bytes
- `/media/transcripts/ARG/2023-08-10_ARG_Mitre.json` -> `200`, `application/json`, `7494093` Bytes

Test-Client-Log mit expliziter Pfadauflosung:

- `Audio resolution: filename=2023-08-10_ARG_Mitre.mp3 resolved_path=c:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3 exists=True`
- `Audio resolution: filename=ARG/2023-08-10_ARG_Mitre.mp3 resolved_path=C:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3 exists=True`

Automatisierte Regression:

- neuer fokussierter Test fuer Media-Routen gegen temporaere kanonische `media/`-Struktur
- geprueft werden sowohl Audio als auch Transcript-Endpunkte fuer flache und verschachtelte Requests

## 7.4 Lessons Learned

- Pfadkonsolidierung kann Subfolder-Strukturen brechen, wenn Code implizit flache Strukturen annimmt
- eine frische Dev-Instanz auf isoliertem Port ist bei Pfad- und Cache-Diagnosen die zuverlaessigere Quelle als ein bereits laufender Default-Port-Prozess
- Media-Verifikation muss immer beide Request-Formen pruefen:
  - flach: `/media/full/<datei>` bzw. `/media/transcripts/<datei>`
  - verschachtelt: `/media/full/<country>/<datei>` bzw. `/media/transcripts/<country>/<datei>`