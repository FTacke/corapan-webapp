const MEDIA_ENDPOINT = '/media';
const PLAYER_PATH = '/player';

function openPlayer(jsonFile) {
  const baseName = jsonFile.slice(0, -5);
  const audioBase = jsonFile.slice(0, -10);
  const transcriptionPath = `${MEDIA_ENDPOINT}/transcripts/${baseName}`;
  const audioPath = `${MEDIA_ENDPOINT}/full/${audioBase}.mp3`;
  window.location.href = `${PLAYER_PATH}?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}`;
}

if (typeof window !== 'undefined') {
  window.openPlayer = openPlayer;
}

document.addEventListener('DOMContentLoaded', function () {
  console.log('audios_script loaded');
  
  // ============================
  // Globale Konfigurationen
  // ============================
  
  // Zentrale Liste aller Städte – wird für Marker & Überschriften genutzt
  let cityMarkers = {};
  const cityList = [
    { name: 'Argentina: Buenos Aires', code: 'ARG' },
    { name: 'Argentina: Trelew (Chubut)', code: 'ARG-Cht' },
    { name: 'Argentina: Córdoba (Córdoba)', code: 'ARG-Cba' },
    { name: 'Argentina: Santiago del Estero (Santiago del Estero)', code: 'ARG-SdE' },
    { name: 'Bolivia: La Paz', code: 'BOL' },
    { name: 'Chile: Santiago', code: 'CHI' },
    { name: 'Colombia: Bogotá', code: 'COL' },
    { name: 'Costa Rica: San José', code: 'CR' },
    { name: 'Cuba: La Habana', code: 'CUB' },
    { name: 'Ecuador: Quito', code: 'ECU' },
    { name: 'España: La Laguna (Canarias)', code: 'ES-CAN' },
    { name: 'España: Sevilla (Andalucía)', code: 'ES-SEV' },
    { name: 'España: Madrid', code: 'ES-MAD' },
    { name: 'Guatemala: Ciudad de Guatemala', code: 'GUA' },
    { name: 'Honduras: Tegucigalpa', code: 'HON' },
    { name: 'México: Ciudad de México', code: 'MEX' },
    { name: 'Nicaragua: Managua', code: 'NIC' },
    { name: 'Panamá: Ciudad de Panamá', code: 'PAN' },
    { name: 'Paraguay: Asunción', code: 'PAR' },
    { name: 'Perú: Lima', code: 'PER' },
    { name: 'República Dominicana: Santo Domingo', code: 'RD' },
    { name: 'El Salvador: San Salvador', code: 'SAL' },
    { name: 'Uruguay: Montevideo', code: 'URU' },
    { name: 'Venezuela: Caracas', code: 'VEN' }
  ];

  // Variable für die Karte
  var map;
  // Globaler Flag, damit der Auth-Fehlerhinweis nur einmal angezeigt wird
  var authErrorDisplayed = false;

  // Berechnet den initialen Zoom basierend auf der Kartenbreite
  function getInitialZoom() {
    const mapContainer = document.getElementById('map-container');
    const mapWidth = mapContainer ? mapContainer.offsetWidth : window.innerWidth;
    
    if (mapWidth <= 400) {
      // Bei 400px oder schmaler: etwas weiter herauszoomen
      return 2.6;
    } else if (mapWidth < 801) {
      // Bei Kartenbreiten zwischen 401px und 800px: minimal herauszoomen
      return 2.8;
    } else {
      // Für größere Container
      return 3;
    }
  }

  // ============================
  // Initialisierung der Karte
  // ============================
  function initializeMap() {
    const mapContainer = document.getElementById('map-container');
    const mapWidth = mapContainer ? mapContainer.offsetWidth : window.innerWidth;
    
    // Standardmittelpunkt
    var center = [1, -50];
    // Falls die Kartenbreite 400px oder kleiner ist, verschiebe den Mittelpunkt leicht nach unten und links
    if (mapWidth <= 400) {
      center = [center[0] - 15.0, center[1] - 18.0];
    }
    
    var initialZoom = getInitialZoom();
    map = L.map('map', {
      center: center,
      zoom: initialZoom,
      attributionControl: false
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    // Legende in der unteren rechten Ecke
    var legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
      var div = L.DomUtil.create('div', 'legend');
      div.style.backgroundColor = 'white';
      div.style.padding = '8px';
      div.style.borderRadius = '5px';
      div.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
      div.style.fontFamily = 'Arial Narrow, sans-serif';
      div.style.fontSize = '14px';
      div.innerHTML =
        '<div style="margin-bottom: 5px;">' +
          '<img src="static/img/citymarkers/primary/communications-tower.svg" style="width:20px; height:20px; vertical-align:middle; margin-right:8px;">' +
          'Emisora nacional' +
        '</div>' +
        '<div>' +
          '<img src="static/img/citymarkers/secondary/communications-tower.svg" style="width:20px; height:20px; vertical-align:middle; margin-right:8px;">' +
          'Emisora regional' +
        '</div>';
      return div;
    };
    legend.addTo(map);

    // -------------------------------
    // Marker-Konfigurationen (Icons)
    // -------------------------------
    const markerConfigs = {
      primary: {
        path: 'static/img/citymarkers/primary/',
        defaultFile: 'communications-tower.svg',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -15]
      },
      secondary: {
        path: 'static/img/citymarkers/secondary/',
        defaultFile: 'communications-tower.svg',
        iconSize: [25, 25],
        iconAnchor: [17, 17],
        popupAnchor: [0, -17]
      }
    };

    /**
     * Fügt einen Marker für eine Stadt hinzu.
     *
     * @param {number} lat - Breitengrad
     * @param {number} lng - Längengrad
     * @param {string} cityName - Name der Stadt (wird als Popup genutzt)
     * @param {string} countryCode - Ländercode (für updateCapitalLinks)
     * @param {string} markerClass - 'primary' oder 'secondary'
     * @param {string} [customIconFile] - Optional: eigener Icon-Dateiname
     */
    function addCityMarker(lat, lng, cityName, countryCode, markerClass = 'primary', customIconFile = null) {
      const config = markerConfigs[markerClass] || markerConfigs.primary;
      const iconFile = customIconFile || config.defaultFile;
      
      const icon = L.icon({
        iconUrl: `${config.path}${iconFile}`,
        iconSize: config.iconSize,
        iconAnchor: config.iconAnchor,
        popupAnchor: config.popupAnchor
      });
      
      const marker = L.marker([lat, lng], { icon: icon }).addTo(map);
      marker.bindPopup(cityName);
      marker.on('click', function () {
        // Bei Marker-Klick wird nur diese Stadt angezeigt (Container wird geleert)
        updateCapitalLinks(cityName, countryCode, true);
      });
      // Marker im globalen Objekt speichern
      cityMarkers[countryCode] = marker;
    }

    // -------------------------------
    // Marker hinzufügen
    // -------------------------------
    addCityMarker(-34.6118, -58.4173, 'Buenos Aires, Argentina', 'ARG', 'primary');
    addCityMarker(-43.2489, -65.3051, 'Trelew (Chubut), Argentina', 'ARG-Cht', 'secondary');
    addCityMarker(-31.4201, -64.1888, 'Córdoba (Córdoba), Argentina', 'ARG-Cba', 'secondary');
    addCityMarker(-27.7951, -64.2615, 'Santiago del Estero (Santiago del Estero), Argentina', 'ARG-SdE', 'secondary');
    addCityMarker(-16.5000, -68.1500, 'La Paz, Bolivia', 'BOL', 'primary');
    addCityMarker(-33.4489, -70.6693, 'Santiago, Chile', 'CHI', 'primary');
    addCityMarker(4.6097, -74.0817, 'Bogotá, Colombia', 'COL', 'primary');
    addCityMarker(9.9281, -84.0907, 'San José, Costa Rica', 'CR', 'primary');
    addCityMarker(23.1330, -82.3830, 'La Habana, Cuba', 'CUB', 'primary');
    addCityMarker(-0.2300, -78.5200, 'Quito, Ecuador', 'ECU', 'primary');
    addCityMarker(28.4874, -16.3141, 'La Laguna (Canarias), España', 'ES-CAN', 'secondary');
    addCityMarker(37.3886, -5.9823, 'Sevilla (Andalucía), España', 'ES-SEV', 'secondary');
    addCityMarker(40.4168, -3.7038, 'Madrid, España', 'ES-MAD', 'primary');
    addCityMarker(14.6349, -90.5069, 'Ciudad de Guatemala, Guatemala', 'GUA', 'primary');
    addCityMarker(14.0723, -87.1921, 'Tegucigalpa, Honduras', 'HON', 'primary');
    addCityMarker(19.4326, -99.1332, 'Ciudad de México, México', 'MEX', 'primary');
    addCityMarker(12.1364, -86.2514, 'Managua, Nicaragua', 'NIC', 'primary');
    addCityMarker(8.9824, -79.5199, 'Ciudad de Panamá, Panamá', 'PAN', 'primary');
    addCityMarker(-25.2637, -57.5759, 'Asunción, Paraguay', 'PAR', 'primary');
    addCityMarker(-12.0464, -77.0428, 'Lima, Perú', 'PER', 'primary');
    addCityMarker(18.4663, -69.9526, 'Santo Domingo, República Dominicana', 'RD', 'primary');
    addCityMarker(13.6929, -89.2182, 'San Salvador, El Salvador', 'SAL', 'primary');
    addCityMarker(-34.9011, -56.1910, 'Montevideo, Uruguay', 'URU', 'primary');
    addCityMarker(10.5000, -66.9333, 'Caracas, Venezuela', 'VEN', 'primary');
  }


  // Bei Resize die Karte neu initialisieren
  window.addEventListener('resize', function () {
    map.remove();
    initializeMap();
  });

  // Karte beim Laden der Seite initialisieren
  window.addEventListener('load', initializeMap);

  // ============================
  // Aktualisieren der Container-Inhalte
  // ============================
  /**
   * Baut den Inhalt (Überschrift und Tabelle) für eine ausgewählte Stadt auf.
   *
   * @param {string} cityName - Ursprünglicher Name (Fallback)
   * @param {string} countryCode - Ländercode der Stadt
   * @param {boolean} clearContainer - Bei true: Vorheriges Löschen (z. B. bei Marker-Klick)
   */
  function updateCapitalLinks(cityName, countryCode, clearContainer = true) {
    var container = document.getElementById('capitalLinksContainer');
    var mp3LinksContainer = document.getElementById('mp3Links');

    if (clearContainer) {
      mp3LinksContainer.innerHTML = '';
    }
    container.style.display = 'block';

    // Aktualisiere den Dropdown-Wert, wenn clearContainer true ist
    if (clearContainer) {
      document.getElementById('citySelect').value = countryCode;
    }

    // Den exakten Stadtnamen aus der cityList ermitteln
    const matchedCity = cityList.find(city => city.code === countryCode);
    const headerText = matchedCity ? matchedCity.name : cityName;

    // Einen eigenen Container für diese Stadt erstellen
    const cityContainer = document.createElement('div');
    cityContainer.className = 'city-table-container';

    const cityNameHeader = document.createElement('h3');
    cityNameHeader.textContent = headerText;
    cityContainer.appendChild(cityNameHeader);

    // Tabelle für die Metadaten erstellen (ID gesetzt, damit CSS-Regeln greifen)
    const table = document.createElement('table');
    table.id = 'audiofile-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Emisora</th>
          <th>Audio/Transcripción</th>
          <th>Duración</th>
          <th>Palabras</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    cityContainer.appendChild(table);
    mp3LinksContainer.appendChild(cityContainer);

    const tbody = table.querySelector('tbody');

    fetch(`/get_stats_files_from_db`)
      .then(response => response.json())
      .then(data => {
        const metadataList = data.metadata_list.filter(metadata => metadata.filename.includes(`_${countryCode}_`));
        const uniqueMetadataList = metadataList.filter(
          (metadata, index, self) =>
            index === self.findIndex(m => m.filename === metadata.filename && m.date === metadata.date)
        );
        uniqueMetadataList.forEach((metadata) => {
          const formattedWordCount = metadata.word_count.toLocaleString();
          const [hours, minutes, secondsWithDecimal] = metadata.duration.split(':');
          const seconds = secondsWithDecimal.split('.')[0];
          const formattedDuration = `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}:${seconds.padStart(2, '0')}`;
          const row = document.createElement('tr');
          const filenameWithoutExtension = metadata.filename.replace('.json', '');
          row.innerHTML = `
            <td>${metadata.date}</td>
            <td>${metadata.radio}</td>
            <td>
              <a href="#" onclick="openPlayer('${filenameWithoutExtension}.json')" class="link">
                <i class="bi bi-file-earmark-music"></i> <i class="bi bi-file-text"></i> ${filenameWithoutExtension}
              </a>
            </td>
            <td class="right-align">${formattedDuration}</td>
            <td class="right-align">${formattedWordCount}</td>
          `;
          const filenameLink = row.querySelector('.link');
          filenameLink.addEventListener('click', (event) => {
            event.preventDefault();
            openPlayer(`${metadata.filename}.json`);
          });
          tbody.appendChild(row);
        });
      })
      .catch(error => {
        console.error('Error fetching metadata from the database:', error);
        if (!authErrorDisplayed) {
          container.innerHTML = `
            <div class="login-container-atlas">
              <div class="login-form-atlas error">
                <p><span class="error"><i class="bi bi-lock-fill"></i> Inicie <a href="/" class="link-error">sesión</a> para acceder a los datos.</span></p>
              </div>
            </div>
          `;
          authErrorDisplayed = true;
        }
      });

  }

  document.getElementById('citySelect').addEventListener('change', function () {
    const selectedValue = this.value;
    if (selectedValue === 'ALL') {
      updateAllCapitalLinks();
      // Sanft zur Ursprungsansicht zoomen (Zentrum und initialen Zoom wiederherstellen)
      map.flyTo([5, -50], getInitialZoom());
    } else {
      document.getElementById('mp3Links').innerHTML = '';
      updateCapitalLinks('', selectedValue, true);
      // Marker-Popup öffnen, Karte zentrieren und heranzoomen
      const marker = cityMarkers[selectedValue];
      if (marker) {
        marker.openPopup();
        map.flyTo(marker.getLatLng(), 4);
      }
    }
  });
  
  // -------------------------------
  // Aktualisieren aller Städte ("Todas las capitales")
  // -------------------------------
  function updateAllCapitalLinks() {
    document.getElementById('mp3Links').innerHTML = '';
    const sortedCities = [...cityList].sort((a, b) => a.code.localeCompare(b.code));
    sortedCities.forEach(city => {
      updateCapitalLinks(city.name, city.code, false);
    });
  }

  // -------------------------------
  // Dropdown-Menü befüllen und Event-Listener hinzufügen
  // -------------------------------
  function populateDropdown() {
    const citySelect = document.getElementById('citySelect');
    citySelect.innerHTML = '';
    // Standardoption: "Todas las capitales"
    const defaultOption = document.createElement('option');
    defaultOption.value = 'ALL';
    defaultOption.textContent = 'Todas las capitales';
    citySelect.appendChild(defaultOption);
    // Weitere Optionen aus der cityList
    cityList.forEach(city => {
      const option = document.createElement('option');
      option.value = city.code;
      option.textContent = city.name;
      citySelect.appendChild(option);
    });
  }

  document.getElementById('citySelect').addEventListener('change', function () {
    const selectedValue = this.value;
    if (selectedValue === 'ALL') {
      updateAllCapitalLinks();
    } else {
      document.getElementById('mp3Links').innerHTML = '';
      updateCapitalLinks('', selectedValue, true);
    }
  });

  populateDropdown();
  // Direkt beim Laden alle Tabellen anzeigen (Standardoption "Todas las capitales")
  updateAllCapitalLinks();

  // ============================
  // Footer: Statistiken aktualisieren (öffentliche DB)
  // ============================
  const totalWordCountElement = document.getElementById('totalWordCount');
  const totalDurationElement = document.getElementById('totalDuration');

  fetch('/get_stats_all_from_db')
    .then(response => response.json())
    .then(data => {
      updateTotalStats(data.total_word_count, data.total_duration_all);
    })
    .catch(error => {
      console.error('Error fetching statistics from the database:', error);
    });

  function updateTotalStats(totalWordCount, totalDuration) {
    totalDurationElement.innerHTML = `<span class="meta-value meta-value--primary">${totalDuration}</span> horas de audio`;
    totalWordCountElement.innerHTML = `<span class="meta-value meta-value--primary">${totalWordCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')}</span> palabras transcritas`;
  }
});

