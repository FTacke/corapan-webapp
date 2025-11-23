document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('forgot');
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const resp = await fetch('/auth/reset-password/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) });
    const data = await resp.json();
    const status = document.getElementById('status');
    if (status) status.textContent = data.ok ? 'Anfrage gesendet (sofern Konto existiert).' : 'Fehler';
  });
});
