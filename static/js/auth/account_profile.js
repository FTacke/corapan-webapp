async function loadProfile(){
  const r = await fetch('/auth/account/profile');
  if(r.ok){
    const j = await r.json();
    document.getElementById('username').textContent = j.username;
    document.getElementById('email').value = j.email || '';
    document.getElementById('display_name').value = j.display_name || '';
  } else {
    document.getElementById('status').textContent = 'Bitte einloggen.';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('save');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const body = { display_name: document.getElementById('display_name').value, email: document.getElementById('email').value };
      const r = await fetch('/auth/account/profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json();
      document.getElementById('status').textContent = j.ok ? 'Gespeichert' : 'Fehler';
    });
  }
  loadProfile();
});
