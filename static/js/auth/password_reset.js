document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('reset');
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

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('status');
    status.textContent = '';
    status.className = 'mt-3';

    const token = document.getElementById('token').value;
    const newPassword = document.getElementById('new').value;
    const confirmPassword = document.getElementById('confirm').value;

    if (newPassword !== confirmPassword) {
      status.textContent = 'Die Passwörter stimmen nicht überein.';
      status.style.color = 'var(--md-sys-color-error)';
      return;
    }

    const resp = await fetch('/auth/reset-password/confirm', { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ resetToken: token, newPassword }) 
    });
    
    const data = await resp.json();
    
    if (data.ok) {
      status.textContent = 'Passwort erfolgreich gesetzt. Du kannst dich jetzt anmelden.';
      status.style.color = 'var(--md-sys-color-primary)';
      form.reset();
      // Optional: Redirect to login after a delay
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    } else {
      status.textContent = data.message || 'Fehler beim Setzen des Passworts.';
      status.style.color = 'var(--md-sys-color-error)';
    }
  });
});
