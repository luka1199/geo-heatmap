#!/usr/bin/env python3

from argparse import ArgumentParser, RawTextHelpFormatter
import collections
import fnmatch
import folium
from folium.plugins import HeatMap
import json
import os
from progressbar import ProgressBar, Bar, ETA, Percentage
from utils import *
from xml.etree import ElementTree
from xml.dom import minidom
import zipfile


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0
        self.map_copyrights = {
            "openstreetmap": "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors",
            "stamen terrain": """
                            <a href="http://maps.stamen.com/">Map tiles</a> by
                            <a href="http://stamen.com">Stamen Design</a>, under
                            <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>.
                            Data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>
                            contributors.""",
            "stamen toner": """
                            <a href="http://maps.stamen.com/">Map tiles</a> by
                            <a href="http://stamen.com">Stamen Design</a>, under
                            <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>.
                            Data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>
                            contributors."""
        }


    def loadJSONData(self, json_file, date_range):
        """Loads the Google location data from the given json file.

        Arguments:
            json_file -- An open file-like object with JSON-encoded
                Google location data.
        """
        data = json.load(json_file)
        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=len(data["locations"]), widgets=w) as pb:
            for i, loc in enumerate(data["locations"]):
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                           round(loc["longitudeE7"] / 1e7, 6))

                if timestampInRange(loc['timestampMs'], date_range):
                    self.updateCoord(coords)
                pb.update(i)

    def loadKMLData(self, file_name, date_range):
        """Loads the Google location data from the given KML file.

        Arguments:
            file_name {string or file} -- The name of the KML file
                (or an open file-like object) with the Google location data.
        """
        xmldoc = minidom.parse(file_name)
        gxtrack = xmldoc.getElementsByTagName("gx:coord")
        when = xmldoc.getElementsByTagName("when")
        w = [Bar(), Percentage(), " ", ETA()]

        with ProgressBar(max_value=len(gxtrack), widgets=w) as pb:
            for i, number in enumerate(gxtrack):
                loc = (number.firstChild.data).split()
                coords = (round(float(loc[1]), 6), round(float(loc[0]), 6))
                date = when[i].firstChild.data
                if dateInRange(date[:10], date_range):
                    self.updateCoord(coords)
                pb.update(i)

    def loadZIPData(self, file_name, date_range):
        """
        Load Google location data from a "takeout-*.zip" file.
        """
        from bs4 import BeautifulSoup
        """
        <div class="service_name">
            <h1 class="data-folder-name" data-english-name="LOCATION_HISTORY" data-folder-name="Location History">
                Location History
            </h1>
        </div>
        """
        zip_file = zipfile.ZipFile(file_name)
        namelist = zip_file.namelist()
        (html_path,) = fnmatch.filter(namelist, "Takeout/*.html")
        with zip_file.open(html_path) as read_file:
            soup = BeautifulSoup(read_file, "html.parser")
        (elem,) = soup.select(
            "#service-tile-LOCATION_HISTORY > button > div.service_summary > div > h1[data-english-name=LOCATION_HISTORY]")
        name = elem["data-folder-name"]
        (data_path,) = fnmatch.filter(
            namelist,
            "Takeout/{name}/{name}.*".format(name=name))
        print("Reading location data file from zip archive: {!r}".format(
            data_path))

        if data_path.endswith(".json"):
            with zip_file.open(data_path) as read_file:
                self.loadJSONData(read_file, date_range)
        elif data_path.endswith(".kml"):
            with zip_file.open(data_path) as read_file:
                self.loadKMLData(read_file, date_range)
        else:
            raise ValueError("unsupported extension for {!r}: only .json and .kml supported"
                .format(file_name))

    def updateCoord(self, coords):
        self.coordinates[coords] += 1
        if self.coordinates[coords] > self.max_magnitude:
            self.max_coordinates = coords
            self.max_magnitude = self.coordinates[coords]

    def getMapCopyright(self, name):
        if name.lower() in self.map_copyrights:
            return self.map_copyrights[name.lower()]
        return None

    def generateMap(self, tiles, map_zoom_start=6, heatmap_radius=7,
                    heatmap_blur=4, heatmap_min_opacity=0.2,
                    heatmap_max_zoom=4):
        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=map_zoom_start,
                       tiles=tiles,
                       attr=self.getMapCopyright(tiles))

        # Generate heat map
        heatmap = HeatMap(map_data,
                          max_val=self.max_magnitude,
                          min_opacity=heatmap_min_opacity,
                          radius=heatmap_radius,
                          blur=heatmap_blur,
                          max_zoom=heatmap_max_zoom)

        m.add_child(heatmap)
        return m

    def run(self, data_files, output_file, date_range, tiles):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_files {list} -- List of names of the data files with the Google
                location data or the Goole takeout ZIP archive.
            output_file {string} -- The name of the output file.
        """
        for i, data_file in enumerate(data_files):
            print("({}/{}) Loading data from {}".format(
                i + 1, 
                len(data_files) + 2, 
                data_file))
            if data_file.endswith(".zip"):
                self.loadZIPData(data_file, date_range)
            elif data_file.endswith(".json"):
                with open(data_file) as json_file:
                    self.loadJSONData(json_file, date_range)
            elif data_file.endswith(".kml"):
                self.loadKMLData(data_file, date_range)
            else:
                raise NotImplementedError(
                    "Unsupported file extension for {!r}".format(data_file))
                
        print("({}/{}) Generating heatmap".format(
            len(data_files) + 1, 
            len(data_files) + 2))
        m = self.generateMap(tiles)
        print("({}/{}) Saving map to {}".format(
            len(data_files) + 2,
            len(data_files) + 2,
            output_file))
        m.save(output_file)


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "files", metavar="file", type=str, nargs='+', help="Any of the following files:\n"
        "1. Your location history JSON file from Google Takeout\n"
        "2. Your location history KML file from Google Takeout\n"
        "3. The takeout-*.zip raw download from Google Takeout \nthat contains either of the above files")
    parser.add_argument("-o", "--output", dest="output", metavar="", type=str, required=False,
                        help="Path of heatmap HTML output file.", default="heatmap.html")
    parser.add_argument("--min-date", dest="min_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The earliest date from which you want to see data in the heatmap.")
    parser.add_argument("--max-date", dest="max_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The latest date from which you want to see data in the heatmap.")
    parser.add_argument("--map", "-m", dest="map", metavar="MAP", type=str, required=False, default="OpenStreetMap",
                        help="The name of the map tiles you want to use.\n" \
                        "(e.g. 'OpenStreetMap', 'Stamen Terrain', 'Stamen Toner')")

    args = parser.parse_args()
    data_file = args.files
    output_file = args.output
    date_range = args.min_date, args.max_date
    tiles = args.map

    generator = Generator()
    generator.run(data_file, output_file, date_range, tiles)
    # Check if browser is text-based
    if not isTextBasedBrowser(webbrowser.get()):
        print("[info] Opening {} in browser".format(output_file))
        webbrowser.open("file://" + os.path.realpath(output_file))
