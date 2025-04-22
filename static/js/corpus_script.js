// Funktion um zwischen den Tabs zu wechseln
/* Tab‑Umschaltung */
function showTab(tab) {
    // alle Tabs / Buttons zurücksetzen
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active-tab'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  
    // gewünschten Tab aktivieren
    document.getElementById(tab + '-search-container').classList.add('active-tab');
    document.querySelector('[onclick="showTab(\'' + tab + '\')"]').classList.add('active');
  
    // verstecktes Feld „tab“ des aktiven Formulars setzen
    const hidden = document.querySelector('#' + tab + '-search-container form input[name="tab"]');
    if (hidden) hidden.value = tab;
  }
  
/* beim Laden: Tab aus URL wählen */
window.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    showTab(params.get('tab') || 'simple');     
  });   //  <‑‑ Ende DOMContentLoaded  

// Funktion für Checkbox-Gruppen mit einem "all"-Feld (z.B. mode, sex, country_code)
function uncheckAll(category, clickedCheckbox) {
    const checkboxes = document.querySelectorAll(`input[name="${category}"]`);
    const checkboxAll = document.getElementById(`${category}_all`);

    if (clickedCheckbox.value === 'all') {
        // "Todos" gewählt, andere abwählen
        checkboxes.forEach((cb) => {
            if (cb.value !== 'all') cb.checked = false;
        });
    } else {
        // Andere Option gewählt, "Todos" abwählen
        if (checkboxAll) checkboxAll.checked = false;
    }

    // Falls keine spezifische Option mehr gewählt, "Todos" aktivieren
    const anyChecked = Array.from(checkboxes).some(cb => cb.value !== 'all' && cb.checked);
    if (!anyChecked && checkboxAll) {
        checkboxAll.checked = true;
    }
}

// Funktion zum Zurücksetzen des Formulars
function resetForm() {
    // Setzt das Formular zurück
    document.getElementById('searchform').reset();

    // Setzt das Suchfeld explizit auf einen leeren String zurück
    document.getElementById('query').value = '';

    // Setzt alle "all" Checkboxen (für Gruppen wie mode, sex, etc.) auf checked
    var allCheckboxes = document.querySelectorAll('input[type="checkbox"][value="all"]');
    allCheckboxes.forEach(function(checkbox) {
        checkbox.checked = true;
    });
    
    // Entfernt das Häkchen von allen anderen Checkboxen, außer bei "discurso_general"
    var otherCheckboxes = document.querySelectorAll('input[type="checkbox"]:not([value="all"])');
    otherCheckboxes.forEach(function(checkbox) {
        if (checkbox.id !== 'discurso_general') {
            checkbox.checked = false;
        }
    });
    
    // Für die "Discurso"-Gruppe: Setze den "General"-Knopf (id="discurso_general") standardmäßig
    var discursoGeneral = document.getElementById('discurso_general');
    if (discursoGeneral) {
        discursoGeneral.checked = true;
    }
}


var currentAudio = null;
var currentPlayButton = null;

function togglePlayButton(button, filename, contextStart, contextEnd, query, result_number) {
    var timestamp = new Date().getTime();
    var audioUrl = '/play_audio/' + filename + '?start=' + contextStart + '&end=' + contextEnd + '&query=' + query + '&result_number=' + result_number + '&t=' + timestamp;
        
    // Überprüfen, ob bereits ein Audio abgespielt wird, und es stoppen
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;  // Zurücksetzen der Abspielzeit

        // Icon zurücksetzen (falls es geändert wurde)
        if (currentPlayButton) {
            var playIcon = currentPlayButton.querySelector('.fa-play');
            var fadeIcon = currentPlayButton.querySelector('.fa-play.fa-fade');
            if (playIcon && fadeIcon) {
                playIcon.style.display = 'inline-block';
                fadeIcon.style.display = 'none';
            }
        }
    }

    // Icons ausblenden und anzeigen
    var playIcon = button.querySelector('.fa-play');
    var fadeIcon = button.querySelector('.fa-play.fa-fade');

    if (playIcon && fadeIcon) {
        if (playIcon.style.display === 'none') {
            playIcon.style.display = 'inline-block';
            fadeIcon.style.display = 'none';
        } else {
            playIcon.style.display = 'none';
            fadeIcon.style.display = 'inline-block';
        }
    }

    // Erstellen eines neuen Audio-Objekts und Abspielen
    currentAudio = new Audio(audioUrl);
    currentAudio.play();

    // Aktuellen Play-Button aktualisieren
    currentPlayButton = button;

    // Wenn das Audio beendet ist, das Icon zurück in das Play-Icon ändern
    currentAudio.addEventListener('ended', function () {
        if (playIcon && fadeIcon) {
            playIcon.style.display = 'inline-block';
            fadeIcon.style.display = 'none';
        }
    });
}

/**
 * Öffnet den Audio‑/Transkript‑Player für ein Ergebnis aus corpus.html
 * @param {string} fileNameMp3 – z. B. "2022-01-18_VEN_RCR.mp3"
 * @param {string} tokenId     – Token‑ID des Ergebnisses
 */
function openPlayerBusq(fileNameMp3, tokenId) {
    // Leerzeichen entfernen und ".mp3" abschneiden
    const base = fileNameMp3.trim().replace(/\.mp3$/i, '');
  
    // komplette URL zum Flask‑Player zusammenbauen
    window.location.href =
      `${playerPath}?transcription=grabaciones/${base}.json` +
      `&audio=grabaciones/${base}.mp3` +
      `&token_id=${encodeURIComponent(tokenId)}`;
  }

function downloadAudio(button, filename, start, end, query, result_number) {
    var downloadIcon = button.querySelector('.fa-download');
    var bounceIcon = button.querySelector('.fa-download.fa-bounce');

    // Wechsel zu "fa-bounce" Icon
    if (downloadIcon && bounceIcon) {
        downloadIcon.style.display = 'none';
        bounceIcon.style.display = 'inline-block';
    }

    var downloadUrl = '/play_audio/' + filename + '?start=' + start + '&end=' + end + '&query=' + query + '&result_number=' + result_number;
    
    // Erzeugen eines temporären a-Elements zum Download
    var tempLink = document.createElement('a');
    tempLink.href = downloadUrl;
    tempLink.setAttribute('download', '');
    tempLink.style.display = 'none';
    document.body.appendChild(tempLink);
    tempLink.click();
    document.body.removeChild(tempLink);

    // Nach kurzer Verzögerung das Icon wieder zurücksetzen
    setTimeout(function() {
        if (downloadIcon && bounceIcon) {
            downloadIcon.style.display = 'inline-block';
            bounceIcon.style.display = 'none';
        }
    }, 3000); // 3 Sekunden Verzögerung
}

function getCheckedValues(name) {
    const checkboxes = document.querySelectorAll(`input[name="${name}"]:checked`);
    let values = [];
    checkboxes.forEach((checkbox) => {
      // Annahme: Der Text, den wir erfassen wollen, befindet sich im nächsten Geschwisterelement (z. B. <label>)
      let label = checkbox.nextElementSibling;
      if (label) {
        values.push(label.innerText.trim());
      }
    });
    return values.join(', ');
  }
  
  
  function extractDataFromSpan(className) {
    const elements = document.querySelectorAll(`.${className}`);
    return Array.from(elements).map(element => element.textContent.trim());
  }


  
  
/////////////////////////////
// Download als TXT
/////////////////////////////
function downloadResultsTxtFile() {
    // 1) Header-Infos aus .data-Spans
    //    (Entspricht deinem alten Code)
    const query = extractDataFromSpan('data')[0]?.replace(/"/g, '') || '';
    const totalResults = extractDataFromSpan('data')[1] || '0';
    const uniqueFilenames = extractDataFromSpan('data')[2] || '0';
    const uniqueCountries = extractDataFromSpan('data')[3] || '0';

    const pais = getCheckedValues('country_code') || 'Todos';
    const hablante = getCheckedValues('speaker_type') || 'Todos';
    const sexo = getCheckedValues('sex') || 'Todos';
    const modo = getCheckedValues('mode') || 'General';

    // Deinen Info-Block an der Spitze
    // (eins zu eins wie in deinem ursprünglichen Code)
    const headerInfo = 
`CO.RA.PAN
Resultados
Palabra/secuencia buscada: "${query}"
País(es): "${pais}"
Hablante: "${hablante}"
Sexo: "${sexo}"
Modo: "${modo}"

Resultados (total): ${totalResults}
Documentos (total): ${uniqueFilenames}
Países (total): ${uniqueCountries}

`;

    // 2) Tabelle "results-table-full" holen
    const resultsTable = document.getElementById('results-table-full');
    let resultsContent = headerInfo;  // Wir starten schon mal mit dem Info-Block
    if (!resultsTable) {
        alert("Vollständige Tabelle (results-table-full) nicht gefunden!");
        return;
    }

    // 3) Spaltennamen (THs) ermitteln
    let headers = resultsTable.querySelectorAll('thead tr th');
    // => Array der Spaltentexte
    let headerTitles = Array.from(headers).map(h => h.innerText);

    // (A) Audio-Spalte ausfindig machen und entfernen
    const audioIndex = headerTitles.indexOf('Audio');
    if (audioIndex > -1) {
        headerTitles.splice(audioIndex, 1); 
    }

    // (B) Spaltenbreiten berechnen
    let columnWidths = headerTitles.map((_, idx) => {
        // Start = Länge des Spaltentitels
        return headerTitles[idx].length;
    });

    // 4) Zeilen aus dem TBody auslesen
    const rows = resultsTable.querySelectorAll('tbody tr');
    // Wir sammeln die Zeilen in einem Array-of-Arrays
    let allRowData = [];

    rows.forEach((row) => {
        let cells = row.querySelectorAll('td');
        // String-Array der Zellen
        let rowCells = Array.from(cells).map(c => c.innerText);
        // Falls die Audio-Spalte existiert, entfernen wir sie
        if (audioIndex > -1 && rowCells.length > audioIndex) {
            rowCells.splice(audioIndex, 1);
        }
        allRowData.push(rowCells);

        // Gleichzeitig aktualisieren wir columnWidths
        rowCells.forEach((txt, colI) => {
            columnWidths[colI] = Math.max(columnWidths[colI], txt.length);
        });
    });

    // 5) Kopfzeile mit padEnd
    //    => parted by '  ' (zwei Leerzeichen)
    const headerLine = headerTitles.map((title, i) => title.padEnd(columnWidths[i], ' ')).join('  ');
    resultsContent += headerLine + "\n";

    // 6) Datenzeilen
    allRowData.forEach(rowCells => {
        let line = rowCells.map((txt, i) => txt.padEnd(columnWidths[i], ' ')).join('  ');
        resultsContent += line + "\n";
    });

    // 7) Download-Blob erzeugen
    const textBlob = new Blob([resultsContent], { type: 'text/plain;charset=utf-8' });
    const filename = `corapan_resultados_${query.replace(/\s+/g, '_')}.txt`;
    const downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(textBlob);
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/////////////////////////////
// Download als CSV
/////////////////////////////
function downloadResultsCsvFile() {
    // Header‐Daten
    const query = extractDataFromSpan('data')[0]?.replace(/"/g, '') || '';
    const totalResults = extractDataFromSpan('data')[1] || '0';
    const uniqueFilenames = extractDataFromSpan('data')[2] || '0';
    const uniqueCountries = extractDataFromSpan('data')[3] || '0';

    const pais = getCheckedValues('country_code') || 'Todos';
    const hablante = getCheckedValues('speaker_type') || 'Todos';
    const sexo = getCheckedValues('sex') || 'Todos';
    const modo = getCheckedValues('mode') || 'General';

    // Kleiner Info-Kopf für CSV (du kannst es auch als Kommentarzeilen mit '#' machen)
    let headerInfo = 
`CO.RA.PAN // Resultados
Palabra/secuencia buscada: "${query}"
País(es): "${pais}"
Hablante: "${hablante}"
Sexo: "${sexo}"
Modo: "${modo}"

Resultados (total): ${totalResults}
Documentos (total): ${uniqueFilenames}
Países (total): ${uniqueCountries}

`;

    // Start CSV mit BOM + Info (optional)
    const BOM = "\uFEFF";
    let csvContent = BOM + headerInfo.replace(/\n/g, "\r\n") + "\r\n";

    // results-table-full
    const resultsTable = document.getElementById('results-table-full');
    if (!resultsTable) {
        alert("Vollständige Tabelle (results-table-full) nicht gefunden!");
        return;
    }

    // Spaltennamen
    let headers = resultsTable.querySelectorAll('thead tr th');
    let headerTitles = Array.from(headers).map(h => `"${h.innerText.replace(/"/g, '""')}"`);

    // Audio-Spalten entfernen
    const skipColumns = ["Audio/contexto", "Audio/palabra"];
        if (audioIndex > -1) {
        headerTitles.splice(audioIndex, 1);
    }

    // Erste Zeile in CSV
    csvContent += headerTitles.join(",") + "\r\n";

    // Body rows
    const rows = resultsTable.querySelectorAll('tbody tr');
    rows.forEach((row) => {
        let cells = row.querySelectorAll('td');
        let cellTexts = Array.from(cells).map(c => `"${c.innerText.replace(/"/g, '""')}"`);
        if (audioIndex > -1 && cellTexts.length > audioIndex) {
            cellTexts.splice(audioIndex, 1);
        }
        csvContent += cellTexts.join(",") + "\r\n";
    });

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const filename = `corapan_resultados_${query.replace(/\s+/g, '_')}.csv`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/////////////////////////////
// Download als XLSX
/////////////////////////////
function downloadResultsXlsxFile() {
    // Header
    const query = extractDataFromSpan('data')[0]?.replace(/"/g, '') || '';
    const totalResults = extractDataFromSpan('data')[1] || '0';
    const uniqueFilenames = extractDataFromSpan('data')[2] || '0';
    const uniqueCountries = extractDataFromSpan('data')[3] || '0';

    const pais = getCheckedValues('country_code') || 'Todos';
    const hablante = getCheckedValues('speaker_type') || 'Todos';
    const sexo = getCheckedValues('sex') || 'Todos';
    const modo = getCheckedValues('mode') || 'General';

    // Wir packen den Info-Block in ein Array-of-Arrays, dann Leerzeile, dann Spalten
    let headerBlock = [
        ["CO.RA.PAN // Resultados"],
        [`Palabra/secuencia buscada: "${query}"`],
        [`País(es): "${pais}"`],
        [`Hablante: "${hablante}"`],
        [`Sexo: "${sexo}"`],
        [`Modo: "${modo}"`],
        [""],
        [`Resultados (total): ${totalResults}`],
        [`Documentos (total): ${uniqueFilenames}`],
        [`Países (total): ${uniqueCountries}`],
        [""]
    ];

    const resultsTable = document.getElementById('results-table-full');
    if (!resultsTable) {
        alert("Vollständige Tabelle (results-table-full) nicht gefunden!");
        return;
    }

    // Spaltenkopf
    let headers = resultsTable.querySelectorAll('thead tr th');
    let headerTitles = Array.from(headers).map(h => h.innerText);
    const audioIndex = headerTitles.indexOf("Audio");
    if (audioIndex > -1) {
        headerTitles.splice(audioIndex, 1);
    }

    // Body
    const rows = resultsTable.querySelectorAll('tbody tr');
    let bodyAoA = [];
    rows.forEach((tr) => {
        const tds = tr.querySelectorAll('td');
        let rowData = Array.from(tds).map(c => c.innerText);
        if (audioIndex > -1 && rowData.length > audioIndex) {
            rowData.splice(audioIndex, 1);
        }
        bodyAoA.push(rowData);
    });

    // AOArray: [headerBlock, ...Spaltenkopf, ...Daten]
    // a) headerBlock -> ist ein Array-of-Arrays mit 11 Zeilen
    // b) headerTitles -> in einer Zeile
    // c) bodyAoA -> Datenzeilen
    let finalAoA = [
        ...headerBlock, 
        headerTitles, 
        ...bodyAoA
    ];

    // XLSX
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(finalAoA);
    XLSX.utils.book_append_sheet(wb, ws, "Resultados");
    const xlsxData = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' });

    function s2ab(s) {
        const buf = new ArrayBuffer(s.length);
        const view = new Uint8Array(buf);
        for (let i = 0; i < s.length; i++) {
            view[i] = s.charCodeAt(i) & 0xFF;
        }
        return buf;
    }

    const blob = new Blob([s2ab(xlsxData)], { type: "application/octet-stream" });
    const filename = `corapan_resultados_${query.replace(/\s+/g, '_')}.xlsx`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Event Listener für Klicks auf die drei Download-Buttons
document.addEventListener('DOMContentLoaded', function() {
    const linkTxt = document.querySelector('.link-txt');
    if (linkTxt) {
      linkTxt.addEventListener('click', downloadResultsTxtFile);
    }
  
    const linkCsv = document.querySelector('.link-csv');
    if (linkCsv) {
      linkCsv.addEventListener('click', downloadResultsCsvFile);
    }
  
    const linkXlsx = document.querySelector('.link-xlsx');
    if (linkXlsx) {
      linkXlsx.addEventListener('click', downloadResultsXlsxFile);
    }
  });  


// PAGINATION: Funktion zum Ändern der Seitegröße
function changePageSize(newSize) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', '1');
    url.searchParams.set('page_size', newSize);
  
    const sel = document.getElementById('search_mode');
    if (sel) url.searchParams.set('search_mode', sel.value);
  
    // URL aufrufen
    window.location.href = url.toString();
  }  

// Globale Variable für Audio
let overlayAudio = null;

// OVERLAY: Spektogrammanzeige
function showSpectrogramOverlay(filename, start, end, query, result_number, theWord) {
    const timestamp = new Date().getTime();
    const spectroUrl = `/spectrogram/${filename}?start=${start}&end=${end}&query=${query}&result_number=${result_number}&word=${encodeURIComponent(theWord)}&t=${timestamp}`;
    const audioUrl = `/play_audio/${filename}?start=${start}&end=${end}&query=${query}&result_number=${result_number}&t=${timestamp}`;

    // Bild in <img id="spectrogramImage">
    const imgElem = document.getElementById('spectrogramImage');
    if (imgElem) {
        imgElem.src = spectroUrl;
    }

    // Download-Link
    const dlElem = document.getElementById('spectrogramDownload');
    if (dlElem) {
        dlElem.href = spectroUrl;
        dlElem.download = filename + "_spectrogram.png";
    }

    // Audio vorbereiten
    overlayAudio = new Audio(audioUrl);

    // Overlay anzeigen
    const overlay = document.getElementById('spectrogramOverlay');
    if (overlay) {
        overlay.style.display = "block";
    }

    // Play-Button zurücksetzen
    const playButton = document.getElementById('spectrogramPlay');
    if (playButton) {
        playButton.innerHTML = '<i class="fa-solid fa-play"></i>';
    }
}

function closeSpectrogramOverlay() {
    // Overlay ausblenden
    const overlay = document.getElementById('spectrogramOverlay');
    if (overlay) {
        overlay.style.display = "none";
    }

    // Audio stoppen
    if (overlayAudio) {
        overlayAudio.pause();
        overlayAudio = null;
    }

    // Bild zurücksetzen
    const imgElem = document.getElementById('spectrogramImage');
    if (imgElem) {
        imgElem.src = "";
    }
}

// Play-Funktion für Audio
function toggleSpectrogramAudio() {
    const playButton = document.getElementById('spectrogramPlay');

    if (overlayAudio) {
        if (overlayAudio.paused) {
            overlayAudio.play();
            playButton.innerHTML = '<i class="fa-solid fa-stop"></i>';
        } else {
            overlayAudio.pause();
            overlayAudio.currentTime = 0;
            playButton.innerHTML = '<i class="fa-solid fa-play"></i>';
        }

        overlayAudio.addEventListener('ended', () => {
            playButton.innerHTML = '<i class="fa-solid fa-play"></i>';
        });
    }
}

// DRAG-FUNKTION
function makeDraggable(el) {
    let isDown = false;
    let offsetX = 0;
    let offsetY = 0;

    el.addEventListener('mousedown', function(e) {
        if (e.target.classList.contains('spectrogram-close') ||
            e.target.classList.contains('spectrogram-download') ||
            e.target.tagName === 'IMG' ||
            e.target.classList.contains('spectrogram-play')) {
            return;
        }
        isDown = true;
        offsetX = e.clientX - el.offsetLeft;
        offsetY = e.clientY - el.offsetTop;
        el.classList.add('grabbing');
    });

    document.addEventListener('mouseup', function() {
        if (isDown) {
            isDown = false;
            el.classList.remove('grabbing');
        }
    });

    document.addEventListener('mousemove', function(e) {
        if (!isDown) return;
        el.style.left = (e.clientX - offsetX) + 'px';
        el.style.top  = (e.clientY - offsetY) + 'px';
    });
}

// Event-Listener registrieren
document.addEventListener('DOMContentLoaded', function() {
    makeDraggable(document.getElementById('spectrogramContent'));

    const playButton = document.getElementById('spectrogramPlay');
    if (playButton) {
        playButton.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSpectrogramAudio();
        });
    }

    // Neuer Listener: Schließt das Overlay, wenn außerhalb des Inhalts geklickt wird.
    const overlay = document.getElementById('spectrogramOverlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            // Wenn der Klick direkt auf das Overlay (und nicht auf ein untergeordnetes Element) erfolgt:
            if (e.target === overlay) {
                closeSpectrogramOverlay();
            }
        });
    }
});



// FOOTER
// FOOTER
// FOOTER

document.addEventListener('DOMContentLoaded', function () {

    const totalWordCountElement = document.getElementById('totalWordCount');
    const totalDurationElement = document.getElementById('totalDuration');
    
    // Statistiken aus stats_all.db laden
    fetch('/get_stats_all_from_db')
      .then(response => response.json())
      .then(data => {
        const totalWordCountFromDB = data.total_word_count;
        const totalDurationFromDB = data.total_duration_all;
  
        // Setze die globalen Variablen und aktualisiere die Statistiken
        updateTotalStats(totalWordCountFromDB, totalDurationFromDB);
      })
      .catch(error => {
        console.error('Error fetching statistics from the database:', error);
      });
  
    function updateTotalStats(totalWordCount, totalDuration) {
      // Aktualisiere die HTML-Elemente
      totalDurationElement.innerHTML = `<span style="color: #053c96; font-weight: bold;">${totalDuration}</span> horas de audio`;
      totalWordCountElement.innerHTML = `<span style="color: #053c96; font-weight: bold;">${totalWordCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')}</span> palabras transcritas`;
    }                     
      
  });

// Filter Dropdown

function toggleDrop(id){
    document.getElementById('drop-'+id)
            .classList.toggle('open');
  }
  
  /* Klick ausserhalb schliesst alle */
  document.addEventListener('click',e=>{
    if(!e.target.closest('.dropdown-select')){
      document.querySelectorAll('.dropdown-select .select-menu.open')
              .forEach(m=>m.classList.remove('open'));
    }
  });
  
/**
 * Sammelt Token‑IDs im Hidden‑Feld und zeigt sie als „Chips“ an.
 */
/**
 * Vor dem Abschicken die neue TokenID ins versteckte Feld packen.
 * Gibt true zurück, damit das Formular gesendet wird.
 */
function addTokens() {
    const inp = document.getElementById('token_new');
    const hid = document.getElementById('token_ids_hidden');
    const tok = inp.value.trim();
    if (!tok) {
      // nichts eingegeben → Abbruch
      return false;
    }
    // vorhandene Liste holen und ergänzen, falls neu
    const arr = hid.value ? hid.value.split(',') : [];
    if (!arr.includes(tok)) arr.push(tok);
    hid.value = arr.join(',');
    // Eingabe zurücksetzen (optional)
    inp.value = '';
    return true;  // Formular wird jetzt normal abgeschickt
  }
  
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("#searchform");
    if (form) {
        form.addEventListener("submit", function () {
            const resultsContainer = document.getElementById("results-container");
            const loadingIndicator = document.getElementById("loading-indicator");
            if (resultsContainer) resultsContainer.style.display = "none";
            if (loadingIndicator) loadingIndicator.style.display = "block";
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("searchform");
    const indicator = document.getElementById("loading-indicator");
  
    if (form && indicator) {
      form.addEventListener("submit", function () {
        indicator.style.display = "block";
  
        const spans = document.querySelectorAll("#buscandoText span");
        let i = 0;
        let toColor = true;
  
        function animateText() {
          if (i < spans.length) {
            spans[i].style.color = toColor ? "#053c96" : "#7e7e7e";
            i++;
            setTimeout(animateText, 80);
          } else {
            i = 0;
            toColor = !toColor;
            setTimeout(animateText, 400);
          }
        }
  
        animateText();
      });
    }
  });
  