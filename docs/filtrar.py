# unificar_pois_con_features.py
import os
import json
import glob
import math
from tqdm import tqdm
import time

def unificar_pois_con_features():
    """
    Crea múltiples JSONs con POIs que tienen líneas de streets_naming y streets_nav.
    Incluye la información completa de los features para cada POI.
    """
    # Mostrar mensaje de inicio
    print("=" * 80)
    print("UNIFICACIÓN DE POIS CON FEATURES DE CALLES")
    print("=" * 80)
    
    # Definir rutas de directorios
    directorio_pois = input("Directorio de POIs [POIs]: ").strip() or "POIs"
    directorio_streets_nav = input("Directorio de streets_nav [STREETS_NAV]: ").strip() or "STREETS_NAV"
    directorio_streets_naming = input("Directorio de streets_naming_addressing [STREETS_NAMING_ADDRESSING]: ").strip() or "STREETS_NAMING_ADDRESSING"
    
    # Directorio de salida
    directorio_salida = input("Directorio de salida [pois_features]: ").strip() or "pois_features"
    os.makedirs(directorio_salida, exist_ok=True)
    
    # Tamaño de lote (POIs por archivo)
    tamano_lote = 1000
    try:
        tamano_lote_str = input(f"POIs por archivo [{tamano_lote}]: ").strip()
        if tamano_lote_str:
            tamano_lote = int(tamano_lote_str)
    except ValueError:
        print(f"Valor inválido, usando el valor predeterminado: {tamano_lote}")
    
    # Paso 1: Cargar todos los features de streets_nav y streets_naming
    inicio = time.time()
    print("\nCargando features de streets_nav y streets_naming...")
    street_features = cargar_features(directorio_streets_nav, directorio_streets_naming)
    print(f"Se encontraron features para {len(street_features['nav']):,} link_ids en streets_nav")
    print(f"Se encontraron features para {len(street_features['naming']):,} link_ids en streets_naming")
    
    # Conjunto de link_ids que tienen ambos types de features
    link_ids_completos = set(street_features['nav'].keys()) & set(street_features['naming'].keys())
    print(f"Link_ids con ambos tipos de features: {len(link_ids_completos):,}")
    
    # Paso 2: Recorrer todos los POIs y crear entradas completas
    print("\nProcesando archivos de POIs...")
    pois_con_features, resultado_info = procesar_pois_en_lotes(
        directorio_pois, street_features, link_ids_completos, 
        directorio_salida, tamano_lote
    )
    
    # Paso 3: Guardar índice general
    guardar_indice_general(resultado_info, directorio_salida)
    
    fin = time.time()
    print(f"\nProceso completado en {(fin - inicio)/60:.2f} minutos.")
    print(f"Resultados guardados en: {directorio_salida}")
    print(f"POIs procesados: {resultado_info['total_pois']:,}")
    print(f"POIs con ambos features: {resultado_info['pois_completos']:,} ({resultado_info['pois_completos']/resultado_info['total_pois']*100:.2f}% si hay POIs)")
    print(f"Archivos JSON generados: {len(resultado_info['archivos']):,}")

def cargar_features(directorio_nav, directorio_naming):
    """
    Carga todos los features de los archivos GeoJSON de streets_nav y streets_naming.
    
    Returns:
        dict: Diccionario con features de nav y naming por link_id
    """
    street_features = {
        'nav': {},
        'naming': {}
    }
    
    # Procesar archivos de streets_nav
    archivos_nav = glob.glob(os.path.join(directorio_nav, "*.geojson"))
    print(f"Encontrados {len(archivos_nav)} archivos .geojson en {directorio_nav}")
    
    for archivo in tqdm(archivos_nav, desc="Procesando archivos streets_nav (.geojson)"):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
                if geojson.get("type") == "FeatureCollection" and "features" in geojson:
                    for feature in geojson["features"]:
                        if "properties" in feature and "link_id" in feature["properties"]:
                            link_id = str(feature["properties"]["link_id"])
                            street_features['nav'][link_id] = feature
        except Exception as e:
            print(f"Error al procesar {archivo}: {str(e)}")
    
    # También buscar archivos .json por si acaso
    archivos_nav_json = glob.glob(os.path.join(directorio_nav, "*.json"))
    if archivos_nav_json:
        print(f"Encontrados {len(archivos_nav_json)} archivos .json adicionales en {directorio_nav}")
        for archivo in tqdm(archivos_nav_json, desc="Procesando archivos .json de streets_nav"):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    geojson = json.load(f)
                    if geojson.get("type") == "FeatureCollection" and "features" in geojson:
                        for feature in geojson["features"]:
                            if "properties" in feature and "link_id" in feature["properties"]:
                                link_id = str(feature["properties"]["link_id"])
                                street_features['nav'][link_id] = feature
            except Exception as e:
                print(f"Error al procesar {archivo}: {str(e)}")
    
    # Procesar archivos de streets_naming
    archivos_naming_geojson = glob.glob(os.path.join(directorio_naming, "*.geojson"))
    archivos_naming_json = glob.glob(os.path.join(directorio_naming, "*.json"))
    
    archivos_naming = archivos_naming_geojson + archivos_naming_json
    print(f"Encontrados {len(archivos_naming)} archivos en {directorio_naming}")
    
    for archivo in tqdm(archivos_naming, desc="Procesando archivos streets_naming"):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
                if geojson.get("type") == "FeatureCollection" and "features" in geojson:
                    for feature in geojson["features"]:
                        if "properties" in feature and "link_id" in feature["properties"]:
                            link_id = str(feature["properties"]["link_id"])
                            street_features['naming'][link_id] = feature
        except Exception as e:
            print(f"Error al procesar {archivo}: {str(e)}")
    
    return street_features

def procesar_pois_en_lotes(directorio_pois, street_features, link_ids_completos, directorio_salida, tamano_lote):
    """
    Recorre todos los archivos CSV de POIs y crea entradas completas,
    guardándolas en múltiples archivos JSON.
    
    Args:
        directorio_pois: Directorio con archivos CSV de POIs
        street_features: Diccionario con los features de calles
        link_ids_completos: Conjunto de link_ids que tienen ambos tipos de features
        directorio_salida: Directorio donde guardar los archivos JSON
        tamano_lote: Número de POIs por archivo JSON
        
    Returns:
        tuple: (último lote de POIs, información de resultado)
    """
    lote_actual = []
    numero_lote = 1
    total_pois = 0
    pois_validos = 0
    pois_faltantes_nav = 0
    pois_faltantes_naming = 0
    pois_completos = 0
    
    resultado_info = {
        'total_pois': 0,
        'pois_completos': 0,
        'pois_faltantes_nav': 0,
        'pois_faltantes_naming': 0,
        'archivos': []
    }
    
    # Buscar archivos CSV
    archivos_csv = glob.glob(os.path.join(directorio_pois, "*.csv"))
    
    # Crear un índice para buscar POIs por link_id
    indice_por_link = {}
    
    # Contador de POIs guardados en archivos
    pois_guardados = 0
    
    # Procesar cada archivo
    for archivo in tqdm(archivos_csv, desc="Procesando archivos POI"):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                # Leer la primera línea como encabezados
                encabezados = f.readline().strip().split(',')
                
                # Determinar índice de LINK_ID
                link_id_idx = 1  # Por defecto, asumimos que está en la posición 1
                for i, encabezado in enumerate(encabezados):
                    if encabezado.strip() in ["LINK_ID", "link_id"]:
                        link_id_idx = i
                        break
                
                # Procesar cada línea
                for linea in f:
                    total_pois += 1
                    campos = linea.strip().split(',')
                    
                    # Validación básica
                    if len(campos) <= link_id_idx:
                        continue
                    
                    # Obtener link_id
                    link_id = campos[link_id_idx].strip()
                    
                    # POI ID para referencias
                    poi_id = campos[0].strip() if len(campos) > 0 else f"unknown_{total_pois}"
                    
                    # Verificar si el link_id tiene los features completos
                    if link_id in link_ids_completos:
                        # Crear un diccionario completo para este POI
                        poi_entry = {
                            "poi": {
                                "csv_line": linea.strip()
                            },
                            "streets_nav": street_features['nav'][link_id],
                            "streets_naming": street_features['naming'][link_id]
                        }
                        
                        # También incluir los campos como diccionario para facilitar acceso
                        poi_data = {}
                        for i, valor in enumerate(campos):
                            if i < len(encabezados):
                                nombre_campo = encabezados[i].strip()
                                if nombre_campo:  # Solo si el nombre no está vacío
                                    poi_data[nombre_campo] = valor
                        
                        poi_entry["poi"]["fields"] = poi_data
                        
                        # Agregar al lote actual
                        lote_actual.append(poi_entry)
                        pois_validos += 1
                        pois_completos += 1
                        
                        # Registrar en el índice
                        if link_id not in indice_por_link:
                            indice_por_link[link_id] = []
                        indice_por_link[link_id].append({
                            "poi_id": poi_id,
                            "archivo": f"pois_lote_{numero_lote}.json",
                            "indice": len(lote_actual) - 1  # Posición en el lote
                        })
                        
                        # Verificar si el lote está completo
                        if len(lote_actual) >= tamano_lote:
                            # Guardar lote
                            ruta_archivo = os.path.join(directorio_salida, f"pois_lote_{numero_lote}.json")
                            with open(ruta_archivo, 'w', encoding='utf-8') as f_out:
                                json.dump(lote_actual, f_out, ensure_ascii=False, indent=2)
                            
                            # Registrar en información de resultado
                            resultado_info['archivos'].append({
                                "nombre": f"pois_lote_{numero_lote}.json",
                                "cantidad": len(lote_actual),
                                "rango_pois": pois_guardados + 1
                            })
                            
                            pois_guardados += len(lote_actual)
                            print(f"Guardado lote {numero_lote} con {len(lote_actual):,} POIs en {ruta_archivo}")
                            
                            # Reiniciar lote
                            lote_actual = []
                            numero_lote += 1
                    else:
                        # Verificar qué features faltan
                        if link_id in street_features['nav']:
                            pois_faltantes_naming += 1
                        elif link_id in street_features['naming']:
                            pois_faltantes_nav += 1
        
        except Exception as e:
            print(f"Error al procesar {archivo}: {str(e)}")
    
    # Guardar el último lote si tiene datos
    if lote_actual:
        ruta_archivo = os.path.join(directorio_salida, f"pois_lote_{numero_lote}.json")
        with open(ruta_archivo, 'w', encoding='utf-8') as f_out:
            json.dump(lote_actual, f_out, ensure_ascii=False, indent=2)
        
        # Registrar en información de resultado
        resultado_info['archivos'].append({
            "nombre": f"pois_lote_{numero_lote}.json",
            "cantidad": len(lote_actual),
            "rango_pois": pois_guardados + 1
        })
        
        print(f"Guardado lote final {numero_lote} con {len(lote_actual):,} POIs en {ruta_archivo}")
    
    # Guardar índice por link_id
    ruta_indice_link = os.path.join(directorio_salida, "indice_por_link.json")
    with open(ruta_indice_link, 'w', encoding='utf-8') as f:
        json.dump(indice_por_link, f, ensure_ascii=False, indent=2)
    print(f"Guardado índice por link_id en {ruta_indice_link}")
    
    # Actualizar información de resultado
    resultado_info['total_pois'] = total_pois
    resultado_info['pois_completos'] = pois_completos
    resultado_info['pois_faltantes_nav'] = pois_faltantes_nav
    resultado_info['pois_faltantes_naming'] = pois_faltantes_naming
    
    print(f"\nTotal POIs procesados: {total_pois:,}")
    print(f"POIs con ambos features: {pois_completos:,} ({pois_completos/total_pois*100:.2f}% si total_pois > 0)")
    print(f"POIs con link_id en streets_nav pero no en streets_naming: {pois_faltantes_naming:,}")
    print(f"POIs con link_id en streets_naming pero no en streets_nav: {pois_faltantes_nav:,}")
    
    return lote_actual, resultado_info

def guardar_indice_general(resultado_info, directorio_salida):
    """
    Guarda un índice general con información sobre los archivos generados.
    
    Args:
        resultado_info: Diccionario con información de los resultados
        directorio_salida: Directorio donde guardar el índice
    """
    # Crear un índice general
    indice_general = {
        "fecha_generacion": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_pois_procesados": resultado_info['total_pois'],
        "pois_con_features_completos": resultado_info['pois_completos'],
        "total_archivos": len(resultado_info['archivos']),
        "archivos": resultado_info['archivos']
    }
    
    # Guardar índice general
    ruta_indice = os.path.join(directorio_salida, "indice_general.json")
    with open(ruta_indice, 'w', encoding='utf-8') as f:
        json.dump(indice_general, f, ensure_ascii=False, indent=2)
    
    print(f"Guardado índice general en {ruta_indice}")

# Ejecutar el proceso
if __name__ == "__main__":
    try:
        unificar_pois_con_features()
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario.")
    except Exception as e:
        import traceback
        print("\n¡ERROR EN LA EJECUCIÓN!")
        print(f"Error: {str(e)}")
        traceback.print_exc()