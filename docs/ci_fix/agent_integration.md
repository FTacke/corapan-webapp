# Agent Integration

Dieses Dokument haelt fest, welche CI-/Test-Lessons aus dem Reparaturlauf in die Agent-Governance uebernommen wurden.

## Integrierte Regeln

1. Root-CI-Wahrheit bleibt `.github/workflows/*.yml`.
2. Fake-Green-Muster sind verboten:
   - kein `|| true` an echten Qualitaetspruefungen
   - kein Ersetzen von Tests durch Platzhalter-`echo`
   - kein stilles `continue-on-error` fuer Pflichtgates
3. `fast-checks` muss schnell, servicefrei und deterministisch bleiben.
4. Live-, Browser-, localhost-, BlackLab- oder grosse Daten-Tests muessen explizit markiert werden und gehoeren nicht in die Default-Pytest-Selektion.
5. PostgreSQL bleibt Pflicht fuer Auth/Core-Workflows; SQLite-Fallbacks sind fuer diese Pfade auch in der CI unzulaessig.
6. Strikte Config-Regeln bleiben fachlich bestehen, duerfen aber Python-Import und Test-Collection nicht abbrechen. Erzwingung gehoert in App-Config-Laden oder in den konkreten Laufzeitpfad.
7. Repo-eigene Warnings muessen bereinigt werden; Drittanbieter-Warnings duerfen nur eng gefiltert werden.
8. Hash-Kompatibilitaet wird ueber fokussierte Tests abgesichert, nicht ueber eine Vollsuite-Matrix fuer `argon2` und `bcrypt`.

## Aktualisierte Steuerdateien

- `AGENTS.md`
- `app/AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/skills/config-validation/SKILL.md`
- `.github/skills/change-documentation/SKILL.md`

## Zielbild

Agents sollen kuenftig:

- CI-Reparaturen nicht kosmetisch gestalten
- Tests korrekt klassifizieren statt das Produkt fuer veraltete Tests zu verbiegen
- Runtime-Konfigurationshaerte mit Import-/Testbarkeit vereinbar halten
- Dokumentation und Governance direkt zusammen mit der technischen Aenderung aktualisieren