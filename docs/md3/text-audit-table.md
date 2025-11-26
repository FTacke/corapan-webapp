# MD3 Text Audit Table

> **Erstellt:** 2025-01-XX (Commit 5 — Navigation/Auth Audit Implementation)  
> **Regel:** Öffentlicher Bereich → Spanisch (ES), Interner Bereich → Deutsch (DE), `Login`/`Logout` → Neutral (unübersetzt)

---

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Konform mit Sprachregel |
| ⚠️ | Mischung / Inkonsistenz |
| 🇪🇸 | Spanisch (öffentlich) |
| 🇩🇪 | Deutsch (intern) |
| 🌐 | Neutral (Login/Logout) |

---

## 1. Navigation & Top App Bar

| Komponente | Text | Sprache | Status |
|------------|------|---------|--------|
| `_top_app_bar.html` | Avatar-Menü "Profil" | 🇩🇪 DE | ✅ |
| `_top_app_bar.html` | Avatar-Menü "Benutzer" | 🇩🇪 DE | ✅ |
| `_top_app_bar.html` | Avatar-Menü "Logout" | 🌐 Neutral | ✅ |
| `_top_app_bar.html` | Login-Button aria-label | 🌐 "Login" | ✅ |
| `_navigation_drawer.html` | Modal Drawer "Profil" | 🇩🇪 DE | ✅ |
| `_navigation_drawer.html` | Modal Drawer "Logout" | 🌐 Neutral | ✅ |
| `_navigation_drawer.html` | Modal Drawer "Login" | 🌐 Neutral | ✅ |
| `_navigation_drawer.html` | Standard Drawer "Profil" | 🇩🇪 DE | ✅ |
| `_navigation_drawer.html` | Standard Drawer "Logout" | 🌐 Neutral | ✅ |
| `_navigation_drawer.html` | Standard Drawer "Login" | 🌐 Neutral | ✅ |

---

## 2. Auth-Templates (Öffentlich → Spanisch)

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `login.html` | Título "Iniciar sesión" | 🇪🇸 ES | ✅ |
| `login.html` | Eyebrow "Acceso" | 🇪🇸 ES | ✅ |
| `login.html` | Intro "Ingresa tus credenciales..." | 🇪🇸 ES | ✅ |
| `login.html` | Label "Usuario o correo electrónico" | 🇪🇸 ES | ✅ |
| `login.html` | Label "Contraseña" | 🇪🇸 ES | ✅ |
| `login.html` | Link "¿Olvidaste tu contraseña?" | 🇪🇸 ES | ✅ |
| `login.html` | Button "Entrar" | 🇪🇸 ES | ✅ |
| `password_forgot.html` | Título "Recuperar contraseña" | 🇪🇸 ES | ✅ |
| `password_forgot.html` | Eyebrow "Acceso" | 🇪🇸 ES | ✅ |
| `password_forgot.html` | Label "Correo electrónico o usuario" | 🇪🇸 ES | ✅ |
| `password_forgot.html` | Buttons "Cancelar", "Enviar" | 🇪🇸 ES | ✅ |
| `password_reset.html` | Título "Restablecer contraseña" | 🇪🇸 ES | ✅ |
| `password_reset.html` | Eyebrow "Acceso" | 🇪🇸 ES | ✅ |
| `password_reset.html` | Labels "Nueva contraseña", "Confirmar" | 🇪🇸 ES | ✅ |
| `password_reset.html` | Button "Guardar nueva contraseña" | 🇪🇸 ES | ✅ |

---

## 3. Auth-Templates (Intern → Deutsch)

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `account_profile.html` | Título "Profil" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Eyebrow "Konto" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Section "Grunddaten" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Labels "Benutzername", "E-Mail" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Button "Speichern" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Section "Zugang" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Link "Passwort ändern" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Section "Gefahrenzone" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Link "Konto löschen" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Dialog "E-Mail-Adresse ändern" | 🇩🇪 DE | ✅ |
| `account_profile.html` | Dialog Buttons "Abbrechen", "Speichern" | 🇩🇪 DE | ✅ |
| `account_password.html` | Título "Passwort ändern" | 🇩🇪 DE | ✅ |
| `account_password.html` | Eyebrow "Konto" | 🇩🇪 DE | ✅ |
| `account_password.html` | Labels "Altes/Neues Passwort", "bestätigen" | 🇩🇪 DE | ✅ |
| `account_password.html` | Buttons "Abbrechen", "Passwort ändern" | 🇩🇪 DE | ✅ |
| `account_delete.html` | Título "Account löschen" | 🇩🇪 DE | ✅ |
| `account_delete.html` | Eyebrow "Konto" | 🇩🇪 DE | ✅ |
| `account_delete.html` | Card "Bestätigung erforderlich" | 🇩🇪 DE | ✅ |
| `account_delete.html` | Info "irreversible Aktion" | 🇩🇪 DE | ✅ |
| `account_delete.html` | Buttons "Abbrechen", "Löschen" | 🇩🇪 DE | ✅ |

---

## 4. Admin-Templates (Intern → Deutsch)

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `admin_users.html` | Título "Benutzerverwaltung" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Eyebrow "Admin" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Intro "Verwalte Benutzerkonten..." | 🇩🇪 DE | ✅ |
| `admin_users.html` | Placeholder "Benutzer suchen" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Buttons "Aktualisieren", "Benutzer anlegen" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Table Headers (Benutzername, Email, Rolle, Status, etc.) | 🇩🇪 DE | ✅ |
| `admin_users.html` | Dialog "Neuen Benutzer anlegen" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Dialog "Benutzer angelegt" | 🇩🇪 DE | ✅ |
| `admin_users.html` | Dialog Buttons "Abbrechen", "Anlegen", "Schließen" | 🇩🇪 DE | ✅ |
| `admin_users.html` | User Detail Dialog "Invite erneuern" | 🇩🇪 DE | ✅ |

---

## 5. Öffentliche Seiten (Spanisch)

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `index.html` | Card "Proyecto" + "Saber más" | 🇪🇸 ES | ✅ |
| `index.html` | Card "Corpus" + "Abrir corpus" | 🇪🇸 ES | ✅ |
| `index.html` | Card "Atlas" + "Explorar atlas" | 🇪🇸 ES | ✅ |
| `atlas.html` | Título "Atlas panhispánico" | 🇪🇸 ES | ✅ |
| `atlas.html` | Labels "Capitales/emisoras nacionales/regionales" | 🇪🇸 ES | ✅ |
| `corpus_guia.html` | Título "Guía paso a paso..." | 🇪🇸 ES | ✅ |
| `corpus_guia.html` | All content (Consulta Simple, Modo Avanzado, etc.) | 🇪🇸 ES | ✅ |
| `proyecto_overview.html` | Título "El proyecto CO.RA.PAN" | 🇪🇸 ES | ✅ |
| `proyecto_overview.html` | All content (Marco conceptual, Diseño comparativo, etc.) | 🇪🇸 ES | ✅ |
| `advanced.html` | Título "Consultar corpus" | 🇪🇸 ES | ✅ |
| `advanced.html` | Tabs "Consulta simple", "Modo avanzado", "Token" | 🇪🇸 ES | ✅ |
| `advanced.html` | Labels "Consulta", "Tipo", "Forma", "Lema" | 🇪🇸 ES | ✅ |
| `player.html` | Card "Metadatos" | 🇪🇸 ES | ✅ |
| `player.html` | Card "Marcar letras" | 🇪🇸 ES | ✅ |
| `player.html` | Card "Atajos de teclado" | 🇪🇸 ES | ✅ |
| `player.html` | Buttons "Marcar", Tooltips | 🇪🇸 ES | ✅ |
| `admin_dashboard.html` | Título "Panel Administrativo" | 🇪🇸 ES | ⚠️ |
| `admin_dashboard.html` | Cards "Visitas", "Acceso al Corpus", "Búsquedas" | 🇪🇸 ES | ⚠️ |

> **Hinweis `admin_dashboard.html`:** Admin-Dashboard ist derzeit auf Spanisch. Gemäß Sprachregel sollte es auf Deutsch sein (interner Bereich). → **TODO: Prüfen ob gewollt.**

---

## 6. Rechtliche Seiten (Deutsch)

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `impressum.html` | Título "Impressum" | 🇩🇪 DE | ✅ |
| `impressum.html` | Eyebrow "Rechtliche Informationen" | 🇩🇪 DE | ✅ |
| `impressum.html` | All content (Anbieter, Postanschrift, Haftung, etc.) | 🇩🇪 DE | ✅ |
| `privacy.html` | Título "Datenschutzerklärung" | 🇩🇪 DE | ✅ |
| `privacy.html` | Eyebrow "Rechtliche Informationen" | 🇩🇪 DE | ✅ |
| `privacy.html` | All content (Verantwortlicher, Zweck, JWT, etc.) | 🇩🇪 DE | ✅ |

---

## 7. Footer

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `footer.html` | Link "Impressum" | 🇩🇪 DE | ✅ |
| `footer.html` | Link "Datenschutz" | 🇩🇪 DE | ✅ |
| `footer.html` | Copyright Text | 🇩🇪 DE | ✅ |

---

## 8. Error Pages

| Template | Text | Sprache | Status |
|----------|------|---------|--------|
| `400.html` | "Solicitud Incorrecta" | 🇪🇸 ES | ✅ |
| `400.html` | Buttons "Intentar de nuevo", "Volver al inicio" | 🇪🇸 ES | ✅ |
| `401.html` | "Zugang nicht autorisiert" | 🇩🇪 DE | ⚠️ |
| `401.html` | Buttons "Anmelden", "Zur Startseite" | 🇩🇪 DE | ⚠️ |
| `403.html` | "Acceso Prohibido" | 🇪🇸 ES | ✅ |
| `403.html` | Buttons "Volver al inicio", "Página anterior" | 🇪🇸 ES | ✅ |
| `404.html` | "Página No Encontrada" | 🇪🇸 ES | ✅ |
| `404.html` | Buttons "Volver al inicio", "Página anterior" | 🇪🇸 ES | ✅ |
| `500.html` | "Error Interno del Servidor" | 🇪🇸 ES | ✅ |
| `500.html` | Buttons "Recargar página", "Volver al inicio" | 🇪🇸 ES | ✅ |

> **Hinweis `401.html`:** 401 (Unauthorized) ist auf Deutsch, andere Error-Pages auf Spanisch. Da 401 den User zum Login leitet (öffentlicher Flow), sollte es evtl. Spanisch sein. → **TODO: Entscheiden ob Deutsch oder Spanisch.**

---

## Zusammenfassung

| Bereich | Sprache | Konformität |
|---------|---------|-------------|
| Navigation (Avatar, Drawer) | DE + Neutral | ✅ |
| Auth (Login/Password) | ES | ✅ |
| Auth (Account/Profil) | DE | ✅ |
| Admin (Users) | DE | ✅ |
| Admin (Dashboard) | ES | ⚠️ TODO |
| Öffentliche Seiten | ES | ✅ |
| Rechtliche Seiten | DE | ✅ |
| Footer | DE | ✅ |
| Error Pages | ES (außer 401) | ⚠️ 401=DE |

---

## Offene Punkte

1. **`admin_dashboard.html`**: Aktuell Spanisch, sollte gemäß Regel Deutsch sein (Admin = intern).
2. **`401.html`**: Aktuell Deutsch, andere Error-Pages sind Spanisch. Entscheiden ob Login-Redirect-Flow öffentlich (→ ES) oder intern (→ DE).
