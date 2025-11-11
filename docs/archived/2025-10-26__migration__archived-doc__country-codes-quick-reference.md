# Códigos de País - Vista Rápida

## ✅ CÓDIGOS CORRECTOS (ISO 3166-1 alpha-3)

| Código | País | Capital | Tokens en DB |
|--------|------|---------|--------------|
| ARG | Argentina | Buenos Aires | 92,132 |
| BOL | Bolivia | La Paz | 52,986 |
| COL | Colombia | Bogotá | 62,001 |
| CUB | Cuba | La Habana | 59,095 |
| ECU | Ecuador | Quito | 48,593 |
| MEX | México | Ciudad de México | 62,125 |
| NIC | Nicaragua | Managua | 49,334 |
| PAN | Panamá | Ciudad de Panamá | 53,220 |
| PER | Perú | Lima | 57,790 |
| VEN | Venezuela | Caracas | 59,773 |

## ⚠️ CÓDIGOS NO ESTÁNDAR (requieren mapeo)

| Actual | Debería ser (ISO) | País | Observaciones |
|--------|-------------------|------|---------------|
| CHI | CHL | Chile | ISO usa CHL |
| CR | CRI | Costa Rica | alpha-2 → alpha-3 |
| SAL | SLV | El Salvador | ISO usa SLV |
| GUA | GTM | Guatemala | ISO usa GTM |
| HON | HND | Honduras | ISO usa HND |
| PAR | PRY | Paraguay | ISO usa PRY |
| RD | DOM | Rep. Dominicana | ISO usa DOM |
| URU | URY | Uruguay | ISO usa URY |

**Decisión:** Mantener códigos actuales + usar `LEGACY_CODE_MAP` para conversión

## 🏙️ CÓDIGOS REGIONALES

### Argentina (4 ubicaciones)

| Código Actual | Código Propuesto | Ubicación | Tokens |
|---------------|------------------|-----------|--------|
| **ARG** | **ARG** | Buenos Aires (capital nacional) 🏛️ | 92,132 |
| ARG-Cba | **ARG-CBA** | Córdoba (capital regional) 🏙️ | 29,751 |
| ARG-Cht | **ARG-CHU** | Chubut/Trelew (capital regional) 🏙️ | 30,043 |
| ARG-SdE | **ARG-SDE** | Santiago del Estero (capital regional) 🏙️ | 28,508 |

### España (3 ubicaciones)

| Código Actual | Código Propuesto | Ubicación | Tokens |
|---------------|------------------|-----------|--------|
| **ES-MAD** | **ESP** ⚠️ | Madrid (capital nacional) 🏛️ | 69,114 |
| ES-CAN | **ESP-CAN** | Canarias/La Laguna (capital regional) 🏙️ | 66,275 |
| ES-SEV | **ESP-SEV** | Sevilla/Andalucía (capital regional) 🏙️ | 69,009 |

**⚠️ Cambio importante:** `ES-MAD` → `ESP` (capital nacional debe ser sin sufijo)

## 📊 Resumen estadístico

```
Total de ubicaciones:  24
  ├─ Nacionales:       19  (🏛️ sin sufijo regional)
  └─ Regionales:        5  (🏙️ con sufijo -XXX)

Total de tokens:  ~1.4M
  ├─ Nacionales:  ~1.1M  (79%)
  └─ Regionales:  ~300K  (21%)

Países con datos regionales:
  ├─ Argentina:  4 ubicaciones (nacional + 3 regionales)
  └─ España:     3 ubicaciones (nacional + 2 regionales)
```

## 🔧 Cambios necesarios por ubicación

### Cambios de FORMATO (mayúsculas):

```
ARG-Cba  →  ARG-CBA  ✓
ARG-Cht  →  ARG-CHU  ✓
ARG-SdE  →  ARG-SDE  ✓
```

### Cambios de CONCEPTO (nacional vs. regional):

```
ES-MAD  →  ESP  ⚠️ (nacional, no regional)
```

### Cambios OPCIONALES (ISO estricto):

```
CHI  →  CHL  (opcional, con compatibilidad)
CR   →  CRI  (opcional, con compatibilidad)
SAL  →  SLV  (opcional, con compatibilidad)
...
```

## 🎯 Matriz de decisiones

| Aspecto | Opción A (Conservadora) | Opción B (Estándar) | Recomendación |
|---------|-------------------------|---------------------|---------------|
| **Mayúsculas** | Normalizar a MAYÚSCULAS | Normalizar a MAYÚSCULAS | ✅ OBLIGATORIO |
| **ES-MAD → ESP** | Cambiar | Cambiar | ✅ OBLIGATORIO |
| **ISO no estándar** | Mantener + mapeo | Migrar a ISO | ⚠️ Mantener + mapeo |
| **Archivos/carpetas** | No renombrar | Renombrar todo | ⚠️ No renombrar ahora |
| **stats_country.db** | Agregar country_code | Reemplazar nombres | ✅ Agregar campo |

## 📋 Lista de tareas prioritarias

### Alta prioridad (implementar ya):

- [ ] Integrar `src/app/config/countries.py` en app
- [ ] Normalizar códigos en `templates/pages/corpus.html` (MAYÚSCULAS)
- [ ] Actualizar `static/js/atlas_script.js` con códigos normalizados
- [ ] Cambiar `ES-MAD` → `ESP` en todos los archivos
- [ ] Agregar campo `country_code` a `stats_country.db`

### Media prioridad (planificar):

- [ ] Script de migración SQL para `transcription.db`
- [ ] Actualizar `database_creation_v2.py` para usar `countries.py`
- [ ] Crear endpoint `/api/locations.json` para JavaScript
- [ ] Tests unitarios para normalización

### Baja prioridad (futuro):

- [ ] Decidir si migrar a ISO estricto
- [ ] Evaluar renombrado de carpetas `media/transcripts/`
- [ ] Documentación de usuario (metodología)
- [ ] Agregar más regiones si es necesario

## 🚨 Puntos críticos

### ⚠️ No romper:

1. Búsquedas existentes en corpus
2. Referencias de archivos en `media/transcripts/`
3. Queries SQL que usan `country_code`
4. Exports CSV con columna país

### ✅ Asegurar:

1. Compatibilidad con códigos antiguos (vía mapeo)
2. Normalización automática en todas las entradas
3. Consistencia entre DB, frontend y backend
4. Tests antes de migración de DB

---

**Actualizado:** 19.10.2025  
**Ver análisis completo:** `LOKAL/COUNTRY_CODES_ANALYSIS.md`  
**Módulo centralizado:** `src/app/config/countries.py`
