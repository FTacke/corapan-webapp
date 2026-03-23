#!/usr/bin/env python3
# zenodo_corpus_zip.py

import os
import re
import json
import shutil
import zipfile
from datetime import datetime, timezone

# Pfade
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
# Projekt-Root ist 2 Ebenen über dem Skript-Verzeichnis
# (... -> _1_zenodo-repos -> LOKAL -> corapan-webapp)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
MP3_DIR = os.path.join(PROJECT_ROOT, "media", "mp3-full")
TRANSCRIPTS_DIR = os.path.join(PROJECT_ROOT, "media", "transcripts")
ZIP_DIR = os.path.join(SCRIPT_DIR, "Zenodo Full Corpus")
LOG_FILE = os.path.join(SCRIPT_DIR, "zip_process.log")



def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_log(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    os.makedirs(ZIP_DIR, exist_ok=True)
    log = load_log()
    
    if not os.path.isdir(MP3_DIR):
        print(f"❌ ERROR: Ordner '{MP3_DIR}' nicht gefunden!")
        return
    
    if not os.path.isdir(TRANSCRIPTS_DIR):
        print(f"❌ ERROR: Ordner '{TRANSCRIPTS_DIR}' nicht gefunden!")
        return
    
    # Unterordner in media/mp3-full/ sammeln
    groups = {}
    for folder_name in os.listdir(MP3_DIR):
        folder_path = os.path.join(MP3_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        # Alle MP3-Dateien in diesem Unterordner sammeln
        mp3_files = [fn for fn in os.listdir(folder_path) if fn.lower().endswith(".mp3")]
        if mp3_files:
            groups[folder_name] = {"mp3": sorted(mp3_files), "json": []}

    if not groups:
        print("⚠️  Keine Unterordner mit MP3-Dateien gefunden.")
        return
    
    # JSON-Dateien aus media/transcripts/ sammeln (gleiche Unterordnernamen)
    for folder_name in groups.keys():
        transcripts_folder = os.path.join(TRANSCRIPTS_DIR, folder_name)
        if os.path.isdir(transcripts_folder):
            json_files = [fn for fn in os.listdir(transcripts_folder) if fn.lower().endswith(".json")]
            groups[folder_name]["json"] = sorted(json_files)

    updated = False
    for folder_name, data in groups.items():
        mp3_files = data["mp3"]
        json_files = data["json"]
        
        mp3_folder = os.path.join(MP3_DIR, folder_name)
        json_folder = os.path.join(TRANSCRIPTS_DIR, folder_name)
        
        # mtime ermitteln für beide Dateitypen
        mtimes = {}
        for fn in mp3_files:
            mtimes[f"mp3:{fn}"] = os.path.getmtime(os.path.join(mp3_folder, fn))
        for fn in json_files:
            mtimes[f"json:{fn}"] = os.path.getmtime(os.path.join(json_folder, fn))
        
        entry = log.get(folder_name, {})
        
        if entry.get("files") == {"mp3": mp3_files, "json": json_files} and entry.get("mtimes") == mtimes:
            print(f"✓ {folder_name}: keine Änderungen, übersprungen.")
            continue

        zip_path = os.path.join(ZIP_DIR, f"{folder_name}.zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            # MP3-Dateien in mp3-files/ Ordner
            for fn in mp3_files:
                abs_path = os.path.join(mp3_folder, fn)
                z.write(abs_path, arcname=f"mp3-files/{fn}")
            
            # JSON-Dateien in json-transcripts/ Ordner
            for fn in json_files:
                abs_path = os.path.join(json_folder, fn)
                z.write(abs_path, arcname=f"json-transcripts/{fn}")
        
        # Log aktualisieren
        log[folder_name] = {
            "files": {"mp3": mp3_files, "json": json_files},
            "mtimes": mtimes,
            "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        file_count = len(mp3_files) + len(json_files)
        print(f"✓ {folder_name}: ZIP erstellt/aktualisiert ({len(mp3_files)} MP3s + {len(json_files)} JSONs)")
        print(f"  → {zip_path}")
        updated = True

    if updated:
        save_log(log)
        print("\n✅ Log-Datei aktualisiert.")
    else:
        print("\nℹ️  Keine ZIPs neu erstellt; Log bleibt unverändert.")

if __name__ == "__main__":
    main()
