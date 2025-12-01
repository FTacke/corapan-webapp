/**
 * Statistics Page Functionality
 * Handles image zoom modal and country statistics selection.
 * Supports deep-linking via URL query parameter (?country=XXX).
 */

export function initStatsPage() {
  // Image zoom modal functionality
  const modal = document.getElementById('statsZoomModal');
  const modalImage = document.getElementById('statsZoomImage');
  const allImages = document.querySelectorAll('.md3-stats-image, .md3-stats-country-image');
  
  if (modal && modalImage) {
    // Add click handlers to all statistics images
    allImages.forEach(img => {
      const container = img.closest('.md3-stats-image-container, .md3-stats-country-image-container');
      if (container) {
        container.addEventListener('click', function(e) {
          e.preventDefault();
          modalImage.src = img.src;
          modalImage.alt = img.alt;
          modal.classList.add('active');
          document.body.style.overflow = 'hidden';
        });
      }
    });
    
    // Close modal on click
    modal.addEventListener('click', function(e) {
      if (e.target === modal || e.target.closest('.md3-stats-zoom-modal-close')) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

  // Country statistics image display
  const countrySelect = document.getElementById('countrySelect');
  const displayArea = document.getElementById('countryStatsDisplay');
  
  if (countrySelect && displayArea) {
    // Handle country selection
    function loadCountryStats(countryCode) {
      if (!countryCode) {
        displayArea.innerHTML = '';
        return;
      }
      
      // Create figure element
      const figure = document.createElement('figure');
      figure.className = 'md3-stats-country-figure';
      
      const imageContainer = document.createElement('div');
      imageContainer.className = 'md3-stats-country-image-container';
      
      const img = document.createElement('img');
      img.className = 'md3-stats-country-image';
      img.alt = `Estadísticas de ${countrySelect.options[countrySelect.selectedIndex]?.text || countryCode}`;
      img.loading = 'lazy';
      
      // Build image path
      const imagePath = `/static/img/statistics/viz_${countryCode}_resumen.png`;
      
      // Handle image load
      img.onload = function() {
        requestAnimationFrame(() => {
          figure.classList.add('visible');
          // Add click handler for zoom
          imageContainer.addEventListener('click', function(e) {
            e.preventDefault();
            if (modal && modalImage) {
                modalImage.src = img.src;
                modalImage.alt = img.alt;
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
          });
        });
      };
      
      img.onerror = function() {
        displayArea.innerHTML = `
          <div class="md3-stats-placeholder md3-body-large">
            <p><strong>Error:</strong> No se pudo cargar la imagen para este país.</p>
          </div>
        `;
      };
      
      img.src = imagePath;
      imageContainer.appendChild(img);
      figure.appendChild(imageContainer);
      
      // Replace content with fade effect
      displayArea.innerHTML = '';
      displayArea.appendChild(figure);
    }

    // Listen for select changes
    countrySelect.addEventListener('change', function() {
      const countryCode = this.value;
      loadCountryStats(countryCode);
      
      // Update URL without reload
      const url = new URL(window.location);
      if (countryCode) {
        url.searchParams.set('country', countryCode);
      } else {
        url.searchParams.delete('country');
      }
      window.history.replaceState({}, '', url);
    });

    // Check for deep-link on page load
    const params = new URLSearchParams(window.location.search);
    const urlCountry = params.get('country');
    if (urlCountry) {
      // Find matching option
      const option = countrySelect.querySelector(`option[value="${urlCountry}"]`);
      if (option) {
        countrySelect.value = urlCountry;
        loadCountryStats(urlCountry);
      }
    }
  }
}

// Auto-init
document.addEventListener('DOMContentLoaded', initStatsPage);
