# PROD MIGRATION – FINAL MAPPING (Phase D3)

## Zielbild (verbindlich)

/srv/webapps/corapan/
  app/
  data/
    blacklab/          # Ziel für BlackLab-Index
    config/            # Ziel für App-Config
    db/                # optional (nur falls genutzt)
    public/
    stats_temp/
  media/               # Ziel für alle Media-Dateien
  logs/                # optional (final festzulegen)

## IST → SOLL Mapping

### App Data (ohne BlackLab)
FROM:
  runtime/corapan/data

TO:
  data/

STATUS:
  noch NICHT migriert

---

### Media (kritisch, ~15GB)
FROM:
  runtime/corapan/media

TO:
  media/

STATUS:
  noch NICHT migriert

---

### Config
FROM:
  runtime/corapan/config

TO:
  data/config/

STATUS:
  noch NICHT migriert

---

### Logs
FROM:
  runtime/corapan/logs

TO:
  logs/  (oder data/logs – noch final festzulegen)

STATUS:
  noch NICHT migriert

---

### BlackLab (WICHTIG)

AKTUELL GENUTZT:
  /srv/webapps/corapan/data/blacklab_index

ZIEL:
  /srv/webapps/corapan/data/blacklab/

STATUS:
  Index muss verschoben und BlackLab-Container neu gebunden werden

---

### Postgres

LOCATION:
  Docker Volume (corapan_postgres_prod)

STATUS:
  KEINE Migration nötig

---

## Risiken

- Disk nur begrenzt frei → keine Vollkopien möglich
- Media (~15GB) → nur MOVE, kein COPY
- BlackLab darf nicht beschädigt werden
- Container-Mounts müssen exakt angepasst werden

---

## Entscheidungsbedarf

- Logs final unter:
  - logs/ (Top-Level) ODER
  - data/logs/


## Verifikation Zielstruktur (nach Erstellung)

total 0
drwxr-xr-x  1 root     root      78 Mar 22 18:25 .
drwxr-xr-x  1 root     root      94 Feb  6 09:26 ..
drwxr-xr-x  1 root     root     854 Mar 22 17:46 app
drwxr-xr-x  1 root     root      26 Dec  2 23:40 config
drwxr-xr-x  1 root     root     348 Mar 22 18:25 data
drwxr-xr-x  1 root     root      28 Mar 22 18:25 docs
drwxr-xr-x  1 hrzadmin hrzadmin  22 Dec  2 12:04 logs
drwxr-xr-x  1 root     root       0 Jan 19 10:01 media
drwxr-xr-x  1     1001     1001 600 Mar 22 12:28 runner
drwxrwxr-x+ 1 hrzadmin hrzadmin  14 Jan 19 09:55 runtime

total 0
drwxr-xr-x 1 root     root      348 Mar 22 18:25 .
drwxr-xr-x 1 root     root       78 Mar 22 18:25 ..
drwxr-xr-x 1 root     root       56 Mar 20 22:16 blacklab
drwxr-xr-x 1 hrzadmin hrzadmin 1.7K Jan 15 18:41 blacklab_index
drwxrwxrwx 1 hrzadmin hrzadmin 1.7K Jan 16 00:24 blacklab_index.bad_2026-01-19_104135
drwxr-xr-x 1 hrzadmin hrzadmin 1.7K Jan 15 18:41 blacklab_index.bak_2026-01-16_003920
drwxr-xr-x 1 root     root        0 Jan 19 10:26 blacklab_index.new.leftover_2026-01-15_193558
drwxr-xr-x 1 root     root        0 Mar 22 18:25 config
drwxrwsr-x 1 hrzadmin hrzadmin   36 Jan 19 13:34 public
drwxrwsr-x 1 hrzadmin hrzadmin    0 Jan 19 13:33 stats_temp
drwxr-xr-x 1 hrzadmin hrzadmin  148 Dec  2 13:03 tsv_json_test
