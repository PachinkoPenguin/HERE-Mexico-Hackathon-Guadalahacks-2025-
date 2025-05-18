import json
import time

def en_cdmx(lat, lon):
    return 19.2 <= lat <= 19.6 and -99.35 <= lon <= -98.9

def en_toluca(lat, lon):
    return 19.15 <= lat <= 19.4 and -99.75 <= lon <= -99.50

def extraer_puntos(data):
    puntos = []

    def recorrer(sublista):
        if isinstance(sublista, list):
            if len(sublista) == 2 and all(isinstance(i, (int, float)) for i in sublista):
                puntos.append(sublista)
            else:
                for item in sublista:
                    recorrer(item)

    recorrer(data)
    return puntos

def main():
    long = 0
    lat = 0
    with open(r'./STREETS_NAMING_ADDRESSING/SREETS_NAMING_ADDRESSING_4815096.geojson', 'r') as f:
        data = json.load(f)
        
    for data_ind in data['features']:
        long = 0
        lat = 0
        data_individual = extraer_puntos(data_ind['geometry']['coordinates'])
        for list in data_individual:
            num = len(data_individual)
            x, y = list[0], list[1]
            long += x
            lat += y
        long /= num
        lat /= num
        print(data_ind['properties']['ST_NAME'])
        print(data_ind['properties'])
        print(f"lat: {lat}, long: {long}")
        print(f'CDMX: {en_cdmx(lat, long)}')
        print(f'TOLUCA: {en_toluca(lat, long)}\n\n')

if __name__ == "__main__":
    main()