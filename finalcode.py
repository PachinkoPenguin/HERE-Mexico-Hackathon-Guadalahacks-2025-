# procesarPOIs.py
import os
import json
import time
import requests
import math
from dotenv import load_dotenv
from compararPOI import verificar_poi_desde_json

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv('API_KEY')

def lat_lon_to_tile(lat, lon, zoom):
    """
    Convierte latitud y longitud a índices de mosaico (x, y) en un nivel de zoom determinado.
    
    :param lat: Latitud en grados
    :param lon: Longitud en grados
    :param zoom: Nivel de zoom (0-19)
    :return: Tupla (x, y) que representa los índices del mosaico
    """
    # Convertir latitud y longitud a radianes
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n)
    return (x, y)

def tile_coords_to_lat_lon(x, y, zoom):
    """
    Convierte las coordenadas de un mosaico a latitud y longitud.
    
    :param x: Índice x del mosaico
    :param y: Índice y del mosaico
    :param zoom: Nivel de zoom
    :return: Tupla (latitud, longitud) en grados
    """
    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1-2 * y/n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def get_tile_bounds(x, y, zoom):
    """
    Obtiene los límites (esquinas) de un mosaico.
    
    :param x: Índice x del mosaico
    :param y: Índice y del mosaico
    :param zoom: Nivel de zoom
    :return: Tupla de 4 puntos (lat, lon) que representan las esquinas del mosaico
    """
    lat1, lon1 = tile_coords_to_lat_lon(x, y, zoom)
    lat2, lon2 = tile_coords_to_lat_lon(x+1, y, zoom)
    lat3, lon3 = tile_coords_to_lat_lon(x+1, y+1, zoom)
    lat4, lon4 = tile_coords_to_lat_lon(x, y+1, zoom)
    return (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)

def create_wkt_polygon(bounds):
    """
    Crea un polígono WKT a partir de los límites del mosaico.
    
    :param bounds: Límites del mosaico (4 esquinas)
    :return: Cadena de texto con el polígono WKT
    """
    (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4) = bounds
    wkt = f"POLYGON(({lon1} {lat1}, {lon2} {lat2}, {lon3} {lat3}, {lon4} {lat4}, {lon1} {lat1}))"
    return wkt

def get_satellite_tile(lat, lon, zoom, tile_format, api_key, output_dir, poi_id, poi_name):
    """
    Descarga una imagen satelital para las coordenadas dadas y la guarda en el directorio de salida.
    
    :param lat: Latitud del POI
    :param lon: Longitud del POI
    :param zoom: Nivel de zoom
    :param tile_format: Formato de la imagen (png, jpg)
    :param api_key: Clave API para HERE Maps
    :param output_dir: Directorio donde se guardarán las imágenes
    :param poi_id: ID del POI para nombrar el archivo
    :param poi_name: Nombre del POI para nombrar el archivo
    :return: Polígono WKT con los límites del mosaico y la ruta de la imagen
    """
    x, y = lat_lon_to_tile(lat, lon, zoom)
    
    # Tamaño del mosaico (definido como constante)
    tile_size = 512
    
    # Construir la URL para la API de mosaicos de mapa
    url = f'https://maps.hereapi.com/v3/base/mc/{zoom}/{x}/{y}/{tile_format}?style=satellite.day&size={tile_size}&apiKey={api_key}'
    
    # Crear un nombre de archivo seguro
    safe_poi_name = "".join(c for c in poi_name if c.isalnum() or c in [' ', '_']).strip().replace(' ', '_')
    filename = f"{poi_id}_{safe_poi_name}.{tile_format}"
    filepath = os.path.join(output_dir, filename)
    
    # Realizar la solicitud
    try:
        response = requests.get(url)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Guardar el mosaico en un archivo
            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f'Imagen satelital guardada: {filename}')
        else:
            print(f'Error al obtener imagen satelital. Código de estado: {response.status_code}')
            filepath = None
    except Exception as e:
        print(f'Error al descargar imagen satelital: {e}')
        filepath = None
    
    # Obtener los límites del mosaico
    bounds = get_tile_bounds(x, y, zoom)
    wkt_polygon = create_wkt_polygon(bounds)
    
    return wkt_polygon, filepath

def procesar_jsons_pois(directorio_entrada, archivo_salida, directorio_imagenes, zoom_level=16, tile_format='png'):
    """
    Recorre todos los archivos JSON en el directorio de entrada,
    procesa cada POI, guarda los resultados en un archivo JSON y descarga las imágenes satelitales.
    
    Args:
        directorio_entrada: Ruta a la carpeta que contiene los archivos JSON de POIs
        archivo_salida: Ruta donde se guardará el archivo JSON de resultados
        directorio_imagenes: Ruta donde se guardarán las imágenes satelitales
        zoom_level: Nivel de zoom para las imágenes satelitales (0-19)
        tile_format: Formato de las imágenes satelitales (png, jpg)
    """
    # Verificar que el directorio exista
    if not os.path.exists(directorio_entrada):
        print(f"El directorio {directorio_entrada} no existe")
        return
    
    # Crear el directorio de imágenes si no existe
    if not os.path.exists(directorio_imagenes):
        os.makedirs(directorio_imagenes)
        print(f"Directorio creado: {directorio_imagenes}")
    
    # Verificar si existe la clave API
    if not API_KEY:
        print("¡ADVERTENCIA! La clave API no está configurada. No se descargarán imágenes satelitales.")
        descargar_imagenes = False
    else:
        descargar_imagenes = True
    
    # Lista para almacenar todos los resultados
    resultados = []
    archivos_procesados = 0
    pois_procesados = 0
    pois_con_error = 0
    imagenes_descargadas = 0
    
    inicio_tiempo = time.time()
    
    # Recorrer todos los archivos en el directorio
    for nombre_archivo in os.listdir(directorio_entrada):
        if nombre_archivo.endswith('.json'):
            ruta_completa = os.path.join(directorio_entrada, nombre_archivo)
            
            print(f"Procesando archivo: {nombre_archivo}")
            
            try:
                # Cargar el archivo JSON
                with open(ruta_completa, 'r', encoding='utf-8') as f:
                    datos_json = json.load(f)
                
                # Si el JSON contiene una lista de elementos
                if isinstance(datos_json, list):
                    for poi_data in datos_json:
                        pois_procesados += 1
                        resultado = verificar_poi_desde_json(poi_data)
                        
                        # Descargar imagen satelital si no hay error
                        if 'error' not in resultado and descargar_imagenes:
                            try:
                                poi_lat = resultado['coordenadas'][1]  # Latitud es el segundo elemento
                                poi_lon = resultado['coordenadas'][0]  # Longitud es el primer elemento
                                poi_id = resultado['poi_id']
                                poi_name = resultado['poi_name']
                                
                                # Descargar imagen satelital
                                wkt_polygon, imagen_path = get_satellite_tile(
                                    poi_lat, poi_lon, zoom_level, tile_format, 
                                    API_KEY, directorio_imagenes, poi_id, poi_name
                                )
                                
                                # Agregar información de la imagen al resultado
                                if imagen_path:
                                    resultado['imagen_satelital'] = os.path.basename(imagen_path)
                                    resultado['wkt_bounds'] = wkt_polygon
                                    imagenes_descargadas += 1
                            except Exception as e:
                                print(f"Error al descargar imagen para {resultado.get('poi_name', 'desconocido')}: {e}")
                        
                        if 'error' in resultado:
                            pois_con_error += 1
                            print(f"Error en POI: {resultado.get('poi_name', 'desconocido')}")
                        
                        resultados.append(resultado)
                        
                        # Mostrar progreso
                        if pois_procesados % 10 == 0:
                            print(f"POIs procesados: {pois_procesados}, Imágenes descargadas: {imagenes_descargadas}")
                
                # Si el JSON contiene un solo elemento
                else:
                    pois_procesados += 1
                    resultado = verificar_poi_desde_json(datos_json)
                    
                    # Descargar imagen satelital si no hay error
                    if 'error' not in resultado and descargar_imagenes:
                        try:
                            poi_lat = resultado['coordenadas'][1]  # Latitud es el segundo elemento
                            poi_lon = resultado['coordenadas'][0]  # Longitud es el primer elemento
                            poi_id = resultado['poi_id']
                            poi_name = resultado['poi_name']
                            
                            # Descargar imagen satelital
                            wkt_polygon, imagen_path = get_satellite_tile(
                                poi_lat, poi_lon, zoom_level, tile_format, 
                                API_KEY, directorio_imagenes, poi_id, poi_name
                            )
                            
                            # Agregar información de la imagen al resultado
                            if imagen_path:
                                resultado['imagen_satelital'] = os.path.basename(imagen_path)
                                resultado['wkt_bounds'] = wkt_polygon
                                imagenes_descargadas += 1
                        except Exception as e:
                            print(f"Error al descargar imagen para {resultado.get('poi_name', 'desconocido')}: {e}")
                    
                    if 'error' in resultado:
                        pois_con_error += 1
                        print(f"Error en POI: {resultado.get('poi_name', 'desconocido')}")
                    
                    resultados.append(resultado)
                
                archivos_procesados += 1
                
            except Exception as e:
                print(f"Error al procesar el archivo {nombre_archivo}: {e}")
    
    # Calcular tiempo total
    tiempo_total = time.time() - inicio_tiempo
    
    # Guardar todos los resultados en un archivo JSON
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    print("\n=== Resumen de procesamiento ===")
    print(f"Archivos procesados: {archivos_procesados}")
    print(f"POIs procesados: {pois_procesados}")
    print(f"POIs con error: {pois_con_error}")
    print(f"Imágenes satelitales descargadas: {imagenes_descargadas}")
    print(f"Tiempo total: {tiempo_total:.2f} segundos")
    print(f"Resultados guardados en: {archivo_salida}")

# Función para extraer información específica solicitada
def extraer_informacion_resumida(archivo_entrada, archivo_salida):
    """
    Extrae solo la información solicitada de cada POI y guarda en un nuevo archivo.
    
    Args:
        archivo_entrada: Archivo JSON con todos los resultados
        archivo_salida: Archivo donde se guardará la información específica
    """
    try:
        # Cargar resultados completos
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            resultados = json.load(f)
        
        # Lista para almacenar sólo la información solicitada
        info_resumida = []
        
        for poi in resultados:
            if 'error' not in poi:
                # Extraer solo los campos solicitados
                resumen = {
                    "poi_name": poi.get("poi_name", ""),
                    "poi_id": poi.get("poi_id", ""),
                    "link_id": poi.get("link_id", ""),
                    "coordenadas": poi.get("coordenadas", []),
                    "lado": poi.get("lado", ""),
                    "percfrref": poi.get("percfrref", 0),
                    "total_nodos": poi.get("total_nodos", 0)
                }
                
                # Incluir información de la imagen si existe
                if "imagen_satelital" in poi:
                    resumen["imagen_satelital"] = poi.get("imagen_satelital", "")
                    resumen["wkt_bounds"] = poi.get("wkt_bounds", "")
                
                info_resumida.append(resumen)
        
        # Guardar información resumida
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(info_resumida, f, indent=2, ensure_ascii=False)
        
        print(f"\nInformación resumida guardada en: {archivo_salida}")
        print(f"Total de POIs en resumen: {len(info_resumida)}")
        
    except Exception as e:
        print(f"Error al extraer información resumida: {e}")

if __name__ == "__main__":
    # Directorio que contiene los archivos JSON de POIs
    directorio_pois = "pois_features"
    
    # Archivos de salida
    archivo_resultados = "resultados_pois_completos.json"
    archivo_resumen = "resumen_pois.json"
    
    # Directorio para guardar las imágenes satelitales
    directorio_imagenes = "imagenes_satelitales"
    
    # Parámetros para las imágenes satelitales
    zoom_level = 16  # Nivel de zoom
    tile_format = 'png'  # Formato de la imagen
    
    # Procesar todos los POIs y descargar imágenes
    procesar_jsons_pois(directorio_pois, archivo_resultados, directorio_imagenes, zoom_level, tile_format)
    
    # Extraer información específica
    extraer_informacion_resumida(archivo_resultados, archivo_resumen)