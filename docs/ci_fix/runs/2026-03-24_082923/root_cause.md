# Root Cause

Warnungs- und Determinismus-Ursachen dieses Folge-Runs:

1. `tests/test_advanced_api_quick.py` war ein Live-Smoke-Skript mit echten `localhost`-HTTP-Aufrufen, lief aber im normalen pytest-Pfad mit und gab Booleans statt Assertions zurueck.
2. Template-Helfer und Tests nutzten `datetime.utcnow`, was zu deprecation-naher, inkonsistenter Zeitbehandlung fuehrte.
3. Die App-Konfiguration emittierte einen operativen Statistik-Hinweis auch waehrend pytest-Imports.
4. Passlib loest intern weiterhin eine bekannte `argon2.__version__`-Deprecation aus; diese stammt nicht aus Repository-Code.

Root-Cause-Entscheidungen:
- Live-Smoke bleibt moeglich, aber explizit markiert als `live`
- Repo-eigene Warnungen werden an der Quelle behoben
- Drittanbieter-Warnung wird nur eng und transparent gefiltert