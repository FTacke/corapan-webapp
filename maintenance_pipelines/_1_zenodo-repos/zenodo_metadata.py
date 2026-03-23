#!/usr/bin/env python3
# zenodo_metadata.py
"""
Kopiert alle Metadaten-Dateien für das Zenodo Metadata Repository (Public).

Quelle:     runtime/data/public/metadata/latest/
Ziel:       LOKAL/_1_zenodo-repos/Zenodo Metadata/

Enthält:
  - Globale Metadaten (corapan_recordings.*, corapan_corpus_metadata.*)
  - Länderspezifische Metadaten (corapan_recordings_{COUNTRY_CODE}.*)
  - TEI-Header (tei_headers.zip)
"""

import os
import json
import shutil
from datetime import datetime, timezone

# Pfade
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
RUNTIME_ROOT = os.getenv("CORAPAN_RUNTIME_ROOT")
if not RUNTIME_ROOT:
    raise RuntimeError(
        "CORAPAN_RUNTIME_ROOT not configured. "
        "Runtime data is required for Zenodo metadata export."
    )
METADATA_SRC = os.path.join(RUNTIME_ROOT, "data", "public", "metadata", "latest")
METADATA_DEST = os.path.join(SCRIPT_DIR, "Zenodo Metadata")
LOG_FILE = os.path.join(SCRIPT_DIR, "metadata_process.log")

# Globale Metadaten-Dateien (ohne länderspezifische)
GLOBAL_METADATA_FILES = [
    "corapan_recordings.tsv",
    "corapan_recordings.json",
    "corapan_recordings.jsonld",
    "corapan_corpus_metadata.json",
    "corapan_corpus_metadata.jsonld",
    "tei_headers.zip",
]


def load_log():
    """Lädt das Log aus der JSON-Datei."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_log(data):
    """Speichert das Log in die JSON-Datei."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def copy_if_changed(src: str, dest: str, log_entry: dict | None) -> tuple[bool, dict]:
    """
    Kopiert eine Datei nur, wenn sie geändert wurde.
    
    Returns:
        Tuple (changed: bool, new_log_entry: dict)
    """
    if not os.path.exists(src):
        return False, {}
    
    stat = os.stat(src)
    mtime = stat.st_mtime
    size = stat.st_size
    
    # Prüfen, ob Kopie nötig ist
    if log_entry and log_entry.get("mtime") == mtime and log_entry.get("size") == size:
        return False, log_entry
    
    # Kopieren
    shutil.copy2(src, dest)
    
    new_entry = {
        "mtime": mtime,
        "size": size,
        "copied": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return True, new_entry


def main():
    """Hauptfunktion: Kopiert alle Metadaten-Dateien."""
    print("=" * 60)
    print("CO.RA.PAN Metadata Export für Zenodo")
    print("=" * 60)
    print(f"Quelle:  {METADATA_SRC}")
    print(f"Ziel:    {METADATA_DEST}")
    print("=" * 60)
    
    # Prüfen, ob Quellverzeichnis existiert
    if not os.path.isdir(METADATA_SRC):
        print(f"❌ ERROR: Quellverzeichnis nicht gefunden: {METADATA_SRC}")
        print("   Bitte zuerst export_metadata.py ausführen!")
        return
    
    # Zielverzeichnis erstellen
    os.makedirs(METADATA_DEST, exist_ok=True)
    
    # Log laden
    log = load_log()
    changed_count = 0
    skipped_count = 0
    
    # 1) Globale Metadaten-Dateien kopieren
    print("\n📄 Globale Metadaten:")
    global_log = log.get("global", {})
    
    for filename in GLOBAL_METADATA_FILES:
        src = os.path.join(METADATA_SRC, filename)
        dest = os.path.join(METADATA_DEST, filename)
        
        changed, entry = copy_if_changed(src, dest, global_log.get(filename))
        
        if not entry:
            print(f"   ⚠️  {filename} nicht gefunden")
            continue
        
        global_log[filename] = entry
        
        if changed:
            print(f"   ✓ {filename} kopiert")
            changed_count += 1
        else:
            print(f"   · {filename} unverändert")
            skipped_count += 1
    
    log["global"] = global_log
    
    # 2) Länderspezifische Metadaten-Dateien finden und kopieren
    print("\n🌍 Länderspezifische Metadaten:")
    country_log = log.get("countries", {})
    
    # Alle corapan_recordings_{CODE}.* Dateien finden
    country_files = []
    for filename in os.listdir(METADATA_SRC):
        if filename.startswith("corapan_recordings_") and not filename.startswith("corapan_recordings."):
            country_files.append(filename)
    
    country_files.sort()
    
    if not country_files:
        print("   ⚠️  Keine länderspezifischen Metadaten gefunden")
    else:
        for filename in country_files:
            src = os.path.join(METADATA_SRC, filename)
            dest = os.path.join(METADATA_DEST, filename)
            
            changed, entry = copy_if_changed(src, dest, country_log.get(filename))
            
            if entry:
                country_log[filename] = entry
                
                if changed:
                    print(f"   ✓ {filename} kopiert")
                    changed_count += 1
                else:
                    print(f"   · {filename} unverändert")
                    skipped_count += 1
    
    log["countries"] = country_log
    
    # Log speichern
    log["last_run"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_log(log)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Dateien kopiert:    {changed_count}")
    print(f"Dateien unverändert: {skipped_count}")
    print(f"Zielordner:         {METADATA_DEST}")
    print("=" * 60)
    
    if changed_count > 0:
        print("\n✅ Metadaten aktualisiert. Bereit für Zenodo-Upload.")
    else:
        print("\nℹ️  Keine Änderungen. Alle Dateien sind aktuell.")


if __name__ == "__main__":
    main()
