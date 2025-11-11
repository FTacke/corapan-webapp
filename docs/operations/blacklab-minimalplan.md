---
title: "BlackLab Integration - Minimalplan (Next Steps)"
status: active
owner: backend-team
updated: "2025-11-10"
tags: [blacklab, minimalplan, roadmap, implementation, next-steps]
links:
  - blacklab-integration-status.md
  - blacklab-quick-reference.md
  - ../concepts/blacklab-indexing.md
  - ../how-to/build-blacklab-index.md
---

# 🎯 BlackLab Integration - Minimalplan

**Ziel:** Umgebung bereit für UI-Implementation "Búsqueda avanzada"  
**Status:** Stage 1 (Export) ✅ COMPLETE | Stage 2-3 (Index + BLS) ⏳ PENDING  
**Datum:** 2025-11-10  
**Geschätzter Aufwand:** 1-2 Stunden (abhängig von Java-Installation)

---

## 📋 Was bisher erledigt ist

✅ **Stage 1: JSON→TSV Export**
- 146 JSON-Dateien → 146 TSV-Dateien
- 1,487,120 indexierbare Tokens
- Metadata in `docmeta.jsonl` (146 Einträge)
- Exporter-Skript: `src/scripts/blacklab_index_creation.py`
- **Alles ready, kann beliebig oft wiederholt werden**

✅ **Build-Infrastruktur**
- Index-Build-Skript: `scripts/build_blacklab_index.sh`
- BlackLab Server Start-Skript: `scripts/run_bls.sh`
- Proxy-Blueprint: `src/app/routes/bls_proxy.py` (Flask registered)
- Index-Config: `config/blacklab/corapan-tsv.blf.yaml`

✅ **Dokumentation**
- Status-Report: `docs/operations/blacklab-integration-status.md`
- Concepts: `docs/concepts/blacklab-indexing.md`
- How-To: `docs/how-to/build-blacklab-index.md`
- Quick-Ref: `docs/operations/blacklab-quick-reference.md`

---

## ⏳ Was noch fehlt (3 Stages)

### **STAGE 2: Lucene-Index bauen**
**Abhängigkeiten:** Java JDK 11+ + BlackLab Server  
**Input:** `data/blacklab_index/tsv/*.tsv` (146 TSV-Dateien)  
**Output:** `data/blacklab_index/` (Lucene-Index, ~100-500 MB)  
**Zeit:** ~5-15 Minuten

**Kommando:**
```bash
bash scripts/build_blacklab_index.sh tsv 4
```

**Was das Skript macht:**
1. Prüft, ob TSV-Dateien existieren → reuses existing exports
2. Startet IndexTool (BlackLab binary)
3. Erstellt Index in `data/blacklab_index.new/`
4. Atomar wechselt: `.new` → `current` (Zero-Downtime)
5. Schreibt Build-Log: `logs/bls/index_build.log`

### **STAGE 3: BlackLab Server starten**
**Abhängigkeiten:** Java JDK 11+ + BlackLab Server Binary  
**Config:** Port :8081, `indexDir=/data/blacklab_index`  
**Zeit:** ~5-10 Sekunden

**Kommando:**
```bash
bash scripts/run_bls.sh 8081 2g 512m
# port: 8081 (customizable)
# heap: 2g (JVM memory)
# direct: 512m (direct memory)
```

**Was das Skript macht:**
1. Prüft Java-Installation
2. Startet BlackLab Server auf :8081
3. Lädt Index: `data/blacklab_index/`
4. Wartet bis ready (exponential backoff)

### **STAGE 3B: Proxy-Test (Flask → BLS)**
**Abhängigkeiten:** BLS running + Flask app running  
**Endpoint:** `http://localhost:8000/bls/**`  
**Zeit:** ~10 Sekunden

**Smoke-Test Commands:**
```bash
# Test 1: Simple proxy
curl http://localhost:8000/bls/

# Test 2: Search for Spanish verb "ser"
curl 'http://localhost:8000/bls/corpus/corapan/1/hits?cql_query=[lemma="ser"]&format=json'

# Test 3: Get document metadata
curl 'http://localhost:8000/bls/corpus/corapan/doc/2025-02-28_USA_Univision'
```

**Erfolg:** Alle 3 Requests geben JSON zurück (keine Fehler)

---

## 🚀 MINIMALPLAN: Punkt-für-Punkt

### **Step 0: Prerequisites prüfen**

```bash
# Java vorhanden?
java -version
# → Sollte: openjdk version "11" or higher

# BlackLab Server vorhanden?
ls -la /opt/blacklab-server/  (Linux/macOS)
# oder: where blacklab-server  (Windows)
```

**Falls Java/BlackLab fehlen** → siehe "Installation" weiter unten

---

### **Step 1: Java JDK 11+ installieren**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install openjdk-11-jdk
java -version  # Verify
```

**macOS (Homebrew):**
```bash
brew install openjdk@11
# Dann: sudo ln -sfn /usr/local/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk
java -version  # Verify
```

**Windows (Chocolatey):**
```powershell
choco install openjdk11
java -version  # Verify (in new PowerShell window)
```

**Windows (Manual):**
1. Download: https://jdk.java.net/11/
2. Extract to: `C:\Program Files\openjdk-11\`
3. Add to PATH: `C:\Program Files\openjdk-11\bin`
4. Test: `java -version` (in new PowerShell)

---

### **Step 2: BlackLab Server herunterladen & extrahieren**

**Download:**
```bash
cd /tmp
wget https://github.com/INL/BlackLab/releases/download/v4.0.0/blacklab-server-4.0.0.war
# oder: curl -L -O ...
```

**Extrahieren:**
```bash
unzip blacklab-server-4.0.0.war -d /opt/blacklab-server/
# oder: mkdir -p /opt/blacklab-server && cd /opt/blacklab-server && unzip ...
```

**Verify:**
```bash
ls -la /opt/blacklab-server/
# Sollte zeigen: lib/, META-INF/, WEB-INF/, etc.
```

**Windows-Alternative:**
- Download `.war` in beliebigen Ordner
- Extract mit 7-Zip oder WinRAR
- Update `scripts/run_bls.sh` mit korrektem Pfad

---

### **Step 3: Index bauen**

**Command:**
```bash
cd /path/to/CO.RA.PAN
bash scripts/build_blacklab_index.sh tsv 4
```

**Expected Output:**
```
[14:37:41] === BlackLab Index Build Started ===
[14:37:42] Format: tsv, Workers: 4
[14:37:43] Found 146 exported files
[14:37:44] Building index from TSV files...
[14:38:15] Index build successful
[14:38:16] Performing atomic index switch...
[14:38:17] Index ready at: data/blacklab_index/
```

**Verify Success:**
```bash
ls -la data/blacklab_index/
# Sollte zeigen: *.cfs, *.si, segment_*, version.txt (Lucene files)
du -sh data/blacklab_index/
# Sollte: 50-500 MB (abhängig von Kompression)
```

---

### **Step 4: BlackLab Server starten**

**Command (in separatem Terminal):**
```bash
bash scripts/run_bls.sh 8081 2g 512m
```

**Expected Output:**
```
[14:38:30] Checking Java installation...
[14:38:31] Java version: openjdk version "11.0.x"
[14:38:32] Starting BlackLab Server...
[14:38:35] Server starting at: org.apache.catalina.startup.Bootstrap start
[14:38:45] INFO: Server startup in [10,000] ms
[14:38:46] BlackLab Server running on http://localhost:8081/blacklab-server/
[14:38:47] Waiting for index to load...
[14:38:50] Index loaded successfully
```

**Verify Running:**
```bash
# In another terminal:
curl http://localhost:8081/blacklab-server/
# Sollte HTML-Response geben (BlackLab UI)

ps aux | grep java
# Sollte: java -Xmx2g -XX:MaxDirectMemorySize=512m ...
```

---

### **Step 5: Proxy-Test (Flask must be running!)**

**Command (in drittes Terminal):**
```bash
# Stelle sicher, dass Flask läuft:
python -m src.app.main  # Falls nicht schon running

# Dann in anderem Terminal:
curl http://localhost:8000/bls/
```

**Expected Output:**
```json
{"resources":[{"name":"blacklab-server"},...]}
```

**Test 2: Search**
```bash
curl 'http://localhost:8000/bls/corpus/corapan/1/hits?cql_query=[lemma="ser"]&limit=5&format=json'
```

**Expected Output:**
```json
{"summary":{"indexName":"corapan",...},"hits":[{"docPid":"2025-02-28_USA_Univision",...}]}
```

---

## 🔍 Troubleshooting

### **Problem: `java: command not found`**
**Lösung:**
```bash
# Ubuntu/Debian
sudo update-alternatives --config java

# macOS
/usr/libexec/java_home -V  # Show all Java versions
export JAVA_HOME=$(/usr/libexec/java_home -v 11)

# Windows: neues PowerShell-Terminal öffnen (PATH refresh)
```

### **Problem: `IndexTool: command not found`**
**Lösung:**
```bash
# IndexTool ist in BlackLab Server enthalten
# Wenn BlackLab nicht im PATH:
export BLACKLAB_HOME=/opt/blacklab-server
$BLACKLAB_HOME/bin/IndexTool ...

# Oder Pfad in scripts/build_blacklab_index.sh updaten
```

### **Problem: `data/blacklab_index` bleibt leer nach Build**
**Lösung:**
```bash
# Checke Build-Log
cat logs/bls/index_build.log | tail -50

# Prüfe TSV-Dateien
ls -la data/blacklab_index/tsv/ | head
wc -l data/blacklab_index/tsv/*.tsv | tail -1

# Manuelle Index-Erstellung testen
IndexTool create data/blacklab_index.test data/blacklab_index/tsv/*.tsv config/blacklab/corapan-tsv.blf.yaml --docmeta data/blacklab_index/docmeta.jsonl
```

### **Problem: BLS startet nicht, nur `Picking up JAVA_TOOL_OPTIONS` Ausgabe**
**Lösung:**
```bash
# Unset JAVA_TOOL_OPTIONS
unset JAVA_TOOL_OPTIONS
bash scripts/run_bls.sh 8081 2g 512m
```

### **Problem: Proxy antwortet mit 502 Bad Gateway**
**Lösung:**
```bash
# 1. Prüfe ob BLS läuft
curl http://localhost:8081/blacklab-server/

# 2. Prüfe Flask-Log
tail -50 logs/flask.log  # wenn vorhanden

# 3. Prüfe httpx-Client in Proxy
# src/app/routes/bls_proxy.py zeigt Connection-Error
```

---

## 📊 Fortschritt-Tracking

| Phase | Command | Status | Verify |
|-------|---------|--------|--------|
| **Java** | `java -version` | ⏳ TODO | output zeigt 11+ |
| **BlackLab** | `ls /opt/blacklab-server/` | ⏳ TODO | dirs vorhanden |
| **Index-Build** | `bash scripts/build_blacklab_index.sh tsv 4` | ⏳ TODO | `data/blacklab_index/*.cfs` exists |
| **BLS-Start** | `bash scripts/run_bls.sh 8081 2g 512m` | ⏳ TODO | curl :8081 works |
| **Proxy-Test** | `curl http://localhost:8000/bls/` | ⏳ TODO | JSON response |

---

## ✅ Erfolgskriterien

✅ **Stage 2 erfolgreich** wenn:
- `data/blacklab_index/` nicht leer
- `data/blacklab_index/segment_*` Dateien existieren
- `logs/bls/index_build.log` zeigt: "Index build successful"

✅ **Stage 3 erfolgreich** wenn:
- `ps aux | grep java` zeigt BlackLab-Prozess
- `curl http://localhost:8081/blacklab-server/` gibt HTTP 200
- `curl http://localhost:8000/bls/` gibt JSON response

✅ **Alles ready für UI-Implementierung** wenn:
- Alle 3 Proxy-Smoke-Tests erfolgreich
- Search-Requests geben Resultate (auch wenn leer)
- Keine Java/BLS-Fehler in Logs

---

## 🎯 Nach diesem Minimalplan

Wenn alles erfolgreich durchlaufen:

1. **UI-Implementation "Búsqueda avanzada"** kann starten
   - Blueprint `advanced.py` mit CQL-Query-Builder
   - Template `search-advanced.html` mit Formular
   - JS-Module für Query-Syntax-Highlighting
   - Integrations-Tests für Proxy

2. **Nächste Integration-Stufen**
   - Admin-Dashboard für Index-Status
   - Scheduled re-indexing (cron/celery)
   - Index freshness monitoring
   - Disaster recovery (backup/restore)

3. **Production Deployment**
   - Load-Balancing (mehrere BLS-Instanzen)
   - Monitoring & Alerting
   - High-Availability Setup
   - CI/CD für Index-Updates

---

## 📞 Support

**Dokumentation:**
- Alle Details: `docs/operations/blacklab-integration-status.md`
- Quick-Ref: `docs/operations/blacklab-quick-reference.md`
- Troubleshooting: `docs/troubleshooting/blacklab-issues.md`

**Bei Problemen:**
1. Checke `logs/bls/index_build.log` (Index-Fehler)
2. Checke `logs/flask.log` (Proxy-Fehler)
3. Checke Troubleshooting-Docs
4. Siehe GitHub Issues Template in CONTRIBUTING.md

---

**Erstellt:** 2025-11-10  
**Zielgruppe:** Backend-Team, DevOps  
**Nächste Meilenstein:** Stage 2 + 3 complete, UI-Implementierung starten
