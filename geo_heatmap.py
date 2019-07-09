import json
import os

# SETTINGS
MAP_ZOOM_START = 6
HEATMAP_RADIUS = 7
HEATMAP_BLUR = 4
HEATMAP_MIN_OPACITY = 0.2

COORDS = {}
max = 0
max_coords = (0, 0)

with open('heatmap.csv', 'w') as output:
    output.write("name;lat;lon;magnitude\n")
    with open('locations.json') as json_file:
        print("Loading data...")
        data = json.load(json_file)
        data_len = len(data["locations"])
        i = 1
        for loc in data["locations"]:
            lat = round(loc["latitudeE7"]/10000000, 6)
            lon = round(loc["longitudeE7"]/10000000, 6)
            if (lat, lon) in COORDS.keys():
                COORDS[(lat, lon)] += 1
            else:
                COORDS[(lat, lon)] = 1
            # if i % 1000 == 0:
            #     print(i, "/", data_len, sep="")
            i += 1

        print("Generating .csv file...")
        i = 0
        for key, value in COORDS.items():
            output.write("{};{};{};{}\n".format(i, key[0], key[1], value))
            if value > max:
                max = value
                max_coords = key
            i += 1

print("Generating heat map...")
os.system("python heatmap_generator.py -ml {} {} -mzs {} -hmr {} -hmb {} -hmmo {}".format(max_coords[0],
            max_coords[1], MAP_ZOOM_START, HEATMAP_RADIUS, HEATMAP_BLUR, HEATMAP_MIN_OPACITY))
