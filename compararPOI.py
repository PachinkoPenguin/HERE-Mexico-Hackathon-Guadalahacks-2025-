# compararPOI.py
import os
import math
import time
import json

def determinar_nodo_referencia(nodos):
    """
    Determina cuál nodo es el nodo de referencia según reglas de Navstreets.
    El nodo de referencia es el que tiene menor latitud o, si son iguales, menor longitud.
    
    Args:
        nodos: Lista de nodos [lon, lat] que forman la calle
        
    Returns:
        índice del nodo de referencia
    """
    if not nodos:
        return -1
    
    idx_ref = 0
    lat_min = nodos[0][1]
    lon_min = nodos[0][0]
    
    for i, nodo in enumerate(nodos):
        lon, lat = nodo
        
        if lat < lat_min:  # Si la latitud es menor, este es el nuevo nodo de referencia
            lat_min = lat
            lon_min = lon
            idx_ref = i
        elif lat == lat_min and lon < lon_min:  # Si latitudes iguales, comparar longitudes
            lon_min = lon
            idx_ref = i
    
    return idx_ref

def calcular_posicion_poi_en_calle(nodos, percfrref, lado, distancia_estimada=0.00015):
    """
    Calcula la posición de un POI en una calle formada por múltiples nodos.
    
    Args:
        nodos: Lista de nodos [lon, lat] que forman la calle
        percfrref: Porcentaje desde el nodo de referencia (0-100)
        lado: 'R' o 'L' para indicar el lado
        distancia_estimada: Distancia perpendicular en grados
        
    Returns:
        [poi_lon, poi_lat, segment_lon, segment_lat, idx_ref, segment_idx]
    """
    if len(nodos) < 2:
        raise ValueError("Se requieren al menos 2 nodos para formar una calle")
    
    # Determinar nodo de referencia
    idx_ref = determinar_nodo_referencia(nodos)
    nodo_ref = nodos[idx_ref]
    
    print(f"Nodo de referencia: {nodo_ref} (índice {idx_ref})")
    
    # Determinar dirección de recorrido
    if idx_ref == 0:
        # Nodo de referencia es el primero, recorrido normal
        secuencia_nodos = list(range(len(nodos)))
        direccion = "normal"
    elif idx_ref == len(nodos) - 1:
        # Nodo de referencia es el último, recorrido inverso
        secuencia_nodos = list(range(len(nodos) - 1, -1, -1))
        direccion = "inverso"
    else:
        # Nodo de referencia en el medio
        if idx_ref > len(nodos) / 2:
            # Hay más nodos después que antes
            secuencia_nodos = list(range(len(nodos) - 1, -1, -1))
            direccion = "inverso"
        else:
            # Hay más nodos antes que después
            secuencia_nodos = list(range(len(nodos)))
            direccion = "normal"
    
    print(f"Dirección de recorrido: {direccion}")
    
    # Calcular longitud total de la calle en la secuencia establecida
    longitud_total = 0
    longitudes_segmentos = []
    
    for i in range(len(secuencia_nodos) - 1):
        idx1 = secuencia_nodos[i]
        idx2 = secuencia_nodos[i + 1]
        nodo1 = nodos[idx1]
        nodo2 = nodos[idx2]
        
        # Distancia euclidiana entre nodos
        dist = math.sqrt((nodo2[0] - nodo1[0])**2 + (nodo2[1] - nodo1[1])**2)
        longitud_total += dist
        longitudes_segmentos.append((dist, idx1, idx2))
    
    # Normalizar PERCFRREF a valor entre 0 y 1
    if percfrref > 1:
        percfrref_norm = percfrref / 100.0
    else:
        percfrref_norm = percfrref
    
    # Determinar en qué segmento está el POI
    distancia_actual = 0
    segmento_poi = -1
    distancia_segmento = 0
    idx_segmento_inicio = -1
    idx_segmento_fin = -1
    
    for i, (longitud, idx1, idx2) in enumerate(longitudes_segmentos):
        if distancia_actual + longitud >= percfrref_norm * longitud_total:
            segmento_poi = i
            distancia_segmento = percfrref_norm * longitud_total - distancia_actual
            idx_segmento_inicio = idx1
            idx_segmento_fin = idx2
            break
        distancia_actual += longitud
    
    # Si percfrref es 100%, estará al final del último segmento
    if segmento_poi == -1:
        segmento_poi = len(longitudes_segmentos) - 1
        distancia_segmento = longitudes_segmentos[-1][0]
        idx_segmento_inicio = longitudes_segmentos[-1][1]
        idx_segmento_fin = longitudes_segmentos[-1][2]
    
    # Obtener nodos del segmento específico
    nodo_inicio = nodos[idx_segmento_inicio]
    nodo_fin = nodos[idx_segmento_fin]
    
    # Proporción dentro del segmento específico
    proporcion_segmento = distancia_segmento / longitudes_segmentos[segmento_poi][0]
    
    # Calcular posición en el segmento
    lon_segmento = nodo_inicio[0] + proporcion_segmento * (nodo_fin[0] - nodo_inicio[0])
    lat_segmento = nodo_inicio[1] + proporcion_segmento * (nodo_fin[1] - nodo_inicio[1])
    
    # Vector direccional del segmento
    dlon = nodo_fin[0] - nodo_inicio[0]
    dlat = nodo_fin[1] - nodo_inicio[1]
    
    # Vector perpendicular según el lado (R=derecha, L=izquierda)
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
        
        # Calcular posición final del POI
        poi_lon = lon_segmento + distancia_estimada * perpendicular_lon
        poi_lat = lat_segmento + distancia_estimada * perpendicular_lat
        
        return [poi_lon, poi_lat, lon_segmento, lat_segmento, idx_ref, segmento_poi]
    else:
        return [lon_segmento, lat_segmento, lon_segmento, lat_segmento, idx_ref, segmento_poi]

def verificar_poi_desde_csv_corregido(csv_line, nodos):
    """
    Versión corregida de verificar_poi_desde_csv que extrae correctamente el campo PERCFRREF.
    
    Args:
        csv_line: Línea de datos CSV del POI
        nodos: Lista de nodos [lon, lat] que forman la calle en orden
        
    Returns:
        dict: Resultado de la verificación sin imágenes
    """
    try:
        # Parsear línea CSV
        campos = csv_line.strip().split(',')
        
        # Extraer información relevante con validación
        poi_id = campos[0] if len(campos) > 0 else "unknown"
        link_id = campos[1] if len(campos) > 1 else "unknown"
        poi_name = campos[5] if len(campos) > 5 else "unknown"
        lado = campos[13] if len(campos) > 13 else "R"  # Default a 'R' si no está definido
        
        # Obtener PERCFRREF (ahora en la posición 22, índice 0-based)
        percfrref = 0.0
        if len(campos) > 22:
            try:
                percfrref = float(campos[22])
                print(f"PERCFRREF encontrado en posición 22: {percfrref}")
            except (ValueError, TypeError):
                # Intentar posición 20 (que es donde estaba en el código original)
                if len(campos) > 20:
                    try:
                        percfrref = float(campos[20])
                        print(f"PERCFRREF encontrado en posición 20: {percfrref}")
                    except (ValueError, TypeError):
                        print(f"No se pudo parsear PERCFRREF en posición 20 o 22: {campos[20] if len(campos) > 20 else 'N/A'} / {campos[22] if len(campos) > 22 else 'N/A'}")
        
        print(f"Verificando POI: {poi_name} (ID: {poi_id})")
        print(f"Link ID: {link_id}, Lado: {lado}, PERCFRREF: {percfrref}")
        
        # Si percfrref sigue siendo 0, buscar en todo el CSV
        if percfrref == 0.0:
            for i, campo in enumerate(campos):
                try:
                    valor = float(campo)
                    if 1.0 <= valor <= 100.0:  # Rango típico para PERCFRREF
                        print(f"Posible PERCFRREF encontrado en posición {i}: {valor}")
                        percfrref = valor
                        break
                except (ValueError, TypeError):
                    continue
        
        # Calcular posición del POI
        poi_result = calcular_posicion_poi_en_calle(nodos, percfrref, lado)
        poi_lon, poi_lat, segment_lon, segment_lat, idx_ref, segment_idx = poi_result
        
        print(f"Coordenadas calculadas: [{poi_lon}, {poi_lat}]")
        print(f"Nodo de referencia: índice {idx_ref}")
        print(f"Segmento donde está el POI: índice {segment_idx}")
        
        # Crear resultado (sin imágenes)
        return {
            "poi_id": poi_id,
            "poi_name": poi_name,
            "link_id": link_id,
            "coordenadas": [poi_lon, poi_lat],
            "coordenadas_segmento": [segment_lon, segment_lat],
            "lado": lado,
            "percfrref": percfrref,
            "nodo_referencia_idx": idx_ref,
            "segmento_idx": segment_idx
        }
    
    except Exception as e:
        print(f"Error en verificación: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "poi_id": campos[0] if 'campos' in locals() and len(campos) > 0 else "unknown",
            "poi_name": campos[5] if 'campos' in locals() and len(campos) > 5 else "unknown",
            "estado": "ERROR",
            "mensaje": f"Error en procesamiento: {str(e)}",
            "error": True
        }

def verificar_poi_desde_json(poi_data):
    """
    Procesa un POI a partir de los datos extraídos de los JSON unificados.
    
    Args:
        poi_data: Diccionario con datos del POI de los JSON unificados
        
    Returns:
        dict: Resultado con las coordenadas calculadas
    """
    try:
        # Extraer datos del POI
        poi_fields = poi_data["poi"]["fields"]
        poi_id = poi_fields.get("POI_ID", "")
        link_id = poi_fields.get("LINK_ID", "")
        poi_name = poi_fields.get("POI_NAME", "")
        lado = poi_fields.get("POI_ST_SD", "R")
        
        # Buscar PERCFRREF en los campos del POI
        percfrref = 0.0
        if "PERCFRREF" in poi_fields:
            try:
                percfrref = float(poi_fields["PERCFRREF"])
            except (ValueError, TypeError):
                print(f"Error al convertir PERCFRREF: {poi_fields['PERCFRREF']}")
        
        # Si PERCFRREF es 0 o no se pudo convertir, buscar en la línea CSV
        if percfrref == 0.0:
            csv_line = poi_data["poi"]["csv_line"]
            campos = csv_line.strip().split(',')
            
            # Buscar en posición típica (22 o 20)
            if len(campos) > 22:
                try:
                    percfrref = float(campos[22])
                except (ValueError, TypeError):
                    pass
            
            if percfrref == 0.0 and len(campos) > 20:
                try:
                    percfrref = float(campos[20])
                except (ValueError, TypeError):
                    pass
            
            # Si aún no encontramos, buscar en todo el CSV valores que parecen PERCFRREF
            if percfrref == 0.0:
                for i, campo in enumerate(campos):
                    try:
                        valor = float(campo)
                        if 1.0 <= valor <= 100.0:  # Rango típico para PERCFRREF
                            print(f"Posible PERCFRREF encontrado en posición {i}: {valor}")
                            percfrref = valor
                            break
                    except (ValueError, TypeError):
                        continue
        
        print(f"Verificando POI: {poi_name} (ID: {poi_id})")
        print(f"Link ID: {link_id}, Lado: {lado}, PERCFRREF: {percfrref}")
        
        # Extraer nodos
        nodos = []
        if "streets_nav" in poi_data and "geometry" in poi_data["streets_nav"] and \
           "coordinates" in poi_data["streets_nav"]["geometry"]:
            nodos = poi_data["streets_nav"]["geometry"]["coordinates"]
        
        if not nodos or len(nodos) < 2:
            return {
                "poi_id": poi_id,
                "poi_name": poi_name,
                "link_id": link_id,
                "error": "No hay suficientes nodos para calcular la posición"
            }
        
        # Calcular posición del POI
        poi_result = calcular_posicion_poi_en_calle(nodos, percfrref, lado)
        poi_lon, poi_lat, segment_lon, segment_lat, idx_ref, segment_idx = poi_result
        
        print(f"Coordenadas calculadas: [{poi_lon}, {poi_lat}]")
        print(f"Nodo de referencia: índice {idx_ref}")
        print(f"Segmento donde está el POI: índice {segment_idx}")
        
        # Crear resultado
        return {
            "poi_id": poi_id,
            "poi_name": poi_name,
            "link_id": link_id,
            "coordenadas": [poi_lon, poi_lat],
            "coordenadas_segmento": [segment_lon, segment_lat],
            "lado": lado,
            "percfrref": percfrref,
            "nodo_referencia_idx": idx_ref,
            "segmento_idx": segment_idx,
            "total_nodos": len(nodos)
        }
    
    except Exception as e:
        print(f"Error en verificación desde JSON: {e}")
        import traceback
        traceback.print_exc()
        
        # Intentar extraer información básica para el error
        resultado_error = {
            "error": f"Error en procesamiento: {str(e)}",
        }
        
        try:
            if "poi" in poi_data and "fields" in poi_data["poi"]:
                resultado_error["poi_id"] = poi_data["poi"]["fields"].get("POI_ID", "unknown")
                resultado_error["poi_name"] = poi_data["poi"]["fields"].get("POI_NAME", "unknown")
                resultado_error["link_id"] = poi_data["poi"]["fields"].get("LINK_ID", "unknown")
        except:
            pass
            
        return resultado_error

# Ejemplo de uso para probar la función corregida con CSV
def probar_verificacion_csv():
    """Prueba la función corregida con el ejemplo de línea CSV."""
    # Línea CSV del ejemplo - PERCFRREF está en posición 22 (índice 0-based)
    csv_line = "173875,702721512,1200787905,1,7994,ALCOHÓLICOS ANÓNIMOS,SPA,B,,,,CALLE PLAN DE AYALA,SPA,R,,,0,N,N,N,0,0,21.0,0,,,,,,,,,,,,,,,,"
    
    # Lista de nodos que forman la calle (ejemplo)
    nodos_ejemplo = [ [ -99.63755, 19.27054 ], [ -99.63758, 19.27101 ] ]
    
    # Verificar POI con la función corregida
    resultado = verificar_poi_desde_csv_corregido(csv_line, nodos_ejemplo)
    
    # Mostrar resultados
    print("\n=== Resultado de verificación ===")
    print(f"POI: {resultado['poi_name']} (ID: {resultado['poi_id']})")
    if 'coordenadas' in resultado:
        print(f"Coordenadas: {resultado['coordenadas']}")
    print(f"Lado: {resultado['lado']}")
    print(f"PERCFRREF: {resultado['percfrref']}")
    print(f"Índice del nodo de referencia: {resultado['nodo_referencia_idx']}")
    print(f"Índice del segmento del POI: {resultado['segmento_idx']}")

# Ejemplo de uso para probar la función con un JSON
def probar_verificacion_json():
    """Prueba la función con datos simulados de un JSON."""
    # Ejemplo de un registro JSON como los que has generado
    poi_json = {
        "poi": {
            "csv_line": "244,1296526969,1244439551,1,4013,TOLUCA CENTRO,SPA,B,,,,AVENIDA SOLIDARIDAD LAS TORRES,SPA,R,,,0,N,N,N,0,0,10.0,0,,,,,,,,,,,,,,,,",
            "fields": {
                "LINK_ID": "1296526969",
                "POI_ID": "1244439551",
                "POI_NAME": "TOLUCA CENTRO",
                "POI_ST_SD": "R",
                "PERCFRREF": "10.0"
            }
        },
        "streets_nav": {
            "geometry": {
                "coordinates": [ [ -99.6423, 19.2704 ], [ -99.6418, 19.27052 ] ]
            }
        }
    }
    
    # Verificar POI desde JSON
    resultado = verificar_poi_desde_json(poi_json)
    
    # Mostrar resultados
    print("\n=== Resultado de verificación desde JSON ===")
    print(f"POI: {resultado['poi_name']} (ID: {resultado['poi_id']})")
    if 'coordenadas' in resultado:
        print(f"Coordenadas: {resultado['coordenadas']}")
    print(f"Lado: {resultado['lado']}")
    print(f"PERCFRREF: {resultado['percfrref']}")
    print(f"Total de nodos: {resultado['total_nodos']}")
    print(f"Índice del nodo de referencia: {resultado['nodo_referencia_idx']}")
    print(f"Índice del segmento del POI: {resultado['segmento_idx']}")

# Ejecutar pruebas
if __name__ == "__main__":
    print("=== PRUEBA CON LÍNEA CSV ===")
    probar_verificacion_csv()
    
    print("\n\n=== PRUEBA CON DATOS JSON ===")
    probar_verificacion_json()