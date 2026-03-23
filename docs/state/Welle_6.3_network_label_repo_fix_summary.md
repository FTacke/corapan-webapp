# Welle 6.3 Network Label Repo Fix Summary

Datum: 2026-03-20
Umgebung: Production compose repo fix, statische Verifikation ohne Server-Eingriff
Scope: minimal-invasive Angleichung des logischen Compose-Netzwerk-Keys an die bestehende Produktionsrealitaet

## Root Cause

Der Konflikt lag nicht im realen Produktionsnetzwerk-Namen, sondern in der logischen Compose-Netzwerk-ID im Repo. Das bestehende aktive Produktionsnetzwerk heisst bereits `corapan-network-prod`, traegt aber ein Legacy-Compose-Label fuer denselben logischen Namen, waehrend das Repo noch den abweichenden Key `corapan-prod` verwendete. Dadurch konnte Compose V2 das vorhandene Netzwerk trotz passendem Realnamen als inkonsistent bewerten.

## Geaenderte Dateien

- `infra/docker-compose.prod.yml`
- `docs/state/Welle_6.3_network_label_repo_fix_summary.md`
- `docs/changes/2026-03-20-wave6.3-network-label-repo-fix.md`
- `docs/state/instance-structure-unification-plan.md`

## Exakte Aenderung

- alter logischer Netzwerk-Key: `corapan-prod`
- neuer logischer Netzwerk-Key: `corapan-network-prod`
- unveraenderter realer Netzwerkname: `name: corapan-network-prod`

Angepasst wurden ausschliesslich:

- der Netzwerkschluessel unter `networks:`
- die beiden Service-Referenzen von `db` und `web`

## Was bewusst NICHT geaendert wurde

- kein `external: true`
- kein Wechsel des Compose-Projektnamens
- keine Umbenennung des realen Netzwerks
- keine Aenderung an PostgreSQL/Auth
- keine Aenderung an Analytics
- keine Aenderung an BlackLab
- keine Aenderung an Volumes, Mounts oder Datenpfaden
- keine Aenderung an Containernamen
- keine Aenderung am Server, Runner oder Deploy-Skript
- keine Docker-Kommandos mit Seiteneffekt

## Konfigurationsklassifikation

- live Produktionsrealitaet aus Forensik: aktiv
  - Projektname `infra`
  - reales Netzwerk `corapan-network-prod`
  - Compose V2 vorhanden
- `infra/docker-compose.prod.yml` vor dem Fix: aktiv, aber inkonsistent
  - realer Netzwerkname korrekt
  - logischer Netzwerk-Key abweichend und damit gefaehrlich fuer Compose-V2-Ownership-Pruefung
- `scripts/deploy_prod.sh`: aktiv, aber fuer diesen Fix unveraendert
- `src/app/config/__init__.py`: fuer diesen Fix nicht entscheidend; keine Netzwerk-Key-Steuerung

Gewinnende Quelle fuer den Fix war die Produktionsrealitaet zusammen mit der kanonischen Produktions-Compose-Datei.

## Statische Verifikation

Nach der Repo-Aenderung wurde die Produktions-Compose-Datei statisch gerendert.

Geprueft wurde:

- der logische Netzwerk-Key ist jetzt `corapan-network-prod`
- der reale Netzwerkname bleibt `corapan-network-prod`
- keine Service-Referenz auf `corapan-prod` bleibt im Repo zurueck
- der statische Render zeigt weiterhin das Produktionsnetzwerk unter `networks.corapan-network-prod.name = corapan-network-prod`

Der Projektname bleibt fuer den naechsten Deploy unveraendert bei `infra`; an der Projektbenennung wurde im Repo nichts geaendert.

## Risikoabschaetzung fuer den naechsten Deploy

Der Fix ist klein und auf die logische Netzwerk-ID im Compose-File begrenzt. Er sollte Compose V2 erlauben, das bereits existente Produktionsnetzwerk als zum Stack gehoerig zu erkennen, ohne ein neues Netzwerk anlegen zu muessen. Restrisiko bleibt nur dann, wenn auf dem Server zusaetzlich weitere historische Label- oder Projektinkonsistenzen ausserhalb dieses belegten Konflikts existieren.