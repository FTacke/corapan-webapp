document.addEventListener('DOMContentLoaded', function () {
  const listBody = document.getElementById('list-body');
  const refreshBtn = document.getElementById('refresh');
  const createBtn = document.getElementById('create');
  const createDialog = document.getElementById('create-user-dialog');
  const createForm = document.getElementById('create-user-form');
  const cancelCreateBtn = document.getElementById('cancel-create');
  const inviteDialog = document.getElementById('invite-dialog');
  const inviteLinkCode = document.getElementById('invite-link');
  const closeInviteBtn = document.getElementById('close-invite');
  const copyInviteBtn = document.getElementById('copy-invite');
  const userDetailDialog = document.getElementById('user-detail-dialog');
  const userDetailContent = document.getElementById('user-detail-content');
  const userDetailTitle = document.getElementById('user-detail-title');
  const userDetailClose = document.getElementById('user-detail-close');
  const userDetailGenInvite = document.getElementById('user-detail-gen-invite');
  const inviteMeta = document.getElementById('invite-meta');

  function formatDate(isoString) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
  }

  // Role icon mapping for badges
  const roleIcons = {
    admin: 'verified_user',
    editor: 'edit',
    user: 'person'
  };

  function renderRoleBadge(role) {
    const icon = roleIcons[role] || 'person';
    return `
      <span class="md3-badge md3-badge--small md3-badge--role-${role}">
        <span class="material-symbols-rounded md3-badge__icon" aria-hidden="true">${icon}</span>
        ${role}
      </span>
    `;
  }

  function renderStatusBadge(isActive) {
    if (isActive) {
      return `
        <span class="md3-badge md3-badge--status-active">
          <span class="material-symbols-rounded md3-badge__icon" aria-hidden="true">check_circle</span>
          Aktiv
        </span>
      `;
    }
    return `<span class="md3-badge md3-badge--status-inactive">Inaktiv</span>`;
  }

  function renderRow(user) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="md3-body-medium">${user.username}</span></td>
      <td><span class="md3-body-small">${user.email || '-'}</span></td>
      <td>${renderRoleBadge(user.role)}</td>
      <td>${renderStatusBadge(user.is_active)}</td>
      <td class="md3-hide-mobile"><span class="md3-body-small">${formatDate(user.created_at)}</span></td>
      <td class="md3-table__actions">
        <button class="md3-button md3-button--icon edit-user-btn" data-id="${user.id}" title="Bearbeiten" aria-label="Benutzer bearbeiten">
          <span class="material-symbols-rounded">edit</span>
        </button>
        <button class="md3-button md3-button--icon reset-user-btn" data-id="${user.id}" title="Passwort zurücksetzen / Invite erneuern" aria-label="Invite erneuern">
          <span class="material-symbols-rounded">history_edu</span>
        </button>
      </td>
    `;
    return tr;
  }

  function reload() {
    listBody.innerHTML = '<tr class="md3-table__empty-row"><td colspan="6"><div class="md3-empty-inline"><span class="material-symbols-rounded" aria-hidden="true">hourglass_empty</span><span>Lade...</span></div></td></tr>';
    
    fetch('/admin/users')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load users');
        return r.json();
      })
      .then((data) => {
        listBody.innerHTML = '';
        if (!data.items || data.items.length === 0) {
          listBody.innerHTML = `
            <tr class="md3-table__empty-row">
              <td colspan="6">
                <div class="md3-empty-inline">
                  <span class="material-symbols-rounded" aria-hidden="true">person_off</span>
                  <span>Keine Benutzer gefunden.</span>
                </div>
              </td>
            </tr>
          `;
          return;
        }
        data.items.forEach(user => {
          listBody.appendChild(renderRow(user));
        });
        
        // Attach event listeners to new buttons
        document.querySelectorAll('.edit-user-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const uid = e.currentTarget.dataset.id;
            // Fetch detail and show in dialog
            userDetailContent.innerHTML = '<p class="md3-body-small md3-text-variant">Lade Benutzerdaten…</p>';
            userDetailTitle.textContent = `Benutzer: ${user.username}`;
            // attach a small state id on the dialog to keep track
            userDetailDialog.dataset.userId = uid;
            fetch(`/admin/users/${encodeURIComponent(uid)}`)
              .then(r => r.json())
              .then(data => {
                let html = `<div class="md3-stack--dialog">
                    <div><strong>Benutzername:</strong> ${data.username}</div>
                    <div><strong>Email:</strong> ${data.email || '-'}</div>
                    <div><strong>Rolle:</strong> ${data.role}</div>
                    <div><strong>Status:</strong> ${data.is_active ? 'Aktiv' : 'Inaktiv'}</div>
                  </div>`;
                // show recent reset tokens
                if (data.resetTokens && data.resetTokens.length) {
                  html += '<h4 class="md3-title-small">Reset Tokens</h4><ul class="md3-list">';
                  data.resetTokens.forEach(t => {
                    html += `<li class="md3-list-item"><div class="md3-list-item__text">ID: ${t.id}</div><div class="md3-list-item__meta">Erstellt: ${new Date(t.created_at).toLocaleString()} • Läuft ab: ${new Date(t.expires_at).toLocaleString()} ${t.used_at ? '• Verwendet' : ''}</div></li>`;
                  });
                  html += '</ul>';
                } else {
                  html += '<p class="md3-body-small md3-text-variant">Keine kürzlichen Reset-Token.</p>';
                }
                userDetailContent.innerHTML = html;
                try { userDetailDialog.showModal(); } catch (e) { userDetailDialog.setAttribute('open','true'); }
              })
              .catch(err => {
                console.error(err);
                userDetailContent.innerHTML = '<p class="md3-body-small md3-text-error">Fehler beim Laden der Benutzerdaten.</p>';
                try { userDetailDialog.showModal(); } catch (e) { userDetailDialog.setAttribute('open','true'); }
              });
          });
        });

        document.querySelectorAll('.reset-user-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const uid = e.currentTarget.dataset.id;
            if (!confirm('Einen neuen Invite-Link für den Benutzer erzeugen? (bestehende Token bleiben erhalten)')) return;

            fetch(`/admin/users/${encodeURIComponent(uid)}/reset-password`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
            })
            .then(r => r.json())
            .then(resp => {
              if (resp.ok && resp.inviteLink) {
                inviteLinkCode.textContent = resp.inviteLink;
                if (resp.inviteExpiresAt) {
                  inviteMeta.textContent = `Gültig bis: ${new Date(resp.inviteExpiresAt).toLocaleString()}`;
                } else {
                  inviteMeta.textContent = '';
                }
                inviteDialog.showModal();
              } else if (resp.ok) {
                alert('Passwort-Reset erzeugt, aber kein Link erhalten.');
              } else {
                alert('Fehler: ' + (resp.error || 'Unbekannter Fehler'));
              }
            })
            .catch(err => {
              console.error(err);
              alert('Netzwerkfehler beim Anfordern des Reset-Links.');
            });
          });
        });
      })
      .catch((err) => {
        console.error(err);
        listBody.innerHTML = '<tr><td colspan="6" class="md3-text-center md3-text-error">Fehler beim Laden der Benutzer.</td></tr>';
      });
  }

  // Event Listeners
  if (refreshBtn) refreshBtn.addEventListener('click', reload);
  
  if (copyInviteBtn && inviteLinkCode) {
    copyInviteBtn.addEventListener('click', () => {
      const text = inviteLinkCode.textContent || inviteLinkCode.innerText || '';
      navigator.clipboard.writeText(text).then(() => {
        const originalIcon = copyInviteBtn.innerHTML;
        copyInviteBtn.innerHTML = '<span class="material-symbols-rounded">check</span>';
        // update screen-reader live region if present
        const status = document.getElementById('invite-copy-status');
        if (status) status.textContent = 'Invite-Link in die Zwischenablage kopiert.';
        setTimeout(() => {
          copyInviteBtn.innerHTML = originalIcon;
          if (status) status.textContent = '';
        }, 2000);
      }).catch(err => {
        // fallback: inform via live region
        const status = document.getElementById('invite-copy-status');
        if (status) status.textContent = 'Kopieren fehlgeschlagen.';
        console.error('Clipboard error', err);
      });
    });
  }
  
  if (createBtn && createDialog) {
    createBtn.addEventListener('click', () => {
      createForm.reset();
      createDialog.showModal();
      // Put keyboard focus into the username field so users can start typing immediately
      const first = document.getElementById('new-username');
      if (first) {
        // small timeout to ensure showModal has completed in some browsers
        setTimeout(() => first.focus(), 40);
      }
    });
  }

  if (cancelCreateBtn && createDialog) {
    cancelCreateBtn.addEventListener('click', () => {
      createDialog.close();
    });
  }

  if (createForm) {
    createForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(createForm);
      const data = Object.fromEntries(formData.entries());

      fetch('/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.ok) {
          createDialog.close();
          reload();
          if (resp.inviteLink) {
            // place the invite link into the pre/code block (escape handled by textContent)
            inviteLinkCode.textContent = resp.inviteLink;
            // show metadata if provided
            if (resp.inviteExpiresAt) {
              inviteMeta.textContent = `Gültig bis: ${new Date(resp.inviteExpiresAt).toLocaleString()}`;
            } else {
              inviteMeta.textContent = '';
            }
            inviteDialog.showModal();
          } else {
            alert('Benutzer angelegt, aber kein Invite-Link erhalten.');
          }
        } else {
          alert('Fehler: ' + (resp.error || 'Unbekannter Fehler'));
        }
      })
      .catch(err => {
        console.error(err);
        alert('Netzwerkfehler beim Anlegen des Benutzers.');
      });
    });
  }

  if (closeInviteBtn && inviteDialog) {
    closeInviteBtn.addEventListener('click', () => {
      inviteDialog.close();
      inviteLinkCode.textContent = '';
      if (inviteMeta) inviteMeta.textContent = '';
    });
  }

  if (userDetailClose && userDetailDialog) {
    userDetailClose.addEventListener('click', () => {
      try { userDetailDialog.close(); } catch (e) { userDetailDialog.removeAttribute('open'); }
      userDetailContent.innerHTML = '';
      delete userDetailDialog.dataset.userId;
    });
  }

  if (userDetailGenInvite && userDetailDialog) {
    userDetailGenInvite.addEventListener('click', () => {
      const uid = userDetailDialog.dataset.userId;
      if (!uid) return alert('Kein Benutzer ausgewählt');
      if (!confirm('Einen neuen Invite-Link für den Benutzer erzeugen? (bestehende Token bleiben erhalten)')) return;

      fetch(`/admin/users/${encodeURIComponent(uid)}/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(r => r.json())
        .then(resp => {
          if (resp.ok && resp.inviteLink) {
            inviteLinkCode.textContent = resp.inviteLink;
            if (resp.inviteExpiresAt) inviteMeta.textContent = `Gültig bis: ${new Date(resp.inviteExpiresAt).toLocaleString()}`;
            inviteDialog.showModal();
            // refresh user detail to reflect new token
            const uid2 = userDetailDialog.dataset.userId;
            fetch(`/admin/users/${encodeURIComponent(uid2)}`).then(r => r.json()).then(d => {
              // update content quickly
              let html = `<div class="md3-stack--dialog">
                    <div><strong>Benutzername:</strong> ${d.username}</div>
                    <div><strong>Email:</strong> ${d.email || '-'}</div>
                    <div><strong>Rolle:</strong> ${d.role}</div>
                    <div><strong>Status:</strong> ${d.is_active ? 'Aktiv' : 'Inaktiv'}</div>
                  </div>`;
              if (d.resetTokens && d.resetTokens.length) {
                html += '<h4 class="md3-title-small">Reset Tokens</h4><ul class="md3-list">';
                d.resetTokens.forEach(t => {
                  html += `<li class="md3-list-item"><div class="md3-list-item__text">ID: ${t.id}</div><div class="md3-list-item__meta">Erstellt: ${new Date(t.created_at).toLocaleString()} • Läuft ab: ${new Date(t.expires_at).toLocaleString()} ${t.used_at ? '• Verwendet' : ''}</div></li>`;
                });
                html += '</ul>';
              } else {
                html += '<p class="md3-body-small md3-text-variant">Keine kürzlichen Reset-Token.</p>';
              }
              userDetailContent.innerHTML = html;
            });
          } else if (resp.ok) {
            alert('Passwort-Reset erzeugt, aber kein Link erhalten.');
          } else {
            alert('Fehler: ' + (resp.error || 'Unbekannter Fehler'));
          }
        })
        .catch(err => {
          console.error(err);
          alert('Netzwerkfehler beim Erzeugen des Reset-Links.');
        });
    });
  }

  // Initial load
  reload();
});
