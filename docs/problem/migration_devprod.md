# migration_devprod.md

**Data- & Runtime-Migration DEV ⇄ PROD (Zielbild & Begründung)**

## 1. Ausgangslage (Problem)

Der aktuelle `data/`-Ordner ist historisch gewachsen und vermischt unterschiedliche Dinge:

* aktive Produktionsdaten
* temporäre Build-Artefakte
* Backups mit Zeitstempeln
* DEV-Reste, Testbuilds, „bad“-Zustände
* Datenbanken mit unterschiedlicher Sensitivität

Das führt zu:

* unklarer Quelle der Wahrheit
* schwerem Aufräumen
* implizitem Wissen („welcher Ordner wird wirklich benutzt?“)
* DEV ≠ PROD (strukturell)

Ziel dieser Migration ist **keine kosmetische Ordnung**, sondern eine **tragfähige, prod-konforme Datenarchitektur**.

---

## 2. Grundprinzip (entscheidend)

**Trennung nach Verantwortung, nicht nach Historie.**

> **Code & Inputs gehören ins Repo**
> **Laufzeitdaten gehören in `runtime/`**
> **`data/` ist ein logisches Namespace, kein Sammelplatz**

DEV und PROD sollen **dieselbe Struktur** verwenden.
Der einzige Unterschied ist **der physische Ort** (lokal vs. Server).

---

## 3. Definitionen (Begriffe)

* **Repo**: Git-Checkout (`corapan-webapp/`)
* **Runtime**: Laufzeitverzeichnis (`CORAPAN_RUNTIME_ROOT`)
* **data/**: Logischer Container *innerhalb* der Runtime (nicht im Repo!)

In PROD existiert **kein Repo-`data/`**.
In DEV darf ein Repo-`data/` nur **Legacy/Input** enthalten.

---

## 4. Zielbild (Proposed Structure – final)

Diese Struktur gilt **identisch** für DEV-Runtime und PROD-Runtime:

```
data/
├── blacklab/
│   ├── index/                  # Aktiver produktiver Index
│   ├── index-staging/          # Pre-Validation / Testbuild
│   ├── backups/                # Rollierende, datierte Backups
│   │   └── index_YYYYMMDD_HHMMSS/
│   └── exports/                # Input für Index-Build
│       ├── tsv/
│       ├── metadata/
│       └── docmeta.jsonl
│
├── db/
│   ├── public/                 # Öffentliche, read-only DBs
│   │   ├── stats_files.db
│   │   ├── stats_country.db
│   │   └── (nur stats_files.db, stats_country.db)
│   └── restricted/             # Sensitiv, nie öffentlich
│       └── auth.db
│
└── public/
  ├── metadata/               # FAIR-Metadaten (Versioniert)
  │   ├── latest/ -> v2025-12-06
  │   ├── v2025-12-01/
  │   └── v2025-12-06/
  └── statistics/             # Laufzeit-Statistiken
        ├── corpus_stats.json
        └── viz_*.png
```

---

## 5. Klare Regeln (nicht verhandelbar)

### 5.1 Runtime-Regeln

* **Alles**, was generiert wird → `runtime/.../data/`
* Die App liest **ausschließlich** aus Runtime
* Repo-`data/` ist **niemals** Quelle der Wahrheit

### 5.2 BlackLab

* **index/**: genau **ein** aktiver Index
* **index-staging/**: genau **ein** Kandidat vor Aktivierung
* **backups/**: nur rotierende Backups (Retention!)
* Keine `blacklab_index.bad_*`, `.new.bad_*`, `.testbuild.*` mehr

### 5.3 Datenbanken

* Öffentliche Statistik-DBs → `db/public`
* Auth / sensible DBs → `db/restricted`
* Klare Sync-Regeln (public ja, restricted nein)

### 5.4 Statistiken

* Statistiken werden **immer** nach
  `data/public/statistics/` geschrieben
* Repo-Statistiken sind **legacy** und werden migriert
* DEV darf warnen, PROD darf abbrechen

---

## 6. Migrationsstrategie (bewusst schrittweise)

### Phase 1 – Jetzt (in Arbeit)

* Statistik-Skripte schreiben nur noch in Runtime
* App liest nur noch aus Runtime
* Einmalige Migration Repo → Runtime

### Phase 2 – Konsolidierung

* BlackLab-Ordner zusammenführen:

  * `blacklab_index*` → `blacklab/index`, `index-staging`, `backups`
* Alte `.bad`, `.testbuild`, `.bak` eliminieren
* Naming konsistent machen

### Phase 3 – Aufräumen Repo

* Repo-`data/` → `data_legacy/`
* Nur echte Inputs behalten (falls nötig)
* Laufzeitdaten komplett entfernt

### Phase 4 – PROD-Härtung

* Retention-Policy für Backups
* Harte Checks (kein Start ohne Runtime)
* Dokumentierte Restore-Pfad

---

## 7. Warum dieses Zielbild „richtig“ ist

* DEV = PROD (strukturell identisch)
* Keine impliziten Pfade mehr
* Einfache Backups & Restores
* Saubere Verantwortungstrennung
* Zukunftssicher für Automatisierung

---

## 8. Leitsatz

> **Runtime ist die Wahrheit.
> data/ ist strukturiert.
> Chaos entsteht nur, wenn beides vermischt wird.**

Dieses Dokument beschreibt **das Ziel**, nicht jeden Einzelschritt.
Alle technischen Prompts und Skripte dienen ausschließlich dazu, **dieses Zielbild schrittweise und sicher zu erreichen**.
