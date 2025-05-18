## Requisitos previos

- Python 3.6 o superior
- Bibliotecas Python: `requests`, `tqdm`, `dotenv`, `concurrent.futures`
- Clave API de Google Places
- Archivos de datos:
  - Archivos CSV de POIs
  - Archivos GeoJSON de calles (streets_nav)
  - Archivos GeoJSON de nombres de calles (streets_naming_addressing)

## Estructura de carpetas recomendada

```
proyecto/
├── POIs/                          # Carpeta con los archivos CSV de POIs
├── STREETS_NAV/                   # Archivos GeoJSON de navegación de calles
├── STREETS_NAMING_ADDRESSING/     # Archivos GeoJSON de nombres de calles
├── scripts/
│   ├── unificar_pois_con_features_filtrado.py  # Filtrado por MULTIDIGIT
│   ├── procesarPOIs.py                         # Cálculo de coordenadas
│   └── verificar_pois_google_paralelo.py       # Verificación con Google Places
├── .env                           # Archivo con variables de entorno (API_GOOGLE)
└── README.md                      # Este archivo
```

## Paso 1: Filtrar POIs por MULTIDIGIT

El primer paso consiste en filtrar los POIs para obtener solamente aquellos que están en calles con MULTIDIGIT="Yes" y sin excepciones (RAMP, DIR_TRAVEL, MANOEUVRE).

### Ejecutar:

```bash
python scripts/unificar_pois_con_features_filtrado.py
```

### Entradas:
- Directorio con archivos CSV de POIs
- Directorio con archivos GeoJSON de streets_nav
- Directorio con archivos GeoJSON de streets_naming_addressing

### Salidas:
- Carpeta `pois_features_filtrados/` con archivos JSON de POIs filtrados
- Archivo `pois_features_filtrados/indice_general.json` con estadísticas
- Archivo `pois_features_filtrados/indice_por_link.json` para búsquedas

### Descripción:

Este script filtra los POIs para seleccionar únicamente los que están en calles con MULTIDIGIT="Yes" y que NO tienen ninguna de las excepciones (RAMP="Y", DIR_TRAVEL="B", o MANOEUVRE="Y"). Unifica la información de los POIs con los datos de las calles (geometría y nombres) y crea archivos JSON por lotes.

```
=== UNIFICACIÓN DE POIS CON FEATURES DE CALLES (FILTRO MULTIDIGIT SIN EXCEPCIONES) ===

Directorio de POIs [POIs]: POIs
Directorio de streets_nav [STREETS_NAV]: STREETS_NAV
Directorio de streets_naming_addressing [STREETS_NAMING_ADDRESSING]: STREETS_NAMING_ADDRESSING
Directorio de salida [pois_features_multidigit]: pois_features_filtrados
POIs por archivo [1000]: 1000
```

## Paso 2: Calcular coordenadas de los POIs filtrados

Una vez filtrados los POIs, necesitamos calcular sus coordenadas precisas basándonos en los datos de la calle, lado y porcentaje de distancia (PERCFRREF).

### Ejecutar:

```bash
python scripts/procesarPOIs.py
```

### Entradas:
- Directorio con los POIs filtrados (del paso anterior)

### Salidas:
- Archivo `resultados_pois_completos.json` con todos los resultados detallados
- Archivo `resumen_pois.json` con información resumida de los POIs

### Descripción:

Este script procesa los POIs filtrados, calcula las coordenadas exactas basadas en el porcentaje desde el nodo de referencia (PERCFRREF) y el lado de la calle (R o L). También calcula las coordenadas del lado opuesto de la calle y extrae información completa sobre la calle y sus nodos.

```
Directorio de POIs [pois_features_filtrados]: pois_features_filtrados
Archivo de resultados [resultados_pois_completos.json]: resultados_pois_completos.json
Archivo de resumen [resumen_pois.json]: resumen_pois.json
```

## Paso 3: Verificar POIs con Google Places API

Finalmente, verificamos si los POIs realmente existen en las coordenadas calculadas usando la API de Google Places.

### Configuración:

Antes de ejecutar el script, crea un archivo `.env` en la raíz del proyecto con tu clave API:

```
API_GOOGLE=tu_clave_api_de_google_places
```

### Ejecutar:

```bash
python scripts/verificar_pois_google_paralelo.py
```

### Entradas:
- Archivo de POIs con coordenadas calculadas (del paso anterior)
- Clave API de Google Places (desde archivo .env)

### Salidas:
- Archivo `pois_verificados_todos.json` con todos los resultados (verificados y no verificados)
- Archivo `pois_validos.json` con solo los POIs válidos (coordenadas originales o corregidas)
- Archivo `resumen_verificacion.json` con estadísticas detalladas
- Archivo `resumen_estadisticas.json` con estadísticas básicas

### Descripción:

Este script verifica si los POIs realmente existen en las coordenadas calculadas usando la API de Google Places. Utiliza procesamiento en paralelo para acelerar significativamente la verificación. Para cada POI:

1. Busca lugares con nombre similar en un radio de 10 metros de la coordenada original
2. Si no encuentra coincidencia, busca en un radio de 10 metros de la coordenada del lado opuesto
3. Si encuentra coincidencia, incluye el POI en `pois_validos.json` (con coordenadas actualizadas si fue necesario)
4. Si no encuentra coincidencia, el POI se omite en `pois_validos.json` pero se mantiene en `pois_verificados_todos.json`

```
Archivo de POIs [resumen_pois.json]: resumen_pois.json
Archivo de resultados completos [pois_verificados_todos.json]: pois_verificados_todos.json
Archivo de resultados válidos [pois_validos.json]: pois_validos.json
Archivo de resumen [resumen_verificacion.json]: resumen_verificacion.json
Radio de búsqueda en metros [20]: 20
POIs por lote [50]: 50
Número de hilos [8]: 8
Máximo de POIs a procesar (dejar vacío para todos):
```

## Resumen de los resultados:

### Estadísticas de filtrado (Paso 1):
- Total de POIs procesados
- POIs que cumplen el filtro MULTIDIGIT sin excepciones
- POIs con ambos tipos de features (streets_nav y streets_naming)

### Estadísticas de cálculo de coordenadas (Paso 2):
- Total de POIs procesados
- POIs con coordenadas calculadas correctamente
- POIs con error en el cálculo

### Estadísticas de verificación (Paso 3):
- POIs correctos (verificados en coordenada original)
- POIs corregidos (verificados en coordenada del lado opuesto)
- POIs eliminados (no encontrados)
- Distribución por atributos de calle (MULTIDIGIT, DIR_TRAVEL, etc.)
- Distribución por similitud y distancia

---
