import { fetchCorpus } from './api.js';
import { renderResults } from './render.js';

const form = document.querySelector('#corpus-filter-form');
const resultsContainer = document.querySelector('[data-element="results-table"]');
const resultsMeta = document.querySelector('[data-element="results-meta"]');
const transcriptPanel = document.querySelector('[data-element="transcript-viewer"]');
const transcriptContent = document.querySelector('[data-element="transcript-content"]');
const closeTranscriptButton = document.querySelector('[data-action="close-transcript"]');

const audioPlayer = document.createElement('audio');
audioPlayer.controls = true;
audioPlayer.className = 'snippet-player';
audioPlayer.hidden = true;
let currentAudioUrl = null;
if (resultsMeta) {
  resultsMeta.appendChild(audioPlayer);
}

function updateMeta(payload) {
  if (!resultsMeta) return;
  const pieces = [];
  if (payload.error) {
    pieces.push(payload.error);
  } else if (payload.total !== undefined) {
    pieces.push(`${payload.total} results`);
    if (payload.page && payload.total_pages) {
      pieces.push(`Page ${payload.page} of ${payload.total_pages}`);
    }
  }
  resultsMeta.innerHTML = '';
  const info = document.createElement('span');
  info.textContent = pieces.join(' | ') || 'Ready to search';
  resultsMeta.appendChild(info);
  resultsMeta.appendChild(audioPlayer);
}

function resetTranscriptPanel() {
  if (!transcriptPanel || !transcriptContent) return;
  transcriptPanel.hidden = true;
  transcriptContent.textContent = '';
}

async function runSearch(event) {
  if (event) {
    event.preventDefault();
  }
  resetTranscriptPanel();
  const formData = new FormData(form);
  const query = (formData.get('query') || '').trim();
  if (!query) {
    renderResults(resultsContainer, []);
    updateMeta({ error: 'Enter a search term to begin.' });
    return;
  }
  const params = new URLSearchParams();
  for (const [key, value] of formData.entries()) {
    if (!value) continue;
    params.append(key, value);
  }
  try {
    const payload = await fetchCorpus(params);
    renderResults(resultsContainer, payload.results);
    updateMeta({
      total: payload.meta?.total ?? 0,
      page: payload.meta?.page ?? 1,
      total_pages: payload.meta?.total_pages ?? 1,
    });
  } catch (error) {
    renderResults(resultsContainer, []);
    updateMeta({ error: error.message || 'Search failed.' });
  }
}

function revokeAudioUrl() {
  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = null;
  }
}

async function requestSnippet(row) {
  const filename = row.dataset.filename;
  const start = Number(row.dataset.start || 0);
  const end = Number(row.dataset.end || 0);
  if (!filename) return;
  try {
    const response = await fetch('/media/snippet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, start, end }),
    });
    if (response.status === 401) {
      throw new Error('Authentication required for audio snippets.');
    }
    if (!response.ok) {
      throw new Error('Unable to create snippet.');
    }
    const blob = await response.blob();
    revokeAudioUrl();
    currentAudioUrl = URL.createObjectURL(blob);
    audioPlayer.src = currentAudioUrl;
    audioPlayer.hidden = false;
    await audioPlayer.play();
  } catch (error) {
    updateMeta({ error: error.message });
  }
}

async function requestTranscript(row) {
  if (!transcriptPanel || !transcriptContent) return;
  const fileName = row.dataset.transcript;
  if (!fileName) return;
  try {
    const response = await fetch(`/media/transcripts/${encodeURIComponent(fileName)}`);
    if (response.status === 401) {
      throw new Error('Authentication required for transcripts.');
    }
    if (!response.ok) {
      throw new Error('Unable to load transcript.');
    }
    const data = await response.json();
    transcriptContent.textContent = JSON.stringify(data, null, 2);
    transcriptPanel.hidden = false;
  } catch (error) {
    updateMeta({ error: error.message });
  }
}

function handleResultsClick(event) {
  const trigger = event.target.closest('button');
  if (!trigger) return;
  const row = trigger.closest('.result-row');
  if (!row) return;
  const enabled = trigger.dataset.enabled === 'true';
  if (!enabled) {
    event.preventDefault();
    return;
  }
  if (trigger.classList.contains('audio-trigger')) {
    requestSnippet(row);
  }
  if (trigger.classList.contains('transcript-trigger')) {
    requestTranscript(row);
  }
}

if (form) {
  form.addEventListener('submit', runSearch);
}

if (resultsContainer) {
  resultsContainer.addEventListener('click', handleResultsClick);
}

if (closeTranscriptButton) {
  closeTranscriptButton.addEventListener('click', () => {
    resetTranscriptPanel();
  });
}

const initialInput = form?.querySelector('[name="query"]');
if (initialInput && initialInput.value.trim()) {
  runSearch();
}
