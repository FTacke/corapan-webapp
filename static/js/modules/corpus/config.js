/**
 * Corpus Configuration & Constants
 * Zentrale Konfiguration für das Corpus-Modul
 */

export const MEDIA_ENDPOINT = "/media";

export const REGIONAL_OPTIONS = [
    { value: 'ARG-CHU', text: 'Argentina / Chubut', country: 'ARG' },
    { value: 'ARG-CBA', text: 'Argentina / Córdoba', country: 'ARG' },
    { value: 'ARG-SDE', text: 'Argentina / Santiago del Estero', country: 'ARG' },
    { value: 'ESP-CAN', text: 'España / Canarias', country: 'ESP' },
    { value: 'ESP-SEV', text: 'España / Sevilla', country: 'ESP' }
];

export const SELECT2_CONFIG = {
    placeholder: 'Seleccionar...',
    allowClear: true,
    closeOnSelect: false,
    language: {
        noResults: () => "No se encontraron resultados"
    }
};

/**
 * Check if public temp audio is allowed
 */
export function allowTempMedia() {
    return (window.__CORAPAN__?.allowPublicTempAudio === true) || 
           (window.ALLOW_PUBLIC_TEMP_AUDIO === 'true') || 
           (window.IS_AUTHENTICATED === 'true');
}
