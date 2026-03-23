# BlackLab Server Prep 2026-03-20

## Ziel

Nicht-disruptive Vorbereitung der künftigen kanonischen BlackLab-Zielstruktur unter `/srv/webapps/corapan/data/blacklab`, ohne Datenmigration, ohne Aenderung produktiver Pfade, ohne Container-/Mount-Aenderungen.

## Scope

- Erlaubt: Existenzpruefung, Rechtebasis erfassen, fehlende leere Zielverzeichnisse anlegen, Ergebnis verifizieren.
- Nicht erfolgt: Daten verschoben, Daten kopiert, Daten geloescht, Compose/Mounts angepasst, Container neu gestartet, Live-Pfade umgebogen.

## Pre-Check

### Vorhandene Zielstruktur vor der Ausfuehrung

- `/srv/webapps/corapan/data/blacklab` existierte bereits.
- `/srv/webapps/corapan/data/blacklab/export` existierte bereits.
- `/srv/webapps/corapan/data/blacklab/index` fehlte.
- `/srv/webapps/corapan/data/blacklab/backups` fehlte.
- `/srv/webapps/corapan/data/blacklab/quarantine` fehlte.

### Konfliktpruefung im bestehenden Zielbaum

- Unter `/srv/webapps/corapan/data/blacklab` war nur `export/` vorhanden.
- Unter `/srv/webapps/corapan/data/blacklab/export` wurden keine weiteren Eintraege gefunden.
- Ergebnis: kein inhaltlicher Konflikt im bestehenden Teilbaum festgestellt.

### Rechtebasis der Referenzpfade vor der Ausfuehrung

| Pfad | Status vor der Ausfuehrung |
| --- | --- |
| `/srv/webapps/corapan/data` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab_index` | `hrzadmin:hrzadmin`, Modus `755` |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | `hrzadmin:hrzadmin`, Modus `770` |

## Ausgefuehrte Vorbereitung

Angelegt wurden ausschliesslich die zuvor fehlenden, leeren Zielverzeichnisse:

- `/srv/webapps/corapan/data/blacklab/index`
- `/srv/webapps/corapan/data/blacklab/backups`
- `/srv/webapps/corapan/data/blacklab/quarantine`

Nicht neu angelegt, weil bereits vorhanden:

- `/srv/webapps/corapan/data/blacklab`
- `/srv/webapps/corapan/data/blacklab/export`

## Verifikation nach der Ausfuehrung

### Vollstaendiger Zielbaum

Der Zielbaum ist jetzt vollstaendig vorhanden:

- `/srv/webapps/corapan/data/blacklab`
- `/srv/webapps/corapan/data/blacklab/index`
- `/srv/webapps/corapan/data/blacklab/export`
- `/srv/webapps/corapan/data/blacklab/backups`
- `/srv/webapps/corapan/data/blacklab/quarantine`

### Effektive Rechte des aktuell angelegten Zielbaums

| Pfad | Status nach der Ausfuehrung |
| --- | --- |
| `/srv/webapps/corapan/data/blacklab` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab/index` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab/export` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab/backups` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab/quarantine` | `root:root`, Modus `755` |

### Unveraenderte produktive Referenzpfade

Die vorab erhobenen Referenzpfade waren nach der Strukturvorbereitung unveraendert:

| Pfad | Status nach der Ausfuehrung |
| --- | --- |
| `/srv/webapps/corapan/data` | `root:root`, Modus `755` |
| `/srv/webapps/corapan/data/blacklab_index` | `hrzadmin:hrzadmin`, Modus `755` |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | `hrzadmin:hrzadmin`, Modus `770` |

## Empfohlene Zielrechte fuer den spaeteren Cutover

Die jetzt angelegte Struktur wurde absichtlich nicht normalisiert. Fuer den spaeteren produktiven Cutover ist eine Rechteanpassung sinnvoll, orientiert an den heute aktiven Pfaden:

| Zielpfad | Empfohlener Owner:Group | Empfohlener Modus | Begruendung |
| --- | --- | --- | --- |
| `/srv/webapps/corapan/data/blacklab/index` | `hrzadmin:hrzadmin` | `755` | Soll funktional den heutigen Live-Indexpfad `/srv/webapps/corapan/data/blacklab_index` abloesen, der ebenfalls `755` nutzt. |
| `/srv/webapps/corapan/data/blacklab/export` | `hrzadmin:hrzadmin` | `770` | Soll funktional den heute aktiven Exportpfad `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` abbilden, der restriktiver mit `770` gesetzt ist. |
| `/srv/webapps/corapan/data/blacklab/backups` | `hrzadmin:hrzadmin` | `755` | Passt zu den bestehenden Index-Backup-Pfaden unter `/srv/webapps/corapan/data`, die heute mit `755` vorliegen. |
| `/srv/webapps/corapan/data/blacklab/quarantine` | `hrzadmin:hrzadmin` | `770` | Quarantaene-/Fehlerpfad sollte restriktiver sein als der oeffentliche Parent und nicht weiter geoeffnet werden als noetig. |

## Konflikte und offene Punkte

- Es wurde ein bereits vorhandener Teilbaum vorgefunden: `/srv/webapps/corapan/data/blacklab` mit leerem `export/`.
- Es wurde kein inhaltlicher Konflikt in diesem Teilbaum festgestellt.
- Die aktuellen Live-Pfade bleiben weiterhin ausserhalb des neuen Zielbaums:
  - BlackLab-Index live: `/srv/webapps/corapan/data/blacklab_index`
  - Web-Export live: `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`
- Fuer einen echten Cutover sind weiterhin Repo-/Deploy-/Mount-Aenderungen erforderlich; diese Vorbereitung allein aendert kein Runtime-Verhalten.

## Ergebnis

- Die kanonische Zielstruktur wurde auf Serverebene vollstaendig vorbereitet.
- Es wurden nur leere Zielverzeichnisse angelegt.
- Produktive Pfade und deren Rechte blieben unveraendert.
- Es wurden keine Konflikte festgestellt, die die reine Strukturvorbereitung blockieren.