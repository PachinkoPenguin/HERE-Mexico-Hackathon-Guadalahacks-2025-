import matplotlib.pyplot as plt
import numpy as np

def visualizar_comparacion_simple(nodo_inicio, nodo_fin, percfrref, lado, coord_real, poi_name):
    """
    Compara el cálculo normal y con nodos invertidos, ambos usando el lado derecho correcto.
    """
    # Crear figura con dos subgráficos
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Configuración compartida
    for ax in [ax1, ax2]:
        ax.grid(True, linestyle='--', alpha=0.7)
    
    #----- GRÁFICO 1: Cálculo Normal -----
    ax1.set_title("Cálculo Normal", fontsize=12)
    
    # Determinar nodo de referencia según regla (latitud menor)
    if nodo_inicio[1] < nodo_fin[1]:
        nodo_ref = nodo_inicio
        nodo_no_ref = nodo_fin
        es_inicio_ref = True
    else:
        nodo_ref = nodo_fin
        nodo_no_ref = nodo_inicio
        es_inicio_ref = False
    
    # Calcular punto en el segmento según PERCFRREF
    percfrref_norm = percfrref / 100.0
    lon_segmento = nodo_ref[0] + percfrref_norm * (nodo_no_ref[0] - nodo_ref[0])
    lat_segmento = nodo_ref[1] + percfrref_norm * (nodo_no_ref[1] - nodo_ref[1])
    
    # Vector direccional del segmento
    dlon = nodo_no_ref[0] - nodo_ref[0]
    dlat = nodo_no_ref[1] - nodo_ref[1]
    
    # Vector perpendicular para lado derecho
    # Rotación 90° sentido horario: (x, y) -> (y, -x)
    perp_derecha_lon = dlat
    perp_derecha_lat = -dlon
    
    # Normalizar
    magnitud = np.sqrt(perp_derecha_lon**2 + perp_derecha_lat**2)
    if magnitud > 0:
        perp_derecha_lon /= magnitud
        perp_derecha_lat /= magnitud
    
    # Distancia estimada
    distancia_estimada = 0.00015
    
    # Calcular POI en lado derecho
    poi_lon = lon_segmento + distancia_estimada * perp_derecha_lon
    poi_lat = lat_segmento + distancia_estimada * perp_derecha_lat
    
    # Graficar en primer subgráfico
    ax1.plot([nodo_inicio[0], nodo_fin[0]], [nodo_inicio[1], nodo_fin[1]], 'b-', linewidth=2, label='Segmento')
    ax1.plot(nodo_ref[0], nodo_ref[1], 'ro', markersize=8, label='Nodo Ref.')
    ax1.plot(nodo_no_ref[0], nodo_no_ref[1], 'go', markersize=8, label='Nodo No Ref.')
    ax1.plot(lon_segmento, lat_segmento, 'yo', markersize=6, label=f'{percfrref}%')
    ax1.plot(poi_lon, poi_lat, 'mo', markersize=8, label='POI (Lado R)')
    ax1.plot(coord_real[0], coord_real[1], 'co', markersize=8, label='POI real')
    ax1.plot([lon_segmento, poi_lon], [lat_segmento, poi_lat], 'k--', linewidth=1)
    
    # Calcular distancia al POI real
    dist_normal = np.sqrt((poi_lon - coord_real[0])**2 + (poi_lat - coord_real[1])**2) * 111000  # metros
    
    #----- GRÁFICO 2: Cálculo con Nodos Invertidos -----
    ax2.set_title("Cálculo con Nodos Invertidos", fontsize=12)
    
    # Invertir los nodos
    inv_nodo_ref = nodo_no_ref
    inv_nodo_no_ref = nodo_ref
    
    # Calcular punto en el segmento con nodos invertidos
    inv_lon_segmento = inv_nodo_ref[0] + percfrref_norm * (inv_nodo_no_ref[0] - inv_nodo_ref[0])
    inv_lat_segmento = inv_nodo_ref[1] + percfrref_norm * (inv_nodo_no_ref[1] - inv_nodo_ref[1])
    
    # Vector direccional con nodos invertidos
    inv_dlon = inv_nodo_no_ref[0] - inv_nodo_ref[0]
    inv_dlat = inv_nodo_no_ref[1] - inv_nodo_ref[1]
    
    # Vector perpendicular derecho con nodos invertidos
    inv_perp_lon = inv_dlat
    inv_perp_lat = -inv_dlon
    
    # Normalizar
    inv_magnitud = np.sqrt(inv_perp_lon**2 + inv_perp_lat**2)
    if inv_magnitud > 0:
        inv_perp_lon /= inv_magnitud
        inv_perp_lat /= inv_magnitud
    
    # Calcular POI con nodos invertidos
    inv_poi_lon = inv_lon_segmento + distancia_estimada * inv_perp_lon
    inv_poi_lat = inv_lat_segmento + distancia_estimada * inv_perp_lat
    
    # Graficar en segundo subgráfico
    ax2.plot([nodo_inicio[0], nodo_fin[0]], [nodo_inicio[1], nodo_fin[1]], 'b-', linewidth=2, label='Segmento')
    ax2.plot(inv_nodo_ref[0], inv_nodo_ref[1], 'ro', markersize=8, label='Nodo Ref. (Inv)')
    ax2.plot(inv_nodo_no_ref[0], inv_nodo_no_ref[1], 'go', markersize=8, label='Nodo No Ref. (Inv)')
    ax2.plot(inv_lon_segmento, inv_lat_segmento, 'yo', markersize=6, label=f'{percfrref}%')
    ax2.plot(inv_poi_lon, inv_poi_lat, 'mo', markersize=8, label='POI (Lado R)')
    ax2.plot(coord_real[0], coord_real[1], 'co', markersize=8, label='POI real')
    ax2.plot([inv_lon_segmento, inv_poi_lon], [inv_lat_segmento, inv_poi_lat], 'k--', linewidth=1)
    
    # Calcular distancia con nodos invertidos
    dist_invertido = np.sqrt((inv_poi_lon - coord_real[0])**2 + (inv_poi_lat - coord_real[1])**2) * 111000  # metros
    
    # Ajustar límites para ambos gráficos
    all_lons = [nodo_inicio[0], nodo_fin[0], poi_lon, inv_poi_lon, coord_real[0]]
    all_lats = [nodo_inicio[1], nodo_fin[1], poi_lat, inv_poi_lat, coord_real[1]]
    
    x_min = min(all_lons) - 0.0002
    x_max = max(all_lons) + 0.0002
    y_min = min(all_lats) - 0.0002
    y_max = max(all_lats) + 0.0002
    
    for ax in [ax1, ax2]:
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel('Longitud', fontsize=10)
        ax.set_ylabel('Latitud', fontsize=10)
        ax.legend(loc='best', fontsize=8)
    
    # Añadir información sobre distancias
    fig.suptitle(f"Comparación para {poi_name} (Lado Derecho en ambos casos)", fontsize=14)
    
    info_text = (
        f"Distancia al POI real: Normal = {dist_normal:.2f}m, Invertido = {dist_invertido:.2f}m\n"
        f"El cálculo {'invertido' if dist_invertido < dist_normal else 'normal'} está más cerca del POI real."
    )
    fig.text(0.5, 0.01, info_text, ha='center', fontsize=12)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.15)
    plt.savefig(f"{poi_name.replace(' ', '_')}_comparacion_lado_derecho.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    # Imprimir resultados
    print("=== Cálculo Normal ===")
    print(f"Nodo de referencia: {nodo_ref}")
    print(f"POI calculado (Lado R): [{poi_lon}, {poi_lat}]")
    print(f"Distancia al POI real: {dist_normal:.2f} metros")
    
    print("\n=== Cálculo con Nodos Invertidos ===")
    print(f"Nodo de referencia (invertido): {inv_nodo_ref}")
    print(f"POI calculado (Lado R): [{inv_poi_lon}, {inv_poi_lat}]")
    print(f"Distancia al POI real: {dist_invertido:.2f} metros")
    
    return {
        "normal": {
            "poi_coords": [poi_lon, poi_lat],
            "distancia_m": dist_normal
        },
        "invertido": {
            "poi_coords": [inv_poi_lon, inv_poi_lat],
            "distancia_m": dist_invertido
        }
    }

# Usar el código con tus datos
nodo_inicio = [  -99.63755, 19.27054  ]  # [longitud, latitud]
nodo_fin = [  -99.63758, 19.27101  ]  # [longitud, latitud]
percfrref = 21.0
lado = 'R'  # Derecha
coord_real = [-99.628523, 19.269612]  # Coordenadas reales [longitud, latitud]
poi_name = "OXXO"

resultados = visualizar_comparacion_simple(nodo_inicio, nodo_fin, percfrref, lado, coord_real, poi_name)