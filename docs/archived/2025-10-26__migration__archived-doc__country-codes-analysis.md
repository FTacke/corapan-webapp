# Análisis de Códigos de País en CO.RA.PAN

**Fecha:** 19 de octubre de 2025  
**Autor:** Análisis del sistema

---

## 📋 Resumen Ejecutivo

Este documento analiza el uso de códigos de país en CO.RA.PAN, identifica inconsistencias y propone un sistema estandarizado para distinguir entre:
- **Capitales nacionales** (nivel país)
- **Capitales regionales** (nivel provincia/región)

---

## 🔍 A) SITUACIÓN ACTUAL: Dónde se referencian los códigos

### 1. **Base de datos** (`data/db/`)

#### `transcription.db` - Tabla `tokens`
- **Campo:** `country_code` (TEXT)
- **Uso:** ~1.4 millones de tokens indexados por país
- **Valores actuales:**
```
ARG         → 92,132 tokens  (Buenos Aires, capital nacional)
ARG-Cba     → 29,751 tokens  (Córdoba, capital regional)
ARG-Cht     → 30,043 tokens  (Chubut/Trelew, capital regional)
ARG-SdE     → 28,508 tokens  (Santiago del Estero, capital regional)
ES-MAD      → 69,114 tokens  (Madrid, capital nacional)
ES-SEV      → 69,009 tokens  (Sevilla, capital regional)
ES-CAN      → 66,275 tokens  (Canarias/La Laguna, capital regional)
CHI         → 63,967 tokens  (Santiago, capital nacional)
MEX         → 62,125 tokens  (Ciudad de México, capital nacional)
... (21 países en total)
```

#### `stats_country.db` - Tabla `stats_country`
- **Campo:** `country` (TEXT)
- **Problema:** Usa **nombres completos en español** en vez de códigos
- **Ejemplos:** "Argentina", "España/Madrid", "España/Canarias", "Argentina/Córdoba"
- **Inconsistencia:** No coincide con `country_code` de `transcription.db`

#### `stats_files.db` - Tabla `metadata`
- **Campo:** `country` (TEXT)
- **Problema:** También usa nombres completos, no códigos
- **Uso:** Metadatos por archivo (fecha, radio, duración, etc.)

### 2. **Frontend - Templates HTML**

#### `templates/pages/corpus.html`
```html
<select id="filter-country" name="country_code" multiple>
  <option value="ARG">Argentina</option>
  <option value="ARG-CHT">Argentina / Chubut</option>
  <option value="ARG-CBA">Argentina / Córdoba</option>
  <option value="ARG-SDE">Argentina / Santiago del Estero</option>
  <option value="ES-MAD">España / Madrid</option>
  <option value="ES-SEV">España / Sevilla</option>
  <option value="ES-CAN">España / Canarias</option>
  ...
</select>
```
**Problema:** Códigos en MAYÚSCULAS con variantes (`ARG-CHT`, `ARG-CBA`, `ARG-SDE`) vs. base de datos (`ARG-Cht`, `ARG-Cba`, `ARG-SdE`)

### 3. **Frontend - JavaScript**

#### `static/js/atlas_script.js`
```javascript
const cityList = [
  { name: 'Argentina: Buenos Aires', code: 'ARG' },
  { name: 'Argentina: Trelew (Chubut)', code: 'ARG-Cht' },
  { name: 'Argentina: Córdoba (Córdoba)', code: 'ARG-Cba' },
  { name: 'Argentina: Santiago del Estero (Santiago del Estero)', code: 'ARG-SdE' },
  { name: 'España: Madrid', code: 'ES-MAD' },
  { name: 'España: La Laguna (Canarias)', code: 'ES-CAN' },
  { name: 'España: Sevilla (Andalucía)', code: 'ES-SEV' },
  ...
];
```
**Observación:** Aquí los códigos regionales sí usan mayúsculas parciales (`ARG-Cba`, `ES-MAD`)

### 4. **Backend - Servicios Python**

#### `src/app/services/corpus_search.py`
```python
SUPPORTED_SORTS = {
    "pais": "country_code",
    "country_code": "country_code",
}
```
- **Consultas SQL:** `WHERE country_code IN (...)`
- **Filtros:** Búsqueda por códigos desde formularios

#### `src/app/services/media_store.py`
```python
def extract_country_code(filename: str) -> Optional[str]:
    # Pattern: YYYY-MM-DD_CODE_*
    # Supports: ARG, VEN, ES-MAD, ARG-Cba, ARG-Cht, ARG-SdE
    match = re.match(r'\d{4}-\d{2}-\d{2}_([A-Z]{2,3}(?:-[A-Za-z]{3})?)', filename)
```
- **Estructura de archivos:** `media/transcripts/ARG/`, `media/transcripts/ES-CAN/`
- **Nombres de archivo:** `2022-01-18_VEN_RCR.json`, `2023-08-10_ARG_Mitre.json`

#### `src/app/routes/corpus.py`
```python
countries = request.args.getlist("country_code")
# ...
5: "country_code",  # País (columna en CSV export)
```

### 5. **Estructura de carpetas**

```
media/transcripts/
├── ARG/
├── ARG-Cba/
├── ARG-Cht/
├── ARG-SdE/
├── BOL/
├── CHI/
├── COL/
├── ES-CAN/
├── ES-MAD/
├── ES-SEV/
├── MEX/
├── VEN/
└── ... (24 carpetas en total)
```

---

## 🌍 B) PROPUESTA: Códigos estandarizados según ISO 3166-1 alpha-3 + extensión regional

### ✅ Sistema recomendado

#### **Nivel 1: Códigos nacionales (ISO 3166-1 alpha-3 en español)**

| País | Código actual | Código propuesto | Observaciones |
|------|---------------|------------------|---------------|
| Argentina | `ARG` | `ARG` | ✅ Correcto (ISO 3166-1) |
| Bolivia | `BOL` | `BOL` | ✅ Correcto |
| Chile | `CHI` | `CHL` | ⚠️ ISO usa `CHL`, no `CHI` |
| Colombia | `COL` | `COL` | ✅ Correcto |
| Costa Rica | `CR` | `CRI` | ⚠️ ISO usa `CRI` (alpha-3), no `CR` (alpha-2) |
| Cuba | `CUB` | `CUB` | ✅ Correcto |
| Ecuador | `ECU` | `ECU` | ✅ Correcto |
| El Salvador | `SAL` | `SLV` | ⚠️ ISO usa `SLV`, no `SAL` |
| España | `ES-MAD` | `ESP` | ⚠️ Actualmente usa código regional para capital |
| Guatemala | `GUA` | `GTM` | ⚠️ ISO usa `GTM`, no `GUA` |
| Honduras | `HON` | `HND` | ⚠️ ISO usa `HND`, no `HON` |
| México | `MEX` | `MEX` | ✅ Correcto |
| Nicaragua | `NIC` | `NIC` | ✅ Correcto |
| Panamá | `PAN` | `PAN` | ✅ Correcto |
| Paraguay | `PAR` | `PRY` | ⚠️ ISO usa `PRY`, no `PAR` |
| Perú | `PER` | `PER` | ✅ Correcto |
| Rep. Dominicana | `RD` | `DOM` | ⚠️ ISO usa `DOM`, no `RD` |
| Uruguay | `URU` | `URY` | ⚠️ ISO usa `URY`, no `URU` |
| Venezuela | `VEN` | `VEN` | ✅ Correcto |

#### **Nivel 2: Códigos regionales (Nacional + guion + código regional)**

**Formato:** `{ISO-3}-{REGION-3}`  
**Ejemplo:** `ARG-CBA` (Argentina, Córdoba), `ESP-CAN` (España, Canarias)

| Región actual | Código actual | Código propuesto | Significado |
|---------------|---------------|------------------|-------------|
| Buenos Aires (capital nacional) | `ARG` | `ARG` | Capital nacional (sin sufijo) |
| Córdoba | `ARG-Cba` | `ARG-CBA` | Capital regional (Córdoba) |
| Chubut/Trelew | `ARG-Cht` | `ARG-CHU` | Capital regional (Chubut) |
| Santiago del Estero | `ARG-SdE` | `ARG-SDE` | Capital regional (Santiago del Estero) |
| Madrid (capital nacional) | `ES-MAD` | `ESP` | ⚠️ Capital nacional (sin sufijo) |
| Sevilla | `ES-SEV` | `ESP-SEV` | Capital regional (Sevilla/Andalucía) |
| Canarias | `ES-CAN` | `ESP-CAN` | Capital regional (Canarias) |

### 🎯 Regla de oro

1. **Capital nacional** = Código ISO 3166-1 alpha-3 **sin sufijo**
   - Ejemplos: `ARG`, `ESP`, `MEX`, `CHL`
   
2. **Capital regional / provincia** = Código nacional + `-` + código regional de 3 letras **en MAYÚSCULAS**
   - Ejemplos: `ARG-CBA`, `ESP-CAN`, `ESP-SEV`

3. **Consistencia:** Siempre usar **MAYÚSCULAS** para los códigos (tanto en DB como en frontend)

---

## 🚨 C) INCONSISTENCIAS ACTUALES

### 1. **Argentina: ARG vs. ARG con regiones**

**Problema actual:**
- `ARG` → Buenos Aires (capital nacional)
- Pero `ARG` **no es explícito** que se refiere a Buenos Aires

**Propuesta:**
- Mantener `ARG` para Buenos Aires (capital nacional implícita)
- O usar `ARG-BUE` si se quiere ser explícito
- **Regionales:** `ARG-CBA`, `ARG-CHU`, `ARG-SDE` (todas MAYÚSCULAS)

### 2. **España: ES-MAD como nacional**

**Problema actual:**
- `ES-MAD` se usa para Madrid (capital nacional)
- Pero formato `XX-YYY` sugiere que es regional

**Propuesta:**
- **Cambiar `ES-MAD` → `ESP`** (código nacional sin sufijo)
- `ESP-SEV` (Sevilla, Andalucía - regional)
- `ESP-CAN` (Canarias - regional)

### 3. **Mayúsculas inconsistentes**

**Problema actual:**
- DB: `ARG-Cba`, `ARG-Cht`, `ARG-SdE` (mixed case)
- HTML: `ARG-CBA`, `ARG-CHT`, `ARG-SDE` (MAYÚSCULAS)
- JS: `ARG-Cba`, `ES-MAD` (mixed case)

**Propuesta:**
- **TODO EN MAYÚSCULAS:** `ARG-CBA`, `ARG-CHU`, `ARG-SDE`, `ESP`, `ESP-CAN`, `ESP-SEV`

### 4. **stats_country.db usa nombres, no códigos**

**Problema actual:**
```sql
SELECT * FROM stats_country;
-- "Argentina", "España/Madrid", "España/Canarias"
```

**Propuesta:**
- **Cambiar campo `country` a `country_code`**
- Usar códigos: `ARG`, `ESP`, `ESP-CAN`, `ESP-SEV`
- Agregar nuevo campo opcional `country_name` para display

### 5. **Códigos ISO incorrectos**

**Problema actual:**
- `CHI` (debería ser `CHL`)
- `CR` (debería ser `CRI`)
- `SAL` (debería ser `SLV`)
- `GUA` (debería ser `GTM`)
- `HON` (debería ser `HND`)
- `PAR` (debería ser `PRY`)
- `RD` (debería ser `DOM`)
- `URU` (debería ser `URY`)

**Propuesta:**
- **Opción A (conservadora):** Mantener códigos actuales por compatibilidad
- **Opción B (estándar):** Migrar gradualmente a ISO 3166-1 alpha-3 estricto

---

## 📊 D) LUGARES DONDE SE REQUIERE CAMBIO

### 1. **Base de datos** (prioridad: ALTA)

#### Cambios necesarios:

**`data/db/transcription.db`**
```sql
-- Si se decide normalizar mayúsculas:
UPDATE tokens SET country_code = 'ARG-CBA' WHERE country_code = 'ARG-Cba';
UPDATE tokens SET country_code = 'ARG-CHU' WHERE country_code = 'ARG-Cht';
UPDATE tokens SET country_code = 'ARG-SDE' WHERE country_code = 'ARG-SdE';
UPDATE tokens SET country_code = 'ESP' WHERE country_code = 'ES-MAD';
UPDATE tokens SET country_code = 'ESP-CAN' WHERE country_code = 'ES-CAN';
UPDATE tokens SET country_code = 'ESP-SEV' WHERE country_code = 'ES-SEV';
```

**`data/db/stats_country.db`**
```sql
-- Opción 1: Renombrar campo y usar códigos
ALTER TABLE stats_country ADD COLUMN country_code TEXT;
UPDATE stats_country SET country_code = 'ARG' WHERE country = 'Argentina';
UPDATE stats_country SET country_code = 'ESP' WHERE country = 'España/Madrid';
UPDATE stats_country SET country_code = 'ESP-CAN' WHERE country = 'España/Canarias';
-- ...
-- Después: DROP old column, RENAME new column

-- Opción 2: Mantener 'country' como nombre display y agregar 'country_code'
```

### 2. **Scripts de creación de DB** (prioridad: ALTA)

**`LOKAL/database/database_creation_v2.py`**
- Línea ~318-340: Cambiar lógica de `country_val = data.get("country", "")`
- Agregar función de mapeo `map_country_name_to_code(name: str) -> str`
- Modificar `stats_country` para insertar códigos en vez de nombres

### 3. **Frontend - Templates** (prioridad: ALTA)

**`templates/pages/corpus.html`**
```html
<!-- Actualizar todos los valores de option a MAYÚSCULAS -->
<option value="ARG">Argentina: Buenos Aires</option>
<option value="ARG-CBA">Argentina: Córdoba</option>
<option value="ARG-CHU">Argentina: Chubut</option>
<option value="ARG-SDE">Argentina: Santiago del Estero</option>
<option value="ESP">España: Madrid</option>
<option value="ESP-CAN">España: Canarias</option>
<option value="ESP-SEV">España: Sevilla</option>
```

### 4. **Frontend - JavaScript** (prioridad: ALTA)

**`static/js/atlas_script.js`**
```javascript
const cityList = [
  // Capitales NACIONALES (sin sufijo regional)
  { name: 'Argentina: Buenos Aires', code: 'ARG', type: 'national' },
  { name: 'España: Madrid', code: 'ESP', type: 'national' },
  { name: 'México: Ciudad de México', code: 'MEX', type: 'national' },
  
  // Capitales REGIONALES (con sufijo)
  { name: 'Argentina: Córdoba', code: 'ARG-CBA', type: 'regional' },
  { name: 'Argentina: Trelew (Chubut)', code: 'ARG-CHU', type: 'regional' },
  { name: 'Argentina: Santiago del Estero', code: 'ARG-SDE', type: 'regional' },
  { name: 'España: La Laguna (Canarias)', code: 'ESP-CAN', type: 'regional' },
  { name: 'España: Sevilla', code: 'ESP-SEV', type: 'regional' },
  ...
];

// Agregar filtros por tipo
function filterNationalCapitals() {
  return cityList.filter(city => city.type === 'national');
}

function filterRegionalCapitals() {
  return cityList.filter(city => city.type === 'regional');
}
```

### 5. **Backend - Servicios** (prioridad: MEDIA)

**`src/app/services/media_store.py`**
```python
def extract_country_code(filename: str) -> Optional[str]:
    # Actualizar regex para soportar códigos normalizados:
    # ARG, ESP, ARG-CBA, ESP-CAN (todo MAYÚSCULAS)
    match = re.match(r'\d{4}-\d{2}-\d{2}_([A-Z]{2,3}(?:-[A-Z]{3})?)', filename)
    if match:
        return match.group(1)
    return None
```

**`src/app/services/atlas.py`**
- Agregar helper para convertir códigos a nombres display

**`src/app/routes/corpus.py`**
- Normalizar códigos entrantes de formularios (`.upper()`)

### 6. **Estructura de archivos** (prioridad: BAJA - solo si renombras carpetas)

**`media/transcripts/`**
```
Opción 1 (conservadora): Mantener nombres actuales
ARG/, ARG-Cba/, ARG-Cht/, ES-MAD/ ...

Opción 2 (normalizada): Renombrar carpetas
ARG/, ARG-CBA/, ARG-CHU/, ESP/, ESP-CAN/, ESP-SEV/ ...
```

---

## 🎨 E) PROPUESTA DE SISTEMA CENTRALIZADO

### Crear archivo de configuración: `src/app/config/countries.py`

```python
"""
Configuración centralizada de códigos de país y regiones.
Sigue ISO 3166-1 alpha-3 con extensiones regionales.
"""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Location:
    """Representa una ubicación (país o región)."""
    code: str  # Código único (e.g., 'ARG', 'ARG-CBA', 'ESP')
    name_es: str  # Nombre completo en español
    type: Literal['national', 'regional']  # Tipo de capital
    country_code: str  # Código del país padre (e.g., 'ARG', 'ESP')
    iso_code: str | None = None  # Código ISO oficial (si aplica)

# ============================================================================
# DEFINICIONES DE PAÍSES Y REGIONES
# ============================================================================

LOCATIONS = [
    # ARGENTINA
    Location('ARG', 'Argentina: Buenos Aires', 'national', 'ARG', 'ARG'),
    Location('ARG-CBA', 'Argentina: Córdoba', 'regional', 'ARG'),
    Location('ARG-CHU', 'Argentina: Chubut (Trelew)', 'regional', 'ARG'),
    Location('ARG-SDE', 'Argentina: Santiago del Estero', 'regional', 'ARG'),
    
    # BOLIVIA
    Location('BOL', 'Bolivia: La Paz', 'national', 'BOL', 'BOL'),
    
    # CHILE
    Location('CHL', 'Chile: Santiago', 'national', 'CHL', 'CHL'),
    
    # COLOMBIA
    Location('COL', 'Colombia: Bogotá', 'national', 'COL', 'COL'),
    
    # COSTA RICA
    Location('CRI', 'Costa Rica: San José', 'national', 'CRI', 'CRI'),
    
    # CUBA
    Location('CUB', 'Cuba: La Habana', 'national', 'CUB', 'CUB'),
    
    # ECUADOR
    Location('ECU', 'Ecuador: Quito', 'national', 'ECU', 'ECU'),
    
    # ESPAÑA
    Location('ESP', 'España: Madrid', 'national', 'ESP', 'ESP'),
    Location('ESP-CAN', 'España: La Laguna (Canarias)', 'regional', 'ESP'),
    Location('ESP-SEV', 'España: Sevilla (Andalucía)', 'regional', 'ESP'),
    
    # EL SALVADOR
    Location('SLV', 'El Salvador: San Salvador', 'national', 'SLV', 'SLV'),
    
    # GUATEMALA
    Location('GTM', 'Guatemala: Ciudad de Guatemala', 'national', 'GTM', 'GTM'),
    
    # HONDURAS
    Location('HND', 'Honduras: Tegucigalpa', 'national', 'HND', 'HND'),
    
    # MÉXICO
    Location('MEX', 'México: Ciudad de México', 'national', 'MEX', 'MEX'),
    
    # NICARAGUA
    Location('NIC', 'Nicaragua: Managua', 'national', 'NIC', 'NIC'),
    
    # PANAMÁ
    Location('PAN', 'Panamá: Ciudad de Panamá', 'national', 'PAN', 'PAN'),
    
    # PARAGUAY
    Location('PRY', 'Paraguay: Asunción', 'national', 'PRY', 'PRY'),
    
    # PERÚ
    Location('PER', 'Perú: Lima', 'national', 'PER', 'PER'),
    
    # REPÚBLICA DOMINICANA
    Location('DOM', 'República Dominicana: Santo Domingo', 'national', 'DOM', 'DOM'),
    
    # URUGUAY
    Location('URY', 'Uruguay: Montevideo', 'national', 'URY', 'URY'),
    
    # VENEZUELA
    Location('VEN', 'Venezuela: Caracas', 'national', 'VEN', 'VEN'),
]

# ============================================================================
# MAPEOS PARA COMPATIBILIDAD CON CÓDIGOS ANTIGUOS
# ============================================================================

LEGACY_CODE_MAP = {
    # Códigos antiguos → Códigos nuevos
    'CHI': 'CHL',
    'CR': 'CRI',
    'SAL': 'SLV',
    'GUA': 'GTM',
    'HON': 'HND',
    'PAR': 'PRY',
    'RD': 'DOM',
    'URU': 'URY',
    
    # Regionales (mixed case → MAYÚSCULAS)
    'ARG-Cba': 'ARG-CBA',
    'ARG-Cht': 'ARG-CHU',
    'ARG-SdE': 'ARG-SDE',
    'ES-MAD': 'ESP',
    'ES-CAN': 'ESP-CAN',
    'ES-SEV': 'ESP-SEV',
}

# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def normalize_country_code(code: str) -> str:
    """Normaliza código antiguo a nuevo estándar."""
    return LEGACY_CODE_MAP.get(code, code.upper())

def get_location(code: str) -> Location | None:
    """Obtiene ubicación por código."""
    normalized = normalize_country_code(code)
    for loc in LOCATIONS:
        if loc.code == normalized:
            return loc
    return None

def get_national_capitals() -> list[Location]:
    """Devuelve solo capitales nacionales."""
    return [loc for loc in LOCATIONS if loc.type == 'national']

def get_regional_capitals() -> list[Location]:
    """Devuelve solo capitales regionales."""
    return [loc for loc in LOCATIONS if loc.type == 'regional']

def get_locations_by_country(country_code: str) -> list[Location]:
    """Devuelve todas las ubicaciones de un país."""
    return [loc for loc in LOCATIONS if loc.country_code == country_code]

def code_to_name(code: str) -> str:
    """Convierte código a nombre en español."""
    loc = get_location(code)
    return loc.name_es if loc else code
```

---

## 🛠️ F) PLAN DE MIGRACIÓN

### Fase 1: Preparación (sin cambios en producción)
1. ✅ Crear `src/app/config/countries.py` con sistema centralizado
2. ✅ Agregar tests unitarios para funciones de mapeo
3. ✅ Documentar cambios en este archivo

### Fase 2: Backend (cambios internos)
1. 🔄 Modificar `LOKAL/database/database_creation_v2.py` para usar códigos normalizados
2. 🔄 Actualizar servicios Python para normalizar códigos entrantes
3. 🔄 Agregar funciones helper en `src/app/services/` para conversión código↔nombre

### Fase 3: Base de datos (requiere backup)
1. 🔄 Backup completo de `data/db/*.db`
2. 🔄 Ejecutar script de migración SQL (UPDATE masivo)
3. 🔄 Actualizar índices y reoptimizar

### Fase 4: Frontend
1. 🔄 Actualizar `templates/pages/corpus.html` con códigos normalizados
2. 🔄 Actualizar `static/js/atlas_script.js` con nueva estructura
3. 🔄 Agregar campo `type` para distinguir nacional/regional

### Fase 5: Testing
1. 🔄 Probar búsquedas en corpus con nuevos códigos
2. 🔄 Verificar visualización de atlas
3. 🔄 Comprobar exports CSV

### Fase 6: Archivos (opcional)
1. ❓ Decidir si renombrar carpetas `media/transcripts/`
2. ❓ Decidir si renombrar archivos JSON

---

## ✅ G) RECOMENDACIONES FINALES

### 1. **Mantener compatibilidad con códigos actuales**
   - No romper búsquedas existentes
   - Usar `LEGACY_CODE_MAP` para conversión automática
   - Agregar warnings en logs cuando se usen códigos antiguos

### 2. **Distinguir nacional vs. regional en UI**
   - Agregar iconos/badges: 🏛️ Nacional | 🏙️ Regional
   - Permitir filtros por tipo en corpus y atlas
   - Mostrar jerarquía en breadcrumbs: `España > Canarias`

### 3. **Usar siempre MAYÚSCULAS para códigos**
   - DB: `ARG-CBA` (no `ARG-Cba`)
   - Frontend: `ARG-CBA` (no `ARG-cba`)
   - Archivos: `ARG-CBA/` (o mantener actuales por compatibilidad)

### 4. **Centralizar configuración**
   - Un solo archivo fuente de verdad: `countries.py`
   - Generar automáticamente opciones de formularios
   - Exportar JSON para JavaScript: `/api/countries.json`

### 5. **Documentar en webapp**
   - Agregar página "Metodología > Códigos geográficos"
   - Explicar diferencia nacional/regional
   - Tabla con todos los códigos y nombres

---

## 📌 H) DECISIONES PENDIENTES

### ¿Migrar a ISO 3166-1 alpha-3 estricto?

**Opción A (conservadora):** Mantener códigos actuales
- ✅ No requiere cambios masivos en archivos
- ✅ Compatibilidad total con datos existentes
- ❌ Códigos no estándar (`CHI`, `SAL`, etc.)

**Opción B (estándar):** Migrar a ISO completo
- ✅ Códigos internacionales reconocidos
- ✅ Mejor interoperabilidad
- ❌ Requiere renombrar ~1000 archivos
- ❌ Cambiar millones de registros en DB

**Recomendación:** **Opción A + mapeo interno**
- Mantener códigos actuales en archivos/DB
- Usar `LEGACY_CODE_MAP` para traducir a ISO cuando sea necesario
- Mostrar códigos ISO en documentación académica

### ¿Renombrar carpetas y archivos?

**Opción A:** Mantener nombres actuales
- `media/transcripts/ARG/`, `ARG-Cba/`, `ES-MAD/`
- ✅ Cero trabajo de migración
- ❌ Inconsistencia con nuevos estándares

**Opción B:** Renombrar todo
- `media/transcripts/ARG/`, `ARG-CBA/`, `ESP/`
- ✅ Consistencia total
- ❌ Alto riesgo de romper referencias

**Recomendación:** **Opción A inicialmente**
- Priorizar consistencia en DB y frontend
- Dejar archivos para migración futura opcional

---

## 📅 Próximos pasos

1. **Revisar este documento** y decidir:
   - ¿Mantener códigos actuales o migrar a ISO?
   - ¿Cambiar `ES-MAD` → `ESP`?
   - ¿Renombrar carpetas o solo DB?

2. **Crear `countries.py`** con sistema centralizado

3. **Implementar migración gradual** (backend → DB → frontend)

4. **Documentar cambios** en changelog y guía de usuario

---

**Fin del análisis** | 19.10.2025
