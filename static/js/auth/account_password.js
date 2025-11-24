document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('chg');
  if (!form) return;

  // Toggle visibility logic
  document.querySelectorAll('.md3-outlined-textfield__icon--trailing').forEach(btn => {
    btn.addEventListener('click', () => {
      const inputId = btn.dataset.toggle;
      const input = document.getElementById(inputId);
      const icon = btn.querySelector('.material-symbols-rounded');
      if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility_off';
      } else {
        input.type = 'password';
        icon.textContent = 'visibility';
      }
    });
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const status = document.getElementById('status');
    status.textContent = '';
    status.className = 'mt-3'; // reset classes

    const oldPassword = document.getElementById('old').value;
    const newPassword = document.getElementById('new').value;
    const confirmPassword = document.getElementById('confirm').value;

    if (newPassword !== confirmPassword) {
      status.textContent = 'Die neuen Passwörter stimmen nicht überein.';
      status.classList.add('md3-text-error'); // Assuming error text class exists or use style
      status.style.color = 'var(--md-sys-color-error)';
      return;
    }

    const r = await fetch('/auth/change-password', { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ oldPassword, newPassword }) 
    });
    
    const j = await r.json();
    
    if (j.ok) {
      status.textContent = 'Passwort erfolgreich geändert.';
      status.style.color = 'var(--md-sys-color-primary)';
      form.reset();
    } else {
      status.textContent = j.message || 'Fehler beim Ändern des Passworts.';
      status.style.color = 'var(--md-sys-color-error)';
    }
  });
});
