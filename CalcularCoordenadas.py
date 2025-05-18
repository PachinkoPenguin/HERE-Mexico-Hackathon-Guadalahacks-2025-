# procesarPOIs.py
import os
import json
import time
import math
from compararPOI import verificar_poi_desde_json

def calcular_lado_opuesto(nodo_inicio, nodo_fin, punto_poi, lado):
    """
    Calcula las coordenadas del punto en el lado opuesto de la calle.
    
    Args:
        nodo_inicio: [lon, lat] del primer nodo del segmento
        nodo_fin: [lon, lat] del último nodo del segmento
        punto_poi: [lon, lat] del POI
        lado: 'R' o 'L' que indica el lado actual del POI
        
    Returns:
        [lon, lat] del punto en el lado opuesto
    """
    # Vector direccional del segmento
    dlon = nodo_fin[0] - nodo_inicio[0]
    dlat = nodo_fin[1] - nodo_inicio[1]
    
    # Vector perpendicular según el lado actual
    if lado == 'R':
        perpendicular_lon = dlat
        perpendicular_lat = -dlon
    else:  # 'L'
        perpendicular_lon = -dlat
        perpendicular_lat = dlon
    
    # Normalizar vector perpendicular
    magnitud = math.sqrt(perpendicular_lon**2 + perpendicular_lat**2)
    if magnitud > 0:
        perpendicular_lon /= magnitud
        perpendicular_lat /= magnitud
        
        # Distancia estimada (se puede ajustar según necesidades)
        distancia_estimada = 0.00030  # En grados, aproximadamente 30-40 metros
        
        # Calcular posición en el lado opuesto (dirección opuesta)
        lado_opuesto_lon = punto_poi[0] - 2 * distancia_estimada * perpendicular_lon
        lado_opuesto_lat = punto_poi[1] - 2 * distancia_estimada * perpendicular_lat
        
        return [lado_opuesto_lon, lado_opuesto_lat]
    else:
        return punto_poi  # Si no se puede calcular, devolver el mismo punto

def extraer_info_calle(poi_data):
    """
    Extrae la información relevante de la calle desde los datos del POI.
    
    Args:
        poi_data: Diccionario con los datos del POI
        
    Returns:
        dict: Información de la calle
    """
    calle_info = {}
    
    # Intentar extraer propiedades de la calle desde streets_nav
    if "streets_nav" in poi_data and "properties" in poi_data["streets_nav"]:
        props = poi_data["streets_nav"]["properties"]
        calle_info = {
            "nombre": props.get("ST_NAME", ""),
            "multidigit": props.get("MULTIDIGIT", ""),
            "dir_travel": props.get("DIR_TRAVEL", ""),
            "ramp": props.get("RAMP", ""),
            "manoeuvre": props.get("MANOEUVRE", ""),
            "func_class": props.get("FUNC_CLASS", ""),
            "speed_cat": props.get("SPEED_CAT", ""),
            "link_id": props.get("link_id", "")
        }
    
    return calle_info

def extraer_nodos_calle(poi_data):
    """
    Extrae los nodos que forman la calle desde los datos del POI.
    
    Args:
        poi_data: Diccionario con los datos del POI
        
    Returns:
        list: Lista de nodos [lon, lat] que forman la calle
    """
    nodos = []
    
    # Intentar extraer nodos desde la geometría de streets_nav
    if "streets_nav" in poi_data and "geometry" in poi_data["streets_nav"] and \
       "coordinates" in poi_data["streets_nav"]["geometry"]:
        nodos = poi_data["streets_nav"]["geometry"]["coordinates"]
    
    return nodos

def procesar_jsons_pois(directorio_entrada, archivo_salida):
    """
    Recorre todos los archivos JSON en el directorio de entrada,
    procesa cada POI y guarda los resultados en un archivo JSON.
    
    Args:
        directorio_entrada: Ruta a la carpeta que contiene los archivos JSON de POIs
        archivo_salida: Ruta donde se guardará el archivo JSON de resultados
    """
    # Verificar que el directorio exista
    if not os.path.exists(directorio_entrada):
        print(f"El directorio {directorio_entrada} no existe")
        return
    
    # Lista para almacenar todos los resultados
    resultados = []
    archivos_procesados = 0
    pois_procesados = 0
    pois_con_error = 0
    
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
                        
                        # Extraer información de la calle
                        calle_info = extraer_info_calle(poi_data)
                        
                        # Extraer nodos de la calle
                        nodos_calle = extraer_nodos_calle(poi_data)
                        
                        # Calcular coordenadas usando verificar_poi_desde_json
                        resultado = verificar_poi_desde_json(poi_data)
                        
                        # Añadir información extra al resultado
                        resultado['calle'] = calle_info
                        resultado['nodos_calle'] = nodos_calle
                        
                        # Calcular lado opuesto si tenemos suficiente información
                        if 'segmento_idx' in resultado and nodos_calle and len(nodos_calle) > resultado['segmento_idx'] + 1:
                            nodo_inicio = nodos_calle[resultado['segmento_idx']]
                            nodo_fin = nodos_calle[resultado['segmento_idx'] + 1]
                            lado = resultado.get('lado', 'R')
                            
                            # Calcular coordenadas del lado opuesto
                            lado_opuesto = calcular_lado_opuesto(nodo_inicio, nodo_fin, resultado['coordenadas'], lado)
                            resultado['coordenadas_lado_opuesto'] = lado_opuesto
                            
                            # Guardar información del segmento
                            resultado['nodo_inicio_segmento'] = nodo_inicio
                            resultado['nodo_fin_segmento'] = nodo_fin
                        
                        if 'error' in resultado:
                            pois_con_error += 1
                            print(f"Error en POI: {resultado.get('poi_name', 'desconocido')}")
                        
                        resultados.append(resultado)
                        
                        # Mostrar progreso
                        if pois_procesados % 100 == 0:
                            print(f"POIs procesados: {pois_procesados}")
                
                # Si el JSON contiene un solo elemento
                else:
                    pois_procesados += 1
                    
                    # Extraer información de la calle
                    calle_info = extraer_info_calle(datos_json)
                    
                    # Extraer nodos de la calle
                    nodos_calle = extraer_nodos_calle(datos_json)
                    
                    # Calcular coordenadas usando verificar_poi_desde_json
                    resultado = verificar_poi_desde_json(datos_json)
                    
                    # Añadir información extra al resultado
                    resultado['calle'] = calle_info
                    resultado['nodos_calle'] = nodos_calle
                    
                    # Calcular lado opuesto si tenemos suficiente información
                    if 'segmento_idx' in resultado and nodos_calle and len(nodos_calle) > resultado['segmento_idx'] + 1:
                        nodo_inicio = nodos_calle[resultado['segmento_idx']]
                        nodo_fin = nodos_calle[resultado['segmento_idx'] + 1]
                        lado = resultado.get('lado', 'R')
                        
                        # Calcular coordenadas del lado opuesto
                        lado_opuesto = calcular_lado_opuesto(nodo_inicio, nodo_fin, resultado['coordenadas'], lado)
                        resultado['coordenadas_lado_opuesto'] = lado_opuesto
                        
                        # Guardar información del segmento
                        resultado['nodo_inicio_segmento'] = nodo_inicio
                        resultado['nodo_fin_segmento'] = nodo_fin
                    
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
                    "total_nodos": poi.get("total_nodos", 0),
                    "segmento_idx": poi.get("segmento_idx", -1),
                    "nodo_referencia_idx": poi.get("nodo_referencia_idx", -1)
                }
                
                # Añadir campos adicionales si existen
                if "coordenadas_lado_opuesto" in poi:
                    resumen["coordenadas_lado_opuesto"] = poi.get("coordenadas_lado_opuesto", [])
                
                if "nodo_inicio_segmento" in poi:
                    resumen["nodo_inicio_segmento"] = poi.get("nodo_inicio_segmento", [])
                
                if "nodo_fin_segmento" in poi:
                    resumen["nodo_fin_segmento"] = poi.get("nodo_fin_segmento", [])
                
                if "calle" in poi:
                    resumen["calle"] = poi.get("calle", {})
                
                if "nodos_calle" in poi:
                    resumen["nodos_calle"] = poi.get("nodos_calle", [])
                
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
    directorio_pois = input("Directorio de POIs [pois_features_filtrados]: ").strip() or "pois_features_filtrados"
    
    # Archivos de salida
    archivo_resultados = input("Archivo de resultados [resultados_pois_completos.json]: ").strip() or "resultados_pois_completos.json"
    archivo_resumen = input("Archivo de resumen [resumen_pois.json]: ").strip() or "resumen_pois.json"
    
    # Procesar todos los POIs
    procesar_jsons_pois(directorio_pois, archivo_resultados)
    
    # Extraer información específica
    extraer_informacion_resumida(archivo_resultados, archivo_resumen)