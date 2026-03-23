# Welle 3.1 Audio Playback Summary

Datum: 2026-03-20
Umgebung: Development lokal
Scope: gezielter Folge-Run fuer `/media/play_audio/...` auf frischem isoliertem Dev-Prozess
Klassifikation: `FFMPEG_DEPENDENCY_BUG`

## 8.5 Ursache

Der gemeldete Fehler fuer den Search-UI-Player war kein Pfadauflosungsfehler.

Reproduktion gegen die kanonische Dev-Struktur zeigte:

- die angeforderte Quelldatei `C:\dev\corapan\media\mp3-full\DOM\2024-07-17_DOM_Z101.mp3` existiert
- der passende Split-Chunk `C:\dev\corapan\media\mp3-split\DOM\2024-07-17_DOM_Z101_07.mp3` existiert ebenfalls
- `find_split_file(...)` loest fuer den gemeldeten Bereich `start=1467.47`, `end=1474.51` korrekt auf `_07` auf
- der bisherige Fehler entstand erst beim eigentlichen Audio-Decoding ueber pydub, weil im Dev-Prozess weder `ffmpeg` noch `ffprobe` verfuegbar waren

Der bisherige Route-Code fing diesen `FileNotFoundError` wie einen fehlenden Audio-Quellpfad ab und gab deshalb ein irrefuehrendes `404 Audio source not found` zurueck.

## 8.6 Fix

Der Fix wurde auf den Audio-Backend-Pfad begrenzt.

Geaendert wurde:

- `src/app/services/audio_snippets.py`
  - Snippets werden jetzt deterministisch ueber ein aufgeloestes `ffmpeg`-Backend gebaut statt implizit ueber pydub/ffprobe
  - bevorzugte Aufloesung:
    - explizites `CORAPAN_FFMPEG_PATH`
    - System-`ffmpeg` aus `PATH`
    - gebuendeltes `imageio-ffmpeg`
  - Split-vs-Full-Auswahl bleibt unveraendert, wird aber jetzt mit explizitem Source-Logging belegt
- `src/app/routes/media.py`
  - `/media/play_audio/...` und `/media/snippet` unterscheiden nun fehlendes Audio-Backend sauber von fehlenden Audiodateien
  - bei fehlendem Backend kommt jetzt `503 Audio snippet backend unavailable` statt eines falschen `404`
- `requirements.in` und `requirements.txt`
  - `imageio-ffmpeg` wurde als Runtime-Dependency aufgenommen, damit Dev nicht mehr von einer separat installierten System-ffmpeg-Binary abhaengt

Damit bleibt die Pfadlogik unangetastet; behoben wurde ausschliesslich der Snippet-Extraktionspfad.

## 8.7 Verifikation

Direkte Service-Reproduktion in der aktiven Dev-Umgebung:

- `build_snippet('DOM/2024-07-17_DOM_Z101.mp3', 1467.47, 1474.51, 'DOM63039913d', 'ctx')`
  - vorher: `FileNotFoundError [WinError 2]` aus pydub/ffprobe
  - nachher: Snippet wird erfolgreich erzeugt

Automatisierte Regression:

- `pytest tests/test_audio_snippet_integration.py tests/test_media_routes.py -q`
- Ergebnis: `5 passed`

Live-Verifikation auf frischem isoliertem Dev-Prozess (`127.0.0.1:8011`):

- `/media/full/DOM/2024-07-17_DOM_Z101.mp3` -> `200`, `29014714` Bytes, `audio/mpeg`
- `/media/play_audio/DOM/2024-07-17_DOM_Z101.mp3?start=1467.47&end=1474.51&t=123&token_id=DOM63039913d&type=ctx` -> `200`, `66182` Bytes, `audio/mpeg`

Server-Logbeleg fuer den zuvor fehlerhaften Request:

- `source_kind=split`
- `source_path=C:\dev\corapan\media\mp3-split\DOM\2024-07-17_DOM_Z101_07.mp3`
- `local_start=207.47`
- `local_end=214.51`
- `ffmpeg=C:\dev\corapan\webapp\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`

Search-UI-Relevanz:

- `static/js/modules/advanced/audio.js` baut genau dieselbe `/media/play_audio/...`-URL-Form
- der live verifizierte Request entspricht damit dem Player-Pfad der Search UI

## 8.8 Neue Regel

- Spezialrouten wie `/media/play_audio` duerfen nicht als "mitgeprueft" gelten, nur weil `/media/full` funktioniert; sie brauchen eigene Verifikation.
- Ein `FileNotFoundError` im Audio-Snippet-Pfad darf nicht automatisch als fehlende Quelldatei klassifiziert werden; externe Decoder-/Backend-Abhaengigkeiten muessen separat unterschieden und geloggt werden.