# Editor Modul

**Scope:** JSON-Transkript-Editor (Editor-Rolle)  
**Source-of-truth:** `src/app/routes/editor.py`

## Übersicht

- **Zugriff:** Nur Editor/Admin-Rolle
- **Funktionen:** JSON-Transkripte bearbeiten, speichern
- **UI:** Monaco Editor (VS Code Editor als Web-Komponente)

**Routes:**
- `/editor` — Editor-UI
- `/editor/load/<doc>` — Transkript laden (GET)
- `/editor/save/<doc>` — Transkript speichern (POST)

---

## Editor UI

**Template:** `templates/editor/index.html`

```html
<div id="monaco-editor" style="height: 600px;"></div>

<script src="https://cdn.jsdelivr.net/npm/monaco-editor/min/vs/loader.js"></script>
<script>
  require.config({paths: {"vs": "https://cdn.jsdelivr.net/npm/monaco-editor/min/vs"}});
  require(["vs/editor/editor.main"], function() {
    const editor = monaco.editor.create(document.getElementById("monaco-editor"), {
      value: transcriptJson,
      language: "json",
      theme: "vs-dark"
    });
  });
</script>
```

---

## Load Transcript

```python
@editor_bp.route("/load/<doc_id>")
@require_role(Role.editor)
def load_transcript(doc_id):
    transcript_path = Path(current_app.config["TRANSCRIPTS_DIR"]) / f"{doc_id}.json"
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return jsonify(data)
```

---

## Save Transcript

```python
@editor_bp.route("/save/<doc_id>", methods=["POST"])
@require_role(Role.editor)
def save_transcript(doc_id):
    data = request.json
    
    # Validierung (optional)
    validate_transcript_schema(data)
    
    # Speichern
    transcript_path = Path(current_app.config["TRANSCRIPTS_DIR"]) / f"{doc_id}.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return jsonify({"message": "Gespeichert"})
```

---

## Extension Points

- **Versionierung:** Git-Integration für Transkript-History
- **Validierung:** JSON-Schema-Prüfung
- **Diff-Ansicht:** Änderungen visualisieren
- **Kollaboration:** Mehrere Editor gleichzeitig (WebSockets)
