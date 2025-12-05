/**
 * Citation Format Selector
 * Handles format switching and copy functionality for the "Cómo citar" page.
 * @module pages/como-citar
 */

(function () {
  'use strict';

  // Citation formats data
  const CITATION_FORMATS = {
    apa: `Tacke, F. (2025). CO.RA.PAN — Corpus Radiofónico Panhispánico.
Philipps-Universität Marburg, Marburg. https://corapan.online.uni-marburg.de
DOI: https://doi.org/10.5281/zenodo.15360942`,

    chicago: `Tacke, Felix. 2025. CO.RA.PAN — Corpus Radiofónico Panhispánico.
Marburg: Philipps-Universität Marburg. https://corapan.online.uni-marburg.de
DOI: https://doi.org/10.5281/zenodo.15360942`,

    harvard: `Tacke, F. (2025) CO.RA.PAN — Corpus Radiofónico Panhispánico.
Philipps-Universität Marburg, Marburg. Available at: https://corapan.online.uni-marburg.de
DOI: https://doi.org/10.5281/zenodo.15360942`,

    mla: `Tacke, Felix. CO.RA.PAN — Corpus Radiofónico Panhispánico.
Philipps-Universität Marburg, Marburg, 2025. https://corapan.online.uni-marburg.de
DOI: https://doi.org/10.5281/zenodo.15360942`,

    bibtex: `@dataset{corapan2025,
  author    = {Tacke, Felix},
  title     = {CO.RA.PAN — Corpus Radiofónico Panhispánico},
  year      = {2025},
  publisher = {Philipps-Universität Marburg},
  address   = {Marburg},
  doi       = {10.5281/zenodo.15360942},
  url       = {https://corapan.online.uni-marburg.de}
}`,

    ris: `TY  - DATA
TI  - CO.RA.PAN — Corpus Radiofónico Panhispánico
AU  - Tacke, Felix
PY  - 2025
PB  - Philipps-Universität Marburg
CY  - Marburg
UR  - https://corapan.online.uni-marburg.de
DO  - 10.5281/zenodo.15360942
ER  -`
  };

  // DOM elements
  let formatSelect = null;
  let codeElement = null;
  let copyButton = null;
  let statusElement = null;

  /**
   * Update the citation code block based on selected format
   * @param {string} format - The citation format key
   */
  function updateCitation(format) {
    if (!codeElement || !CITATION_FORMATS[format]) return;
    codeElement.textContent = CITATION_FORMATS[format];
  }

  /**
   * Copy citation text to clipboard with visual feedback
   */
  async function copyCitation() {
    if (!codeElement) return;

    const text = codeElement.textContent;
    
    try {
      await navigator.clipboard.writeText(text);
      showCopyFeedback(true);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-9999px';
      document.body.appendChild(textArea);
      textArea.select();
      
      try {
        document.execCommand('copy');
        showCopyFeedback(true);
      } catch (e) {
        console.error('Copy failed:', e);
        showCopyFeedback(false);
      }
      
      document.body.removeChild(textArea);
    }
  }

  /**
   * Show visual and accessible feedback for copy action
   * @param {boolean} success - Whether the copy was successful
   */
  function showCopyFeedback(success) {
    if (!copyButton || !statusElement) return;

    const icon = copyButton.querySelector('.material-symbols-rounded');
    const originalIcon = icon ? icon.textContent : 'content_copy';

    // Visual feedback - change icon temporarily
    if (icon) {
      icon.textContent = success ? 'check' : 'error';
      copyButton.classList.add(success ? 'md3-button--success' : 'md3-button--error');
    }

    // Screen reader feedback
    statusElement.textContent = success 
      ? 'Cita copiada al portapapeles' 
      : 'Error al copiar la cita';

    // Reset after delay
    setTimeout(() => {
      if (icon) {
        icon.textContent = originalIcon;
        copyButton.classList.remove('md3-button--success', 'md3-button--error');
      }
      // Clear status for next action
      setTimeout(() => {
        statusElement.textContent = '';
      }, 1000);
    }, 1500);
  }

  /**
   * Initialize the citation selector functionality
   */
  function init() {
    formatSelect = document.getElementById('citation-format');
    codeElement = document.getElementById('citation-code');
    copyButton = document.getElementById('copy-citation');
    statusElement = document.getElementById('citation-copy-status');

    if (!formatSelect || !codeElement) {
      // Not on the citation page, exit silently
      return;
    }

    // Format change handler
    formatSelect.addEventListener('change', (e) => {
      updateCitation(e.target.value);
    });

    // Copy button handler
    if (copyButton) {
      copyButton.addEventListener('click', copyCitation);
    }

    // Keyboard support for copy (Enter/Space when focused)
    if (copyButton) {
      copyButton.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          copyCitation();
        }
      });
    }

    // Initialize with default format (APA)
    updateCitation('apa');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
