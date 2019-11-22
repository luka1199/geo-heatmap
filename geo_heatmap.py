import json
import sys
import os
import webbrowser
import folium
from folium.plugins import HeatMap


class Generator:
    def __init__(self):
        self.coordinates = {}
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0

    def loadData(self, file_name):
        """Loads the google location data from the given json file.
        
        Arguments:
            file_name {string} -- The name of the json file with the google location data.
        """
        with open(file_name) as json_file:
            data = json.load(json_file)
            for loc in data["locations"]:
                lat = round(loc["latitudeE7"] / 1e7, 6)
                lon = round(loc["longitudeE7"] / 1e7, 6)
                try:
                    self.coordinates[(lat, lon)] += 1
                    if self.coordinates[(lat, lon)] > self.max_magnitude:
                        self.max_coordinates = (lat, lon)
                        self.max_magnitude = self.coordinates[(lat, lon)]
                except KeyError:
                    self.coordinates[(lat, lon)] = 1


    def generateMap(self, map_zoom_start=6, heatmap_radius=7, 
                    heatmap_blur=4, heatmap_min_opacity = 0.2, heatmap_max_zoom=4):
        """Generates a heatmap and saves it in the output_file.
        
        Arguments:
            output_file {string} -- The name of the output file.
        """
        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]
        max_amount = self.max_magnitude

        # Generate map
        map = folium.Map(location=self.max_coordinates,
                        zoom_start=map_zoom_start,
                         tiles="OpenStreetMap")

        # Generate heat map
        heatmap = folium.plugins.HeatMap(map_data,
                                        max_val=max_amount,
                                        min_opacity=heatmap_min_opacity,
                                        radius=heatmap_radius,
                                        blur=heatmap_blur,
                                        max_zoom=heatmap_max_zoom)

        map.add_child(heatmap)
        return map

    def run(self, data_file, output_file):
        """Load the data, generate the heatmap and save it.
        
        Arguments:
            data_file {string} -- The name of the json file with the google location data.
            output_file {[type]} -- The name of the output file.
        """
        print("Loading data from {}...".format(data_file))
        self.loadData(data_file)
        print("Generating heatmap...")
        map = self.generateMap()
        print("Saving map to {}...".format(output_file))
        map.save(output_file)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        output_file = "heatmap.html"
        generator = Generator()
        generator.run(data_file, output_file)
        print("Opening {} in browser...".format(output_file))
        webbrowser.open('file://' + os.path.realpath(output_file))
    else:
        print("Usage: python geo_heatmap.py <file>")
        sys.exit()
