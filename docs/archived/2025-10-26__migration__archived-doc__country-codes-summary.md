# Resumen: Análisis de Códigos de País en CO.RA.PAN

## 📋 Archivos creados

1. **`LOKAL/COUNTRY_CODES_ANALYSIS.md`** ✅
   - Análisis completo del sistema actual
   - Propuestas de estandarización
   - Plan de migración detallado

2. **`src/app/config/countries.py`** ✅
   - Módulo centralizado de configuración
   - ~600 líneas de código bien documentado
   - 19 países + 5 regiones = 24 ubicaciones
   - Funciones helper para normalización y conversión

3. **`src/app/config/__init__.py`** ✅
   - Punto de entrada del paquete config

4. **`LOKAL/demo_countries.py`** ✅
   - Script de demostración (requiere ajuste menor)

---

## 🎯 Hallazgos principales

### A) Inconsistencias actuales

1. **Mayúsculas mixtas en DB:**
   - DB: `ARG-Cba`, `ARG-Cht`, `ARG-SdE`
   - HTML: `ARG-CBA`, `ARG-CHT`, `ARG-SDE`
   - ❌ Inconsistente

2. **España con código regional para capital nacional:**
   - Actual: `ES-MAD` (Madrid)
   - Problema: Parece regional, pero es capital nacional
   - ✅ Propuesta: Cambiar a `ESP` (sin sufijo)

3. **Argentina sin distinción explícita:**
   - `ARG` = Buenos Aires (implícito)
   - Funciona, pero no es obvio que es solo Buenos Aires

4. **stats_country.db usa nombres, no códigos:**
   - Actual: `"Argentina"`, `"España/Madrid"`
   - ❌ Dificulta joins con `transcription.db`
   - ✅ Propuesta: Usar `country_code` en ambas

5. **Códigos no ISO:**
   - `CHI` → debería ser `CHL`
   - `CR` → debería ser `CRI`
   - `SAL` → debería ser `SLV`
   - ... (8 códigos en total)

### B) Solución propuesta

#### **Sistema de códigos:**

```
NACIONAL:  {ISO-3}           (e.g., ARG, ESP, MEX)
REGIONAL:  {ISO-3}-{REG-3}   (e.g., ARG-CBA, ESP-CAN)
```

#### **Reglas:**

1. Capital nacional = código ISO sin sufijo
2. Capital regional = código nacional + guion + 3 letras regionales
3. TODO EN MAYÚSCULAS
4. Un solo módulo centralizado (`countries.py`)

---

## 🔧 Uso del módulo `countries.py`

### Normalización automática:

```python
from app.config.countries import normalize_country_code

# Códigos antiguos/inconsistentes → estándar
normalize_country_code('CHI')        # → 'CHL'
normalize_country_code('arg')        # → 'ARG'
normalize_country_code('ARG-Cba')    # → 'ARG-CBA'
normalize_country_code('ES-MAD')     # → 'ESP'
```

### Conversión código ↔ nombre:

```python
from app.config.countries import code_to_name, name_to_code

code_to_name('ARG')          # → 'Argentina: Buenos Aires'
code_to_name('ARG-CBA')      # → 'Argentina: Córdoba'
code_to_name('ESP')          # → 'España: Madrid'

name_to_code('Argentina')              # → 'ARG'
name_to_code('España/Madrid')          # → 'ESP'
name_to_code('Argentina/Córdoba')      # → 'ARG-CBA'
```

### Filtrado:

```python
from app.config.countries import (
    get_national_capitals,
    get_regional_capitals,
    get_locations_by_country
)

# Solo capitales nacionales
nationals = get_national_capitals()  # 19 ubicaciones
# → [ARG, BOL, CHL, COL, CRI, CUB, ECU, ...]

# Solo capitales regionales
regionals = get_regional_capitals()  # 5 ubicaciones
# → [ARG-CBA, ARG-CHU, ARG-SDE, ESP-CAN, ESP-SEV]

# Todas las ubicaciones de un país
argentina_locs = get_locations_by_country('ARG')
# → [ARG, ARG-CBA, ARG-CHU, ARG-SDE]
```

### Validación:

```python
from app.config.countries import is_national_capital, is_regional_capital

is_national_capital('ARG')      # → True
is_national_capital('ARG-CBA')  # → False

is_regional_capital('ARG-CBA')  # → True
is_regional_capital('ARG')      # → False
```

---

## 📊 Estadísticas del corpus

**Total de ubicaciones:** 24
- **Nacionales:** 19
- **Regionales:** 5 (4 en Argentina, 1 en España con 2 regiones)

**Países con regiones:**
- Argentina: ARG + ARG-CBA + ARG-CHU + ARG-SDE
- España: ESP + ESP-CAN + ESP-SEV

**Distribución de tokens en DB:**
```
ARG      → 92,132 tokens   (Buenos Aires)
ES-MAD   → 69,114 tokens   (Madrid - debería ser ESP)
ES-SEV   → 69,009 tokens   (Sevilla)
ES-CAN   → 66,275 tokens   (Canarias)
CHI      → 63,967 tokens   (Santiago - debería ser CHL)
ARG-Cba  → 29,751 tokens   (Córdoba - debería ser ARG-CBA)
ARG-Cht  → 30,043 tokens   (Chubut - debería ser ARG-CHU)
ARG-SdE  → 28,508 tokens   (S. del Estero - debería ser ARG-SDE)
```

---

## 🛠️ Próximos pasos recomendados

### Opción A: Migración completa (recomendada)

1. ✅ Usar `countries.py` como fuente de verdad
2. 🔄 Crear script de migración SQL para actualizar DB
3. 🔄 Actualizar templates HTML con códigos normalizados
4. 🔄 Actualizar `atlas_script.js` con códigos normalizados
5. 🔄 Modificar `database_creation_v2.py` para usar códigos
6. 🔄 Agregar endpoint `/api/locations.json` para JavaScript
7. ✅ Testing exhaustivo

### Opción B: Migración gradual (conservadora)

1. ✅ Integrar `countries.py` en el código
2. 🔄 Usar `normalize_country_code()` en todas las entradas de usuario
3. 🔄 Mantener compatibilidad con códigos antiguos (vía LEGACY_CODE_MAP)
4. 🔄 Actualizar solo frontend (HTML + JS)
5. 🔄 Dejar DB y archivos sin cambios por ahora
6. 🔄 Migración de DB en fase posterior

### Decisiones pendientes:

- [ ] ¿Cambiar `ES-MAD` → `ESP` en DB y archivos?
- [ ] ¿Normalizar `ARG-Cba` → `ARG-CBA` en DB?
- [ ] ¿Migrar a ISO estricto (`CHI` → `CHL`) o mantener?
- [ ] ¿Renombrar carpetas en `media/transcripts/`?

---

## 📝 Beneficios de la centralización

### Antes (descentralizado):

```
❌ Códigos en 5 lugares diferentes:
   • DB: country_code (mixed case)
   • HTML: country_code options (MAYÚSCULAS)
   • JS: cityList codes (mixed case)
   • Python: hardcoded strings
   • stats_country.db: nombres en español

❌ Sincronización manual requerida
❌ Inconsistencias inevitables
❌ Difícil de mantener
```

### Después (centralizado):

```
✅ Un solo archivo: src/app/config/countries.py
✅ Generación automática de:
   • Opciones de <select>
   • Datos para JavaScript
   • Queries SQL
   • Documentación

✅ Normalización automática de códigos
✅ Fácil de extender (agregar nuevos países/regiones)
✅ Type hints y documentación completa
```

---

## 🎨 Visualización propuesta en UI

### Corpus (filtro de países):

```
📍 CAPITALES NACIONALES
  🏛️ Argentina: Buenos Aires
  🏛️ Bolivia: La Paz
  🏛️ Chile: Santiago
  ...

📍 CAPITALES REGIONALES
  🏙️ Argentina: Córdoba
  🏙️ Argentina: Chubut (Trelew)
  🏙️ España: Canarias (La Laguna)
  🏙️ España: Sevilla
```

### Atlas (mapa):

- Marcadores primarios (🏛️) para nacionales
- Marcadores secundarios (🏙️) para regionales
- Color/icono diferenciado
- Tooltip con tipo de ubicación

---

## 📞 Contacto para dudas

Si hay preguntas sobre:
- Implementación de la migración
- Modificación del módulo `countries.py`
- Estrategia de testing
- Secuencia de cambios

→ Ver análisis completo en `LOKAL/COUNTRY_CODES_ANALYSIS.md`

---

**Fecha:** 19 de octubre de 2025
**Estado:** ✅ Análisis completo | ⏳ Implementación pendiente
