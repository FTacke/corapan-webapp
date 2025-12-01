import { showError, showSuccess, clearAlert } from '/static/js/md3/alert-utils.js';

/**
 * Load current profile data from API and display in the UI
 */
async function loadProfileData() {
  const usernameEl = document.getElementById('current-username');
  const emailEl = document.getElementById('current-email');
  
  try {
    const response = await fetch('/auth/account/profile', {
      method: 'GET',
      credentials: 'same-origin'
    });
    
    if (response.ok) {
      const data = await response.json();
      if (usernameEl) usernameEl.textContent = data.username || '–';
      if (emailEl) emailEl.textContent = data.email || '–';
    } else {
      console.warn('Failed to load profile data:', response.status);
    }
  } catch (e) {
    console.error('Error loading profile data:', e);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  // Load current profile data via API
  await loadProfileData();

  // Initialize floating labels for inputs
  document.querySelectorAll('.md3-outlined-textfield__input').forEach(input => {
    const updateLabel = () => {
      const label = input.parentElement?.querySelector('.md3-outlined-textfield__label');
      if (label) {
        if (input.value) {
          label.classList.add('md3-outlined-textfield__label--floating');
        } else {
          label.classList.remove('md3-outlined-textfield__label--floating');
        }
      }
    };
    // Update on input/focus/blur
    input.addEventListener('input', updateLabel);
    input.addEventListener('focus', () => {
      const label = input.parentElement?.querySelector('.md3-outlined-textfield__label');
      if (label) label.classList.add('md3-outlined-textfield__label--floating');
    });
    input.addEventListener('blur', updateLabel);
  });

  const saveBtn = document.getElementById('save');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const status = document.getElementById('status');
      clearAlert(status);

      const usernameInput = document.getElementById('username');
      const emailInput = document.getElementById('email');
      const newUsername = usernameInput?.value?.trim();
      const newEmail = emailInput?.value?.trim();
      
      // Only send non-empty values
      const body = {};
      if (newUsername) body.username = newUsername;
      if (newEmail) body.email = newEmail;
      
      // Nothing to update
      if (Object.keys(body).length === 0) {
        showError(status, 'Bitte mindestens ein Feld ausfüllen.');
        return;
      }

      const r = await fetch('/auth/account/profile', { 
        method: 'PATCH', 
        headers: { 'Content-Type': 'application/json' }, 
        credentials: 'same-origin',
        body: JSON.stringify(body) 
      });
      const j = await r.json();
      
      if (r.status === 200 && j.ok) {
        showSuccess(status, 'Profil erfolgreich gespeichert.');
        // Refresh display and clear inputs
        await loadProfileData();
        if (usernameInput) usernameInput.value = '';
        if (emailInput) emailInput.value = '';
      } else {
        if (r.status === 409 && j.error === 'username_exists') {
          showError(status, 'Benutzername bereits vergeben.');
        } else {
          showError(status, j.message || 'Fehler beim Speichern.');
        }
      }
    });
  }

  // Delete Account Logic
  const deleteBtn = document.getElementById('delete-account-btn');
  const deleteDialog = document.getElementById('delete-dialog');
  const cancelDeleteBtn = document.getElementById('cancel-delete');
  const confirmDeleteBtn = document.getElementById('confirm-delete');

  if (deleteBtn && deleteDialog) {
    deleteBtn.addEventListener('click', () => {
      deleteDialog.showModal();
    });

    if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', () => {
        // clear inputs + errors when cancelling
        const pw = document.getElementById('delete-password');
        const err = document.getElementById('delete-error');
        if (pw) pw.value = '';
        if (err) err.textContent = '';
        deleteDialog.close();
      });
    }

    // Toggle visibility for delete-password field (same pattern as other pages)
    document.querySelectorAll('.md3-outlined-textfield__icon--trailing').forEach(btn => {
      btn.addEventListener('click', () => {
        const inputId = btn.dataset.toggle;
        const input = document.getElementById(inputId);
        if (!input) return;
        const icon = btn.querySelector('.material-symbols-rounded');
        if (input.type === 'password') {
          input.type = 'text';
          if (icon) icon.textContent = 'visibility_off';
        } else {
          input.type = 'password';
          if (icon) icon.textContent = 'visibility';
        }
      });
    });

    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', async () => {
        const pwInput = document.getElementById('delete-password');
        const errEl = document.getElementById('delete-error');
        if (!pwInput) return;
        const pw = pwInput.value || '';
        errEl.textContent = '';

        if (!pw) {
          errEl.textContent = 'Bitte Passwort eingeben.';
          return;
        }

        try {
          const r = await fetch('/auth/account/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ password: pw })
          });

          if (r.status === 202) {
            // Accepted: account soft-deleted and anonymization scheduled
            // Now call logout endpoint to clear cookies on the client and revoke session
            try {
              await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
            } catch (e) {
              // Best-effort: if logout fails, continue to redirect anyway
              console.warn('Logout after delete failed', e);
            }

            // Redirect to the index page (Inicio)
            window.location.href = '/';
            return;
          }

          if (r.status === 401) {
            errEl.textContent = 'Ungültiges Passwort.';
            return;
          }

          const j = await r.json().catch(() => ({}));
          errEl.textContent = j.error || 'Fehler beim Löschen des Kontos.';
        } catch (e) {
          console.error(e);
          errEl.textContent = 'Ein Fehler ist aufgetreten.';
        }
      });
    }
  }
});
