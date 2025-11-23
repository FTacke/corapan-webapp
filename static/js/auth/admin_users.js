document.addEventListener('DOMContentLoaded', function () {
  function reload() {
    return fetch('/admin/users')
      .then((r) => {
        if (!r.ok) {
          document.getElementById('list').textContent = 'Failed';
          return;
        }
        return r.json();
      })
      .then((j) => {
        if (!j) return;
        document.getElementById('list').textContent = JSON.stringify(j.items || j, null, 2);
      })
      .catch(() => {
        document.getElementById('list').textContent = 'Failed';
      });
  }

  const refresh = document.getElementById('refresh');
  if (refresh) refresh.addEventListener('click', reload);
  reload();
});
