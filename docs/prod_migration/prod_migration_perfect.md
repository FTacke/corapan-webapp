# Prod Migration Plan — Perfect Target State

Basierend auf dem bisherigen Plan fileciteturn0file0 und dem inzwischen erreichten Ist-Stand gilt ab jetzt dieses präzisierte Zielbild und diese Reihenfolge.

## 1. Ausgangslage jetzt

### Bereits erreicht

- Prod ist aktuell stabil deployed.
- App, Auth, Postgres, BlackLab und Audio laufen produktiv.
- Der aktuelle produktive Code-Stand ist sauber auf `main`.
- Der technische Deploy-Pfad über GitHub Actions funktioniert.

### Noch nicht erreicht

- Die **Server-Verzeichnisstruktur in prod ist noch nicht im Zielzustand**.
- Es gibt noch eine **Mischform** aus kanonischen Pfaden unter `corapan/` und einer alten bzw. übergangsweisen Parallelwelt.
- Es ist noch nicht hart ausgeschlossen, dass Teilkomponenten aus alten Orten lesen oder in alte Orte schreiben.
- Die Maintenance-Pipeline muss nach der Umstellung noch gegen die endgültigen Zielpfade verifiziert werden.

---

## 2. Kanonisches Zielbild

Das Ziel ist **nicht** `runtime/corapan/...` als dauerhafte Betriebsstruktur.

Das Ziel ist dieses klare Layout unter dem Workspace-/Server-Root `corapan/`:

```text
corapan/
├─ .github/
├─ app/                     # aktuell lokal noch webapp/, später Rename
├─ maintenance_pipelines/
├─ data/
│  ├─ blacklab/             # alle BlackLab-Indizes und nur dort
│  ├─ config/               # datenbezogene Konfiguration, falls vorgesehen
│  ├─ db/                   # persistente DB-Daten, sofern dateibasiert relevant
│  ├─ public/               # öffentliches Datenmaterial / Exporte
│  └─ ... weitere echte Datendirs
├─ media/                   # große Medienbestände
└─ ... weitere Root-Dateien
```

### Daraus folgt zwingend

1. **BlackLab liegt kanonisch unter `corapan/data/blacklab/`.**
2. **Media liegt kanonisch unter `corapan/media/`.**
3. **App-Code liegt kanonisch unter `corapan/app/`** (aktuell Übergang: lokal noch `webapp/`).
4. **`runtime/corapan/...` ist kein Endzustand und muss verschwinden.**
5. **Alte BlackLab-Orte müssen nach erfolgreicher Migration gelöscht werden**, damit es keine doppelte Wahrheit mehr gibt.

---

## 3. Nicht verhandelbare Migrationsziele

Die Migration ist erst dann fertig, wenn alle folgenden Punkte erfüllt sind:

### A. BlackLab sauber und eindeutig

- Alle produktiv genutzten BlackLab-Indizes liegen vollständig unter `corapan/data/blacklab/`.
- Es gibt **keinen produktiv relevanten zweiten Index-Ort** mehr.
- Alle alten Index-Orte sind nach Verifikation gelöscht oder klar archiviert und vom Betrieb getrennt.
- BlackLab liest nachweislich nur noch vom kanonischen Ort.

### B. Auth/Postgres vollständig portiert und abgesichert

- Auth zeigt nachweislich auf die richtige produktive PostgreSQL-Instanz.
- Alle dafür nötigen Env-/Config-Werte sind sauber an den Zielpfaden verankert.
- Keine Altpfade, keine versehentlichen Fallbacks, keine impliziten Defaults.
- Rollback-/Recovery bleibt vor und nach der Umstellung klar möglich.

### C. Media vollständig am richtigen Ort

- Die großen Media-Inhalte liegen vollständig unter `corapan/media/`.
- Es gibt keine alten Medien-Orte, aus denen produktiv noch gelesen wird.
- Verschieben erfolgt so, dass keine Daten verloren gehen und keine inkonsistenten Teilstände übrig bleiben.

### D. Compose / Deploy / Skripte lesen nur noch aus dem Zielbild

- Alle produktionsrelevanten Mounts zeigen auf die endgültigen Orte.
- Deploy-Skripte, Compose-Dateien und Hilfsskripte referenzieren keine Altpfade mehr.
- Es ist technisch ausgeschlossen, dass ein späterer Deploy wieder in alte Orte schreibt.

### E. Maintenance-Pipeline bindet an die finalen Pfade

- `maintenance_pipelines` und die darunter aufgerufenen Skripte zeigen auf die finalen Serverziele.
- Die rsync-Wege sind nach der Migration einmal praktisch verifiziert.
- Ein Testlauf landet nachweislich im richtigen Zielverzeichnis.

---

## 4. Harte Leitprinzipien

1. **Prod-Stabilität vor Schönheitsumbau.** Keine Strukturmigration im Blindflug.
2. **Erst kopieren/verifizieren, dann umschalten, dann löschen.** Nie direkt destruktiv arbeiten.
3. **Es darf am Ende nur noch eine Wahrheit pro Datenklasse geben.**
4. **Große Medienbestände werden kontrolliert verschoben, nicht improvisiert.**
5. **BlackLab-Altorte bleiben nicht „zur Sicherheit“ aktiv liegen.** Entweder archiviert außerhalb des aktiven Pfads oder gelöscht.
6. **Auth/Postgres ist Go/No-Go-kritisch.** Ohne klaren Recovery-Pfad keine Strukturmigration.
7. **Jeder operative Schritt muss dokumentiert werden.**

---

## 5. Zielgerichtete Migrationsphasen ab heutigem Stand

## Phase 0 — Zielbild festziehen

### Ziel

Alle Beteiligten arbeiten ab jetzt gegen **ein einziges Sollbild**: `corapan/app`, `corapan/data/...`, `corapan/media`, `corapan/maintenance_pipelines`, ohne dauerhafte `runtime/corapan`-Parallelwelt.

### Ergebnis

- Dieses Dokument ist die neue Referenz.
- Alte Formulierungen, die `runtime/corapan` als Zielbild darstellen, gelten nicht mehr.

---

## Phase 1 — Forensik: exakte Prod-Pfadrealität erfassen

### Ziel

Bevor etwas verschoben wird, muss exakt feststehen, **welche produktiven Daten aktuell wo liegen** und **woraus die laufenden Dienste tatsächlich lesen**.

### Prüfpunkte

- Wo liegen die aktuell genutzten BlackLab-Indizes genau?
- Gibt es weitere alte oder doppelte BlackLab-Orte?
- Wo liegen Media-Bestände aktuell?
- Wo liegen Auth-/Postgres-relevante Config- und Env-Dateien?
- Welche Host-Pfade sind aktiv in Container gemountet?
- Welche Skripte referenzieren heute noch `runtime/...` oder andere Altpfade?
- Welche Teile des laufenden Systems lesen noch aus Mischpfaden?

### Ergebnis

- vollständige Pfadmatrix für prod
- Liste aller Altorte
- Liste aller produktiv tatsächlich genutzten Orte

### Ablage

`docs/prod_migration/YYYY-MM-DD_prod_path_reality_audit.md`

---

## Phase 2 — Soll/Ist-Mapping und Migrationsmatrix

### Ziel

Für jede relevante Datenklasse wird exakt dokumentiert:

- **Ist-Ort**
- **Ziel-Ort**
- **Migrationsmethode**
- **Verifikation**
- **Löschkriterium des Altorts**

### Datenklassen mindestens

- BlackLab-Indizes
- Media
- Auth-/Postgres-nahe Config
- sonstige persistente Daten unter `data/`
- Deploy-/Compose-Pfadreferenzen
- Maintenance-Pipeline-Zielpfade

### Ergebnis

Eine Tabelle der Form:

| Bereich | Ist-Ort | Ziel-Ort | Migrationsart | Verifikation | Altort löschen wann |
|---|---|---|---|---|---|
| BlackLab | ... | `corapan/data/blacklab/...` | kopieren/umschalten | Suchtest + Mounttest | nach positivem Test |
| Media | ... | `corapan/media/...` | rsync/move | Dateizahl/Größe/Stichprobe | nach Vollvergleich |
| ... | ... | ... | ... | ... | ... |

### Ablage

`docs/prod_migration/YYYY-MM-DD_prod_mapping_matrix.md`

---

## Phase 3 — Recovery-Schutz vor Eingriffen

### Ziel

Bevor produktive Datenpfade umgestellt werden, müssen Backup- und Wiederherstellungswege belastbar vorliegen.

### Mindestanforderungen

#### BlackLab
- aktueller Index-Bestand inventarisiert
- Fallback klar: auf alten, unveränderten Stand zurückschalten oder alten Pfad temporär remounten

#### Auth/Postgres
- Recovery-Plan schriftlich
- gesicherte DB-/Volume-Strategie
- Health-/Login-Checks definiert

#### Media
- Verschiebe- oder Sync-Verfahren mit Vergleichslog
- klarer Nachweis, dass Quelle und Ziel identisch sind, bevor Quelle gelöscht wird

### Ablage

`docs/prod_migration/YYYY-MM-DD_recovery_guardrails.md`

---

## Phase 4 — BlackLab-Migration auf den kanonischen Ort

### Ziel

Alle produktiven BlackLab-Indizes liegen nur noch unter `corapan/data/blacklab/`.

### Reihenfolge

1. Zielverzeichnis `corapan/data/blacklab/` final anlegen.
2. Bestehende produktive Indizes dorthin kopieren oder kontrolliert verschieben.
3. Größe/Inhalt/Struktur des Zielbestands verifizieren.
4. Compose-/Mount-/Config-Pfade auf den kanonischen Ort umstellen.
5. BlackLab kontrolliert neu starten.
6. Suchtests und erweiterte Suchtests ausführen.
7. Nach positiver Verifikation: alte BlackLab-Orte löschen oder klar außerhalb der aktiven Pfade archivieren.

### Fertig erst wenn

- BlackLab nur noch vom Zielort liest
- keine Altpfad-Mounts mehr aktiv sind
- alte Index-Orte nicht mehr versehentlich nutzbar sind

### Ablage

`docs/prod_migration/YYYY-MM-DD_blacklab_cutover.md`

---

## Phase 5 — Media-Migration auf den kanonischen Ort

### Ziel

Alle großen Medienbestände liegen nur noch unter `corapan/media/`.

### Reihenfolge

1. Zielstruktur unter `corapan/media/` final anlegen.
2. Bestehende Medien per kontrolliertem Verfahren übertragen.
3. Dateimengen, Größen und Stichproben vergleichen.
4. App-/Mount-/Config-Pfade auf den Zielort festziehen.
5. Medien in der App praktisch testen.
6. Erst danach Altorte löschen.

### Wichtiger Punkt

Bei Media ist „schnell verschieben“ die falsche Strategie. Wegen Größe und Risiko braucht es einen kontrollierten Abgleich, nicht Bauchgefühl.

### Ablage

`docs/prod_migration/YYYY-MM-DD_media_cutover.md`

---

## Phase 6 — Auth/Postgres und produktive Config auf Zielpfade festziehen

### Ziel

Alle produktiv relevanten Auth-/DB-/Config-Pfade und Env-Quellen sind auf den finalen Strukturzustand ausgerichtet.

### Prüfpunkte

- `AUTH_DATABASE_URL` und weitere Pflichtwerte kommen aus der richtigen Quelle.
- Keine Alt-Env-Datei, kein Altpfad, kein impliziter Fallback bleibt aktiv.
- Compose und Deploy referenzieren nur noch die finalen Orte.
- Login, Session, Admin-nahe Pfade und DB-Health sind geprüft.

### Ergebnis

Ein Zustand, in dem ein späterer Redeploy nicht wieder in eine alte Struktur zurückkippt.

### Ablage

`docs/prod_migration/YYYY-MM-DD_auth_config_finalization.md`

---

## Phase 7 — Altorte und Parallelwelten endgültig entfernen

### Ziel

Die Übergangsstruktur wird vollständig beendet.

### Das umfasst ausdrücklich

- alte BlackLab-Orte löschen
- alte Media-Orte löschen
- alte produktiv irrelevante Runtime-/Parallelpfade entfernen
- Mounts und Skripte von Altpfaden bereinigen
- sicherstellen, dass keine Komponente mehr aus Altorten lesen kann

### Wichtiger Punkt

Die Migration ist **nicht** fertig, solange Altorte noch so existieren, dass sie versehentlich weitergenutzt werden könnten.

### Ablage

`docs/prod_migration/YYYY-MM-DD_legacy_path_cleanup.md`

---

## Phase 8 — Maintenance-Pipeline gegen Endzustand verifizieren

### Ziel

Nach der eigentlichen Strukturmigration wird geprüft, ob die operative Pflegekette wirklich an die neuen Zielorte gebunden ist.

### Prüfpunkte

- `maintenance_pipelines/_1_blacklab/blacklab_export.py`
- `maintenance_pipelines/_2_deploy/...`
- ggf. aufgerufene Skripte im App-Code oder unter `scripts/`
- rsync-Zielpfade für BlackLab
- rsync-Zielpfade für Media oder andere Daten
- Publish-/Deploy-Helfer

### Testprinzip

- nicht nur Code lesen
- mindestens ein kontrollierter Testlauf oder Dry-Run, der zeigt, dass Daten an den finalen Zielorten landen

### Fertig erst wenn

- die Maintenance-Pipeline nachweislich in die neuen Orte liefert
- kein Schritt mehr an alte Pfade gebunden ist

### Ablage

`docs/prod_migration/YYYY-MM-DD_maintenance_pipeline_verification.md`

---

## Phase 9 — Danach erst Repo-/Namensumbau

### Ziel

Erst wenn prod strukturell sauber und stabil ist, folgen die rein organisatorischen Repo-Schritte:

- `webapp/` → `app/`
- Git-Root auf `corapan/` anheben

### Warum erst dann

Weil dieser Umbau sonst zusätzlich zu laufenden Servermigrationen eine zweite Fehlerdimension eröffnet.

### Ablage

`docs/prod_migration/YYYY-MM-DD_repo_root_cutover_plan.md`

---

## 6. Definition von „Migration abgeschlossen"

Die Prod-Migration ist erst abgeschlossen, wenn **alle** folgenden Aussagen wahr sind:

- Die laufende produktive App nutzt nur noch das kanonische Layout unter `corapan/`.
- BlackLab liest ausschließlich aus `corapan/data/blacklab/`.
- Alle alten BlackLab-Orte sind gelöscht oder klar aus dem aktiven Betrieb entfernt.
- Media liegt ausschließlich unter `corapan/media/`.
- Auth/Postgres und produktive Config sind auf finalen Pfaden verankert.
- Compose, Deploy und Hilfsskripte referenzieren keine Altpfade mehr.
- Die Maintenance-Pipeline schreibt nachweislich an die finalen Orte.
- Ein Redeploy hält diesen Zustand stabil.

Wenn einer dieser Punkte noch offen ist, ist die Migration noch nicht fertig.

---

## 7. Go / No-Go für einzelne operative Schritte

### Go

Ein Migrationsschritt ist vertretbar, wenn:

- Ist- und Zielpfad exakt bekannt sind
- Recovery klar ist
- Verifikation vorab definiert ist
- Altort nicht voreilig gelöscht wird

### No-Go

Ein Migrationsschritt ist nicht vertretbar, wenn:

- unklar ist, woraus die laufende Instanz liest
- unklar ist, ob ein Pfad produktiv aktiv ist
- BlackLab oder Auth im Fehlerfall nicht schnell wiederherstellbar sind
- Altorte gelöscht werden sollen, bevor der Zielpfad praktisch verifiziert ist

---

## 8. Nächste konkrete Reihenfolge ab jetzt

1. **Dieses Zielbild als verbindlich festhalten.**
2. **Prod-Pfadforensik aktualisieren**: BlackLab, Media, Auth/Postgres, Config, Mounts.
3. **Migrationsmatrix erstellen**: Ist-Ort → Ziel-Ort pro Bereich.
4. **Recovery-Guardrails absichern**.
5. **BlackLab auf `corapan/data/blacklab/` migrieren und Altorte entfernen.**
6. **Media auf `corapan/media/` migrieren und Altorte entfernen.**
7. **Auth-/Config-/Compose-/Deploy-Pfade auf finalen Zustand festziehen.**
8. **Alte Parallelwelt vollständig bereinigen.**
9. **Maintenance-Pipeline per rsync-/Deploy-Test gegen Zielpfade verifizieren.**
10. **Erst danach `webapp -> app` und später Git-Root-Cutover.**

---

## 9. Kurzfazit

Der Plan muss aktualisiert werden. Nicht weil der alte Plan nutzlos wäre, sondern weil er in einem zentralen Punkt nicht scharf genug war: Das **echte Zielbild** ist nicht irgendeine Runtime-Zwischenwelt, sondern die klare kanonische Struktur unter `corapan/` mit `data/blacklab`, `data/...`, `media`, `app` und ohne konkurrierende Altorte. Diese Fassung präzisiert genau das und macht das notwendige Aufräumen zu einem verpflichtenden Teil der Migration.
