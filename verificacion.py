# verificar_pois_google_paralelo.py
import os
import json
import time
import requests
import math
import concurrent.futures
from tqdm import tqdm
from dotenv import load_dotenv
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import threading

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv('API_GOOGLE')  # Usar API_GOOGLE para Google Places API

# Crear un lock para escritura segura en archivos
file_lock = threading.Lock()
# Lock para estadísticas compartidas
stats_lock = threading.Lock()

# Estadísticas globales
stats = {
    "pois_correctos": 0,
    "pois_corregidos": 0,
    "pois_eliminados": 0,
    "errores_api": 0,
    "pois_procesados": 0
}

def similar(a, b):
    """Calcula la similitud entre dos cadenas de texto."""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula la distancia en metros entre dos puntos geográficos usando la fórmula Haversine."""
    # Radio de la Tierra en metros
    R = 6371000
    
    # Convertir coordenadas a radianes
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Fórmula Haversine
    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Distancia en metros
    d = R * c
    
    return d

def verificar_poi_con_google(poi_name, lon, lat, lon_opuesto=None, lat_opuesto=None, radio_metros=20, api_key=None):
    """
    Verifica si existe un lugar con nombre similar cerca de las coordenadas dadas usando Google Places API.
    """
    if not api_key:
        return {
            "verificado": False,
            "verificado_lado_opuesto": False,
            "mensaje": "No se proporcionó clave API",
            "lugares_cercanos": []
        }
    
    # URL de la API Google Places
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Parámetros para la solicitud
    params = {
        'location': f"{lat},{lon}",
        'radius': radio_metros,
        'keyword': poi_name,
        'language': 'es',
        'key': api_key
    }
    
    try:
        # Realizar la solicitud
        response = requests.get(url, params=params)
        
        # Verificar respuesta
        if response.status_code == 200:
            data = response.json()
            
            # Lista para almacenar lugares encontrados
            lugares_cercanos = []
            
            # Variables para determinar verificación
            verificado_original = False
            verificado_opuesto = False
            mensaje = "No se encontró coincidencia adecuada"
            coordenadas_reales = None
            
            # Verificar si hay resultados
            if 'results' in data and len(data['results']) > 0:
                for place in data['results']:
                    # Obtener nombre del lugar
                    nombre_google = place.get('name', '')
                    
                    # Calcular similitud del nombre
                    score_similitud = similar(poi_name, nombre_google)
                    
                    # Obtener coordenadas
                    location = place.get('geometry', {}).get('location', {})
                    google_lat = location.get('lat', 0)
                    google_lon = location.get('lng', 0)
                    
                    # Calcular distancia a la coordenada original
                    distancia_original = calcular_distancia(lat, lon, google_lat, google_lon)
                    
                    # Calcular distancia a la coordenada del lado opuesto (si se proporcionó)
                    distancia_opuesto = float('inf')
                    if lon_opuesto is not None and lat_opuesto is not None:
                        distancia_opuesto = calcular_distancia(lat_opuesto, lon_opuesto, google_lat, google_lon)
                    
                    # Determinar si está más cerca del original o del lado opuesto
                    mas_cerca_del_opuesto = distancia_opuesto < distancia_original
                    
                    # Agregar a la lista de lugares cercanos
                    lugares_cercanos.append({
                        'nombre': nombre_google,
                        'similitud': score_similitud,
                        'coordenadas': [google_lon, google_lat],
                        'distancia_metros_original': distancia_original,
                        'distancia_metros_opuesto': distancia_opuesto if lon_opuesto is not None else None,
                        'mas_cerca_del_opuesto': mas_cerca_del_opuesto,
                        'direccion': place.get('vicinity', ''),
                        'tipos': place.get('types', []),
                        'abierto_ahora': place.get('opening_hours', {}).get('open_now', None),
                        'valoracion': place.get('rating', None),
                        'place_id': place.get('place_id', '')
                    })
                
                # Ordenar por similitud (mayor a menor)
                lugares_cercanos.sort(key=lambda x: (-x['similitud'], x['distancia_metros_original']))
                
                # Criterio: al menos un lugar con similitud > 0.6 y distancia < 10m a cualquiera de las coordenadas
                for lugar in lugares_cercanos:
                    if lugar['similitud'] > 0.6:
                        if lugar['distancia_metros_original'] < 10:
                            verificado_original = True
                            mensaje = f"Verificado en coordenada original con similitud {lugar['similitud']:.2f} y distancia {lugar['distancia_metros_original']:.2f}m"
                            coordenadas_reales = lugar['coordenadas']
                            break
                        elif lon_opuesto is not None and lugar['distancia_metros_opuesto'] < 10:
                            verificado_opuesto = True
                            mensaje = f"Verificado en lado opuesto con similitud {lugar['similitud']:.2f} y distancia {lugar['distancia_metros_opuesto']:.2f}m"
                            coordenadas_reales = lugar['coordenadas']
                            break
                
                return {
                    "verificado": verificado_original,
                    "verificado_lado_opuesto": verificado_opuesto,
                    "mensaje": mensaje,
                    "lugares_cercanos": lugares_cercanos,
                    "coordenadas_reales": coordenadas_reales
                }
            else:
                return {
                    "verificado": False,
                    "verificado_lado_opuesto": False,
                    "mensaje": "No se encontraron lugares cercanos",
                    "lugares_cercanos": [],
                    "coordenadas_reales": None
                }
        else:
            return {
                "verificado": False,
                "verificado_lado_opuesto": False,
                "mensaje": f"Error en la API: {response.status_code} - {response.text}",
                "lugares_cercanos": [],
                "coordenadas_reales": None
            }
    except Exception as e:
        return {
            "verificado": False,
            "verificado_lado_opuesto": False,
            "mensaje": f"Error en la solicitud: {str(e)}",
            "lugares_cercanos": [],
            "coordenadas_reales": None
        }

def procesar_lote(lote_pois, api_key, radio_metros):
    """
    Procesa un lote de POIs en paralelo.
    
    Args:
        lote_pois: Lista de POIs a procesar
        api_key: Clave API para Google Places
        radio_metros: Radio de búsqueda en metros
        
    Returns:
        tuple: (Resultados completos, Resultados válidos)
    """
    resultados_lote = []
    resultados_validos_lote = []
    
    for poi in lote_pois:
        # Extraer información del POI
        poi_name = poi.get('poi_name', '')
        coordenadas = poi.get('coordenadas', [0, 0])
        coordenadas_lado_opuesto = poi.get('coordenadas_lado_opuesto', None)
        
        if len(coordenadas) >= 2:
            lon, lat = coordenadas[0], coordenadas[1]
            
            # Extraer coordenadas del lado opuesto si existen
            lon_opuesto, lat_opuesto = None, None
            if coordenadas_lado_opuesto and len(coordenadas_lado_opuesto) >= 2:
                lon_opuesto, lat_opuesto = coordenadas_lado_opuesto[0], coordenadas_lado_opuesto[1]
            
            # Verificar POI con la API de Google
            resultado_verificacion = verificar_poi_con_google(
                poi_name, lon, lat, lon_opuesto, lat_opuesto, radio_metros, api_key
            )
            
            # Crear entrada de resultado completo
            poi_resultado = poi.copy()  # Mantener todos los datos originales
            poi_resultado['verificacion'] = resultado_verificacion
            
            # Agregar a lista de todos los resultados
            resultados_lote.append(poi_resultado)
            
            # Actualizar estadísticas y agregar a resultados válidos si corresponde
            with stats_lock:
                stats["pois_procesados"] += 1
                
                if resultado_verificacion['verificado']:
                    # POI correcto (en coordenada original)
                    stats["pois_correctos"] += 1
                    
                    # Copiar para resultados válidos sin cambiar coordenadas
                    poi_valido = poi.copy()
                    resultados_validos_lote.append(poi_valido)
                    
                elif resultado_verificacion['verificado_lado_opuesto']:
                    # POI en el lado opuesto, hay que corregir sus coordenadas
                    stats["pois_corregidos"] += 1
                    
                    # Copiar para resultados válidos y actualizar coordenadas
                    poi_valido = poi.copy()
                    
                    # Actualizar coordenadas al valor real encontrado
                    if resultado_verificacion['coordenadas_reales']:
                        poi_valido['coordenadas_originales'] = poi_valido['coordenadas']  # Guardar original
                        poi_valido['coordenadas'] = resultado_verificacion['coordenadas_reales']  # Asignar real
                    
                    resultados_validos_lote.append(poi_valido)
                    
                else:
                    # POI no verificado, se elimina de los resultados válidos
                    if "Error en la API" in resultado_verificacion['mensaje']:
                        stats["errores_api"] += 1
                    else:
                        stats["pois_eliminados"] += 1
    
    return resultados_lote, resultados_validos_lote

def verificar_pois_en_paralelo(archivo_entrada, archivo_salida, archivo_resultados_validos, api_key, tamano_lote=100, max_pois=None, radio_metros=20, max_workers=10):
    """
    Verifica la existencia de POIs en paralelo, utilizando múltiples hilos.
    
    Args:
        archivo_entrada: Archivo JSON con los POIs a verificar
        archivo_salida: Archivo donde se guardarán todos los resultados
        archivo_resultados_validos: Archivo donde se guardarán solo los resultados válidos
        api_key: Clave de API para Google Places
        tamano_lote: Tamaño del lote para procesar
        max_pois: Máximo de POIs a procesar (None para todos)
        radio_metros: Radio de búsqueda en metros
        max_workers: Número máximo de hilos a utilizar
    """
    # Verificar que la API key esté configurada
    if not api_key:
        print("¡ERROR! No se ha configurado la clave API de Google Places.")
        print("Añade la clave API en el archivo .env con la variable API_GOOGLE")
        return
    
    # Cargar los POIs del archivo de entrada
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            pois = json.load(f)
    except Exception as e:
        print(f"Error al cargar el archivo {archivo_entrada}: {str(e)}")
        return
    
    # Limitar la cantidad de POIs si se especifica
    if max_pois is not None and max_pois > 0:
        pois = pois[:max_pois]
    
    total_pois = len(pois)
    total_lotes = (total_pois + tamano_lote - 1) // tamano_lote
    
    print(f"Procesando {total_pois} POIs en {total_lotes} lotes usando {max_workers} hilos...")
    
    # Inicializar listas para almacenar resultados
    todos_resultados = []
    todos_resultados_validos = []
    
    # Iniciar tiempo
    inicio_tiempo = time.time()
    
    # Dividir los POIs en lotes
    lotes = []
    for i in range(0, total_pois, tamano_lote):
        lote = pois[i:i+tamano_lote]
        lotes.append(lote)
    
    # Crear un ThreadPoolExecutor para procesar lotes en paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar tareas al ejecutor
        futuro_a_indice = {executor.submit(procesar_lote, lote, api_key, radio_metros): i for i, lote in enumerate(lotes)}
        
        # Procesar los resultados a medida que se completan
        for futuro in tqdm(concurrent.futures.as_completed(futuro_a_indice), total=len(lotes), desc="Procesando lotes"):
            indice_lote = futuro_a_indice[futuro]
            try:
                resultados_lote, resultados_validos_lote = futuro.result()
                
                # Actualizar resultados
                with file_lock:
                    todos_resultados.extend(resultados_lote)
                    todos_resultados_validos.extend(resultados_validos_lote)
                    
                    # Guardar resultados parciales
                    if (indice_lote + 1) % 5 == 0 or indice_lote == len(lotes) - 1:
                        # Guardar cada 5 lotes completados o en el último lote
                        with open(archivo_salida, 'w', encoding='utf-8') as f:
                            json.dump(todos_resultados, f, indent=2, ensure_ascii=False)
                        
                        with open(archivo_resultados_validos, 'w', encoding='utf-8') as f:
                            json.dump(todos_resultados_validos, f, indent=2, ensure_ascii=False)
                
                # Mostrar progreso
                tiempo_transcurrido = time.time() - inicio_tiempo
                porcentaje_completado = stats["pois_procesados"] / total_pois * 100
                
                # Estimar tiempo restante
                if stats["pois_procesados"] > 0:
                    tiempo_por_poi = tiempo_transcurrido / stats["pois_procesados"]
                    tiempo_restante = tiempo_por_poi * (total_pois - stats["pois_procesados"])
                    
                    print(f"\rProgreso: {stats['pois_procesados']}/{total_pois} POIs ({porcentaje_completado:.2f}%) | "
                          f"Tiempo: {tiempo_transcurrido/60:.2f}m | Restante: {tiempo_restante/60:.2f}m | "
                          f"Correctos: {stats['pois_correctos']} | Corregidos: {stats['pois_corregidos']} | "
                          f"Eliminados: {stats['pois_eliminados']}", end="")
            
            except Exception as e:
                print(f"\nError en lote {indice_lote}: {e}")
    
    print("\n")  # Nueva línea después de la barra de progreso
    
    # Guardar resultados finales
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(todos_resultados, f, indent=2, ensure_ascii=False)
    
    with open(archivo_resultados_validos, 'w', encoding='utf-8') as f:
        json.dump(todos_resultados_validos, f, indent=2, ensure_ascii=False)
    
    # Calcular estadísticas finales
    total_validos = stats["pois_correctos"] + stats["pois_corregidos"]
    porcentaje_validos = (total_validos / total_pois) * 100 if total_pois > 0 else 0
    tiempo_total = time.time() - inicio_tiempo
    
    # Crear resumen de estadísticas
    resumen = {
        "fecha_generacion": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_pois_procesados": total_pois,
        "pois_correctos": stats["pois_correctos"],
        "pois_corregidos": stats["pois_corregidos"],
        "pois_eliminados": stats["pois_eliminados"],
        "errores_api": stats["errores_api"],
        "total_pois_validos": total_validos,
        "porcentaje_pois_validos": porcentaje_validos,
        "tiempo_procesamiento_minutos": tiempo_total / 60
    }
    
    # Guardar resumen de estadísticas
    with open("resumen_estadisticas.json", 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    
    print("\n=== Resumen de verificación ===")
    print(f"POIs procesados: {total_pois}")
    print(f"POIs correctos (coordenada original): {stats['pois_correctos']} ({stats['pois_correctos']/total_pois*100:.2f}%)")
    print(f"POIs corregidos (coordenadas actualizadas): {stats['pois_corregidos']} ({stats['pois_corregidos']/total_pois*100:.2f}%)")
    print(f"POIs eliminados (no encontrados): {stats['pois_eliminados']} ({stats['pois_eliminados']/total_pois*100:.2f}%)")
    print(f"Total POIs válidos: {total_validos} ({porcentaje_validos:.2f}%)")
    print(f"Errores de API: {stats['errores_api']}")
    print(f"Tiempo total: {tiempo_total/60:.2f} minutos")
    print(f"Resultados completos guardados en: {archivo_salida}")
    print(f"Resultados válidos guardados en: {archivo_resultados_validos}")
    print(f"Resumen de estadísticas guardado en: resumen_estadisticas.json")

def generar_resumen_verificacion(archivo_entrada, archivo_salida):
    """
    Genera un resumen de verificación con estadísticas detalladas.
    """
    try:
        # Cargar resultados
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            resultados = json.load(f)
        
        # Estadísticas generales
        total_pois = len(resultados)
        pois_verificados_original = sum(1 for r in resultados if r.get('verificacion', {}).get('verificado', False))
        pois_verificados_opuesto = sum(1 for r in resultados if r.get('verificacion', {}).get('verificado_lado_opuesto', False))
        pois_eliminados = total_pois - pois_verificados_original - pois_verificados_opuesto
        
        # Estadísticas por similitud
        rangos_similitud = {
            "0.9-1.0": 0,
            "0.8-0.9": 0,
            "0.7-0.8": 0,
            "0.6-0.7": 0,
            "0.5-0.6": 0,
            "0.0-0.5": 0
        }
        
        # Estadísticas por distancia
        rangos_distancia = {
            "0-5m": 0,
            "5-10m": 0,
            "10-15m": 0,
            "15-20m": 0,
            ">20m": 0
        }
        
        # Estadísticas por atributos de calle
        estadisticas_calle = {
            "multidigit_yes": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "multidigit_no": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "dir_travel_b": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "dir_travel_f": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "dir_travel_t": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "ramp_y": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "ramp_n": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "manoeuvre_y": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            },
            "manoeuvre_n": {
                "correctos": 0,
                "corregidos": 0,
                "eliminados": 0
            }
        }
        
        # Estadísticas por tipo de verificación
        verificacion_por_lado = {
            "verificado_original": pois_verificados_original,
            "verificado_opuesto": pois_verificados_opuesto,
            "eliminado": pois_eliminados
        }
        
        # Contadores por tipo de establecimiento
        tipos_establecimiento = {}
        
        # Analizar cada resultado
        for resultado in resultados:
            verificacion = resultado.get('verificacion', {})
            lugares_cercanos = verificacion.get('lugares_cercanos', [])
            verificado_original = verificacion.get('verificado', False)
            verificado_opuesto = verificacion.get('verificado_lado_opuesto', False)
            
            # Determinar estado de verificación
            estado = "eliminados"
            if verificado_original:
                estado = "correctos"
            elif verificado_opuesto:
                estado = "corregidos"
            
            # Análisis de calle
            if 'calle' in resultado:
                calle = resultado['calle']
                multidigit = calle.get('multidigit', '').upper()
                dir_travel = calle.get('dir_travel', '').upper()
                ramp = calle.get('ramp', '').upper()
                manoeuvre = calle.get('manoeuvre', '').upper()
                
                # Contar atributos de calle según estado de verificación
                if multidigit == 'YES' or multidigit == 'Y':
                    estadisticas_calle["multidigit_yes"][estado] += 1
                elif multidigit == 'NO' or multidigit == 'N':
                    estadisticas_calle["multidigit_no"][estado] += 1
                
                if dir_travel == 'B':
                    estadisticas_calle["dir_travel_b"][estado] += 1
                elif dir_travel == 'F':
                    estadisticas_calle["dir_travel_f"][estado] += 1
                elif dir_travel == 'T':
                    estadisticas_calle["dir_travel_t"][estado] += 1
                
                if ramp == 'Y':
                    estadisticas_calle["ramp_y"][estado] += 1
                elif ramp == 'N':
                    estadisticas_calle["ramp_n"][estado] += 1
                
                if manoeuvre == 'Y':
                    estadisticas_calle["manoeuvre_y"][estado] += 1
                elif manoeuvre == 'N':
                    estadisticas_calle["manoeuvre_n"][estado] += 1
            
            # Análisis de lugares cercanos
            if lugares_cercanos:
                # Obtener el lugar más similar/cercano
                lugar_mas_similar = lugares_cercanos[0]
                similitud = lugar_mas_similar.get('similitud', 0)
                distancia = lugar_mas_similar.get('distancia_metros_original', float('inf'))
                
                # Actualizar estadísticas de similitud
                if similitud >= 0.9:
                    rangos_similitud["0.9-1.0"] += 1
                elif similitud >= 0.8:
                    rangos_similitud["0.8-0.9"] += 1
                elif similitud >= 0.7:
                    rangos_similitud["0.7-0.8"] += 1
                elif similitud >= 0.6:
                    rangos_similitud["0.6-0.7"] += 1
                elif similitud >= 0.5:
                    rangos_similitud["0.5-0.6"] += 1
                else:
                    rangos_similitud["0.0-0.5"] += 1
                
                # Actualizar estadísticas de distancia
                if distancia <= 5:
                    rangos_distancia["0-5m"] += 1
                elif distancia <= 10:
                    rangos_distancia["5-10m"] += 1
                elif distancia <= 15:
                    rangos_distancia["10-15m"] += 1
                elif distancia <= 20:
                    rangos_distancia["15-20m"] += 1
                else:
                    rangos_distancia[">20m"] += 1
                
                # Actualizar contador de tipos de establecimiento
                for tipo in lugar_mas_similar.get('tipos', []):
                    if tipo not in tipos_establecimiento:
                        tipos_establecimiento[tipo] = 0
                    tipos_establecimiento[tipo] += 1
        
        # Crear resumen
        resumen = {
            "fecha_generacion": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_pois": total_pois,
            "pois_correctos": pois_verificados_original,
            "pois_corregidos": pois_verificados_opuesto,
            "pois_eliminados": pois_eliminados,
            "porcentaje_pois_correctos": (pois_verificados_original / total_pois) * 100 if total_pois > 0 else 0,
            "porcentaje_pois_corregidos": (pois_verificados_opuesto / total_pois) * 100 if total_pois > 0 else 0,
            "porcentaje_pois_eliminados": (pois_eliminados / total_pois) * 100 if total_pois > 0 else 0,
            "verificacion_por_lado": verificacion_por_lado,
            "rangos_similitud": rangos_similitud,
            "rangos_distancia": rangos_distancia,
            "estadisticas_calle": estadisticas_calle,
            "tipos_establecimiento": tipos_establecimiento
        }
        
        # Guardar resumen
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)
        
        print(f"\nResumen de verificación guardado en: {archivo_salida}")
        
    except Exception as e:
        print(f"Error al generar resumen: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configuración
    archivo_entrada = input("Archivo de POIs [resumen_pois.json]: ").strip() or "resumen_pois.json"
    archivo_salida = input("Archivo de resultados completos [pois_verificados_todos.json]: ").strip() or "pois_verificados_todos.json"
    archivo_resultados_validos = input("Archivo de resultados válidos [pois_validos.json]: ").strip() or "pois_validos.json"
    archivo_resumen = input("Archivo de resumen [resumen_verificacion.json]: ").strip() or "resumen_verificacion.json"
    
    # Radio de búsqueda
    radio_metros = 20
    try:
        radio_str = input(f"Radio de búsqueda en metros [{radio_metros}]: ").strip()
        if radio_str:
            radio_metros = float(radio_str)
    except ValueError:
        print(f"Valor inválido, usando el valor predeterminado: {radio_metros}")
    
    # Tamaño del lote
    tamano_lote = 50
    try:
        lote_str = input(f"POIs por lote [{tamano_lote}]: ").strip()
        if lote_str:
            tamano_lote = int(lote_str)
    except ValueError:
        print(f"Valor inválido, usando el valor predeterminado: {tamano_lote}")
    
    # Número de hilos
    max_workers = 8
    try:
        workers_str = input(f"Número de hilos [{max_workers}]: ").strip()
        if workers_str:
            max_workers = int(workers_str)
    except ValueError:
        print(f"Valor inválido, usando el valor predeterminado: {max_workers}")
    
    # Máximo de POIs a procesar (para pruebas)
    max_pois = None
    try:
        max_str = input("Máximo de POIs a procesar (dejar vacío para todos): ").strip()
        if max_str:
            max_pois = int(max_str)
    except ValueError:
        print("Valor inválido, se procesarán todos los POIs")
    
    # Verificar POIs en paralelo
    verificar_pois_en_paralelo(
        archivo_entrada, 
        archivo_salida,
        archivo_resultados_validos,
        API_KEY, 
        tamano_lote, 
        max_pois, 
        radio_metros,
        max_workers
    )
    
    # Generar resumen
    generar_resumen_verificacion(archivo_salida, archivo_resumen)