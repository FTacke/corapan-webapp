# Audio-Player Modul

**Scope:** Segmentgenaue Audio-Wiedergabe  
**Source-of-truth:** `src/app/routes/player.py`, `src/app/routes/media.py`

## Übersicht

- **Segmentgenaue Wiedergabe:** 1 MP3 pro Segment
- **Synchronisierung:** Audio ↔ Transkript
- **Media Serving:** Via Flask (Dev) oder Nginx (Prod)

**Routes:**
- `/audio/<doc>/<seg>` — Player-Seite
- `/media/audio/<path>` — Audio-File-Serving

**Audio-Dateien:** `media/mp3-split/`

---

## Player UI

**Template:** `templates/player/index.html`

```html
<audio id="player" controls>
  <source src="/media/audio/{{ doc_id }}/{{ seg_id }}.mp3" type="audio/mpeg">
</audio>

<div class="transcript">
  {{ transcript_text }}
</div>
```

**JavaScript:**
```javascript
const audio = document.getElementById("player");
audio.addEventListener("play", () => {
  highlightTranscript(segId);
});
```

---

## Media Serving

**Route:** `GET /media/audio/<path>`

```python
# src/app/routes/media.py
@media_bp.route("/audio/<path:filepath>")
@jwt_required(optional=True)  # Public oder Auth
def serve_audio(filepath):
    audio_dir = current_app.config["AUDIO_SPLIT_DIR"]
    return send_from_directory(audio_dir, filepath)
```

**Nginx (Prod):**
```nginx
location /media/audio/ {
    alias /var/www/corapan/media/mp3-split/;
    expires 1y;
}
```

---

## Namenskonvention

**Dateiformat:** `<doc_id>_<seg_id>.mp3`

**Beispiel:** `es-bog-001_001.mp3`

---

## Extension Points

- **Playlist-Modus:** Mehrere Segmente hintereinander
- **Playback-Speed:** 0.5x, 1x, 1.5x, 2x
- **Waveform-Visualisierung:** (z.B. wavesurfer.js)
