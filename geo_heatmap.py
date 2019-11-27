#!/usr/bin/env python3

import collections
import json
import os
import sys
import webbrowser
import folium
from folium.plugins import HeatMap
from progressbar import ProgressBar, Bar, ETA, Percentage
from datetime import datetime


TEXT_BASED_BROWSERS = [webbrowser.GenericBrowser, webbrowser.Elinks]


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0

    def loadData(self, file_name, year, month, day):
        """Loads the google location data from the given json file.

        Arguments:
            file_name {string} -- The name of the json file with the google        
            location data.
            
            I know the kode to messy but i will fix it. It is my first progran as a hobby enthusiast
            and my first upload to git hub.
        """
        with open(file_name) as json_file:
            data = json.load(json_file)
            searchs = year + '-' + month + '-' + day
            w = [Bar(), Percentage(), ' ', ETA()]
            with ProgressBar(
                    max_value=len(data["locations"]),
                    widgets=w) as pb:
                for (i, loc) in enumerate(data["locations"]):
                    if "latitudeE7" not in loc or "longitudeE7" not in loc:
                        continue
                    
                    timestamp = int(loc['timestampMs']) / 1000
                    dt = str(datetime.fromtimestamp(timestamp)).split(' ')[0]

                    if dt != searchs:
                        continue
                    lat = round(loc["latitudeE7"] / 1e7, 6)
                    lon = round(loc["longitudeE7"] / 1e7, 6)
                    self.coordinates[(lat, lon)] += 1
                    if self.coordinates[(lat, lon)] > self.max_magnitude:
                        self.max_coordinates = (lat, lon)
                        self.max_magnitude = self.coordinates[(lat, lon)]
                    pb.update(i)


    def generateMap(self, map_zoom_start=6, heatmap_radius=7,
                    heatmap_blur=4, heatmap_min_opacity=0.2,
                    heatmap_max_zoom=4):
        """Generates a heatmap and saves it in the output_file.

        Arguments:
            output_file {string} -- The name of the output file.
        """
        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=map_zoom_start,
                       tiles="OpenStreetMap")

        # Generate heat map
        heatmap = folium.plugins.HeatMap(
                                    map_data,
                                    max_val=self.max_magnitude,
                                    min_opacity=heatmap_min_opacity,
                                    radius=heatmap_radius,
                                    blur=heatmap_blur,
                                    max_zoom=heatmap_max_zoom)

        m.add_child(heatmap)
        return m

    def run(self, data_file, year, month, day, output_file):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_file {string} -- The name of the json file with the google
                location data.
            output_file {[type]} -- The name of the output file.
        """

        print("Loading data from {}...".format(data_file))
        self.loadData(data_file, year, month, day)
        print("Generating heatmap...")
        m = self.generateMap()
        print("Saving map to {}...".format(output_file))
        m.save(output_file)


def isTextBasedBrowser(browser):
    """Returns if browser is a text-based browser.

    Arguments:
        browser {webbrowser.BaseBrowser} -- A browser.

    Returns:
        bool -- True if browser is text-based, False if browser is not
            text-based.
    """
    for tb_browser in TEXT_BASED_BROWSERS:
        if type(browser) is tb_browser:
            return True
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        year = sys.argv[2]
        month = sys.argv[3]
        day = sys.argv[4]
        output_file = "heatmap.html"
        generator = Generator()
        generator.run(data_file, year, month, day, output_file)
        # Check if browser is text-based
        if not isTextBasedBrowser(webbrowser.get()):
            print("Opening {} in browser...".format(output_file))
            webbrowser.open('file://' + os.path.realpath(output_file))
    else:
        print("Usage: python geo_heatmap.py <file>")
        sys.exit()
