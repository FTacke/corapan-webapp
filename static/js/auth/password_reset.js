document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('reset');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = document.getElementById('token').value;
    const newPassword = document.getElementById('new').value;
    const resp = await fetch('/auth/reset-password/confirm', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resetToken: token, newPassword }) });
    const data = await resp.json();
    const status = document.getElementById('status');
    if (status) status.textContent = data.ok ? 'Passwort gesetzt.' : 'Fehler: ' + JSON.stringify(data);
  });
});
