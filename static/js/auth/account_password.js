document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('chg');
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const oldPassword = document.getElementById('old').value;
    const newPassword = document.getElementById('new').value;
    const r = await fetch('/auth/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ oldPassword, newPassword }) });
    const j = await r.json();
    const status = document.getElementById('status');
    if (status) status.textContent = j.ok ? 'Passwort geändert' : JSON.stringify(j);
  });
});
