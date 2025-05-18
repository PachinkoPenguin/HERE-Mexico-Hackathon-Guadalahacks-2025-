# probar_tapatio_google.py
import requests
import json
import math
import os
from dotenv import load_dotenv

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en metros entre dos puntos usando la fórmula de Haversine."""
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

def buscar_con_google_places(lat, lon, nombre, radio_metros=200, api_key=None):
    """
    Busca establecimientos cercanos usando Google Places API.
    
    Args:
        lat: Latitud
        lon: Longitud
        nombre: Nombre del establecimiento a buscar
        radio_metros: Radio de búsqueda en metros
        api_key: Clave API de Google Maps
        
    Returns:
        list: Lista de establecimientos encontrados
    """
    if not api_key:
        print("Se requiere una clave API de Google Maps para usar esta función.")
        return []
    
    # URL de la API Google Places
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Parámetros de búsqueda
    params = {
        'location': f"{lat},{lon}",
        'radius': radio_metros,
        'keyword': nombre,
        'language': 'es',
        'key': api_key
    }
    
    try:
        # Realizar la solicitud
        response = requests.get(url, params=params)
        
        # Verificar respuesta
        if response.status_code == 200:
            data = response.json()
            
            # Lista para almacenar establecimientos encontrados
            establecimientos = []
            
            # Verificar si hay resultados
            if 'results' in data and len(data['results']) > 0:
                for place in data['results']:
                    elemento_nombre = place.get('name', 'Sin nombre')
                    
                    # Obtener coordenadas
                    location = place.get('geometry', {}).get('location', {})
                    elemento_lat = location.get('lat', 0)
                    elemento_lon = location.get('lng', 0)
                    
                    # Calcular distancia
                    distancia = calcular_distancia_haversine(lat, lon, elemento_lat, elemento_lon)
                    
                    # Obtener tipos
                    tipos = place.get('types', [])
                    
                    # Obtener dirección
                    direccion = place.get('vicinity', '')
                    
                    # Estado de apertura
                    abierto_ahora = 'Desconocido'
                    if 'opening_hours' in place and 'open_now' in place['opening_hours']:
                        abierto_ahora = 'Abierto' if place['opening_hours']['open_now'] else 'Cerrado'
                    
                    # Agregar a establecimientos encontrados
                    establecimientos.append({
                        'nombre': elemento_nombre,
                        'coordenadas': [elemento_lon, elemento_lat],
                        'distancia_metros': distancia,
                        'tipos': tipos,
                        'direccion': direccion,
                        'abierto_ahora': abierto_ahora,
                        'valoracion': place.get('rating', 'Sin valoración'),
                        'place_id': place.get('place_id', '')
                    })
                
                # Ordenar por distancia
                establecimientos.sort(key=lambda x: x['distancia_metros'])
                
                return establecimientos, data
            else:
                return [], data
        else:
            print(f"Error en la API Google Places: {response.status_code}")
            print(response.text)
            return [], None
    except Exception as e:
        print(f"Error en la solicitud a Google Places: {str(e)}")
        return [], None

def main():
    # Coordenadas de "El Tapatio"
    lat = 19.45575116638701
    lon = -99.19554761565927
    nombre = "El Tapatio"
    radio = 200  # metros
    
    # Solicitar clave API
    api_key = 
    
    if not api_key:
        print("Se requiere una clave API para continuar.")
        return
    
    print(f"\nBuscando '{nombre}' en las coordenadas [{lat}, {lon}] con un radio de {radio}m...")
    
    # Realizar búsqueda
    establecimientos, data_completa = buscar_con_google_places(lat, lon, nombre, radio, api_key)
    
    # Mostrar resultados
    if establecimientos:
        print(f"\nSe encontraron {len(establecimientos)} establecimientos cercanos:")
        
        for i, lugar in enumerate(establecimientos):
            print(f"\n{i+1}. {lugar['nombre']}")
            print(f"   Distancia: {lugar['distancia_metros']:.2f} metros")
            print(f"   Coordenadas: [{lugar['coordenadas'][1]}, {lugar['coordenadas'][0]}]")
            print(f"   Dirección: {lugar['direccion']}")
            print(f"   Tipos: {', '.join(lugar['tipos'])}")
            print(f"   Estado: {lugar['abierto_ahora']}")
            print(f"   Valoración: {lugar['valoracion']}")
            print(f"   ID: {lugar['place_id']}")
        
        # Guardar resultados en JSON
        with open(f"resultados_{nombre.replace(' ', '_')}.json", 'w', encoding='utf-8') as f:
            json.dump({
                'consulta': {
                    'nombre': nombre,
                    'coordenadas': [lon, lat],
                    'radio': radio
                },
                'establecimientos': establecimientos,
                'data_completa': data_completa
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nResultados guardados en 'resultados_{nombre.replace(' ', '_')}.json'")
    else:
        print("\nNo se encontraron establecimientos que coincidan.")
        
        if data_completa:
            print("\nRespuesta completa de la API:")
            print(json.dumps(data_completa, indent=2, ensure_ascii=False))
        
        # Sugerencias si no se encuentran resultados
        print("\nSugerencias:")
        print("1. Intenta con un radio mayor")
        print("2. Verifica el nombre del establecimiento")
        print("3. Prueba con variaciones del nombre (por ejemplo: 'Tapatio', 'Tapatío', 'Restaurant Tapatio')")
        print("4. Verifica que las coordenadas sean correctas")

if __name__ == "__main__":
    main()