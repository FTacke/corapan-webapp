document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('del');
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const password = document.getElementById('pw').value;
    const r = await fetch('/auth/account/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
    const j = await r.json();
    const status = document.getElementById('status');
    if (status) status.textContent = r.status === 202 ? 'Löschanfrage akzeptiert' : JSON.stringify(j);
    if (r.status === 202) window.location = '/';
  });
});
