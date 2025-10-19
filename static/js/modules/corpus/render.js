const HTML_ESCAPES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

function escapeHtml(value = '') {
  return value.replace(/[&<>"']/g, (char) => HTML_ESCAPES[char] || char);
}

export function renderResults(container, results = []) {
  if (!container) return;
  if (!Array.isArray(results) || results.length === 0) {
    container.innerHTML = '<p class="empty-state">No results yet. Submit a query to explore the corpus.</p>';
    return;
  }
  const rows = results.map((result, index) => renderRow(result, index));
  container.innerHTML = `
    <table class="results-grid">
      <thead>
        <tr>
          <th>#</th>
          <th>Token</th>
          <th>Context</th>
          <th>Metadata</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${rows.join('')}
      </tbody>
    </table>
  `;
}

function renderRow(result, index) {
  const snippetEnabled = result.snippet_enabled ? 'true' : 'false';
  const transcriptEnabled = result.transcript_enabled ? 'true' : 'false';
  const left = escapeHtml(result.context_left || '');
  const token = escapeHtml(result.token || '');
  const right = escapeHtml(result.context_right || '');
  const contextMarkup = `${left}<mark>${token}</mark>${right}`;
  const meta = [
    result.country_code,
    result.radio,
    result.date,
    result.speaker_type,
    result.mode,
  ].filter(Boolean).map(escapeHtml).join(' | ');
  return `
    <tr
      class="result-row"
      data-filename="${escapeHtml(result.filename || '')}"
      data-start="${Number(result.start) || 0}"
      data-end="${Number(result.end) || 0}"
      data-transcript="${escapeHtml(result.transcript_name || '')}"
    >
      <td class="result-index">${index + 1}</td>
      <td class="result-token">${token || '—'}</td>
      <td class="result-context">${contextMarkup}</td>
      <td class="result-meta">${meta || '—'}</td>
      <td class="result-actions">
        <button class="audio-trigger" data-enabled="${snippetEnabled}" title="${snippetEnabled === 'true' ? 'Play snippet' : 'Login required for snippets'}">
          <span class="icon">&#9658;</span>
          Snippet
        </button>
        <button class="transcript-trigger" data-enabled="${transcriptEnabled}" title="${transcriptEnabled === 'true' ? 'View transcript excerpt' : 'Login required for transcripts'}">
          Transcript
        </button>
      </td>
    </tr>
  `;
}
