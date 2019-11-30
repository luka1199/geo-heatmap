#!/usr/bin/env python3

import collections
import fnmatch
import json
import os
from argparse import ArgumentParser, RawTextHelpFormatter
import webbrowser
import zipfile
import folium
from folium.plugins import HeatMap
from progressbar import ProgressBar, Bar, ETA, Percentage
from xml.etree import ElementTree
from xml.dom import minidom


TEXT_BASED_BROWSERS = [webbrowser.GenericBrowser, webbrowser.Elinks]


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0

    def loadJSONData(self, json_file):
        """Loads the google location data from the given json file.

        Arguments:
            json_file -- An open file-like object with JSON-encoded
                google location data.
        """
        data = json.load(json_file)
        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=len(data["locations"]),
                            widgets=w) as pb:
            for i, loc in enumerate(data["locations"]):
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                lat_lon = (round(loc["latitudeE7"] / 1e7, 6),
                            round(loc["longitudeE7"] / 1e7, 6))
                
                self.updateCoord(lat_lon)
                pb.update(i)

    def loadKMLData(self, file_name):
        """Loads the google location data from the given KML file.

        Arguments:
            file_name {string or file} -- The name of the KML file
                (or an open file-like object) with the google location data.
        """
        xmldoc = minidom.parse(file_name)
        kml = xmldoc.getElementsByTagName("kml")[0]
        document = kml.getElementsByTagName("Document")[0]
        placemark = document.getElementsByTagName("Placemark")[0]
        gxtrack = placemark.getElementsByTagName("gx:coord")
        w = [Bar(), Percentage(), " ", ETA()]

        with ProgressBar(max_value=len(gxtrack), widgets=w) as pb:
            for i, number in enumerate(gxtrack):
                loc = (number.firstChild.data).split()
                lat_lon = (loc[1], loc[0])

                self.updateCoord(lat_lon)
                pb.update(i)

    def load_zip_data(self, file_name):
        """
        Load google location data from a "takeout-*.zip" file.
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
        (elem,) = soup.select("#service-tile-LOCATION_HISTORY > button > div.service_summary > div > h1[data-english-name=LOCATION_HISTORY]")
        name = elem["data-folder-name"]
        (data_path,) = fnmatch.filter(namelist, "Takeout/{name}/{name}.*".format(name=name))
        print("Reading location data file from zip archive: {!r}".format(data_path))
        if data_path.endswith(".json"):
            with zip_file.open(data_path) as read_file:
                self.loadJSONData(read_file)
        elif data_path.endswith(".kml"):
            with zip_file.open(data_path) as read_file:
                self.loadKMLData(read_file)
        else:
            raise ValueError(
                "unsupported extension for {!r}: only .json and .kml supported"
                .format(file_name)
                )

    def updateCoord(self, lat_lon):
        self.coordinates[lat_lon] += 1
        if self.coordinates[lat_lon] > self.max_magnitude:
            self.max_coordinates = lat_lon
            self.max_magnitude = self.coordinates[lat_lon]

    def generateMap(self, map_zoom_start=6, heatmap_radius=7,
                    heatmap_blur=4, heatmap_min_opacity=0.2,
                    heatmap_max_zoom=4):
        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=map_zoom_start,
                       tiles="OpenStreetMap")

        # Generate heat map
        heatmap = HeatMap(map_data,
                          max_val=self.max_magnitude,
                          min_opacity=heatmap_min_opacity,
                          radius=heatmap_radius,
                          blur=heatmap_blur,
                          max_zoom=heatmap_max_zoom)

        m.add_child(heatmap)
        return m

    def run(self, data_files, output_file):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_file {string} -- The name of the data file with the google
                location data or the goole takeout ZIP archive.
            output_file {string} -- The name of the output file.
        """
        for data_file in data_files:
            print("Loading data from {}...".format(data_file))
            if data_file.endswith(".zip"):
                self.load_zip_data(data_file)
            elif data_file.endswith(".json"):
                with open(data_file) as json_file:
                    self.loadJSONData(json_file)
            elif data_file.endswith(".kml"):
                self.loadKMLData(data_file)
            else:
                raise NotImplementedError("Unsupported file extension for {!r}".format(data_file))
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
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "files", metavar="file", type=str, nargs='+', help="Any of the following files:\n"
        "1. Your location history JSON file from Google Takeout\n"
        "2. Your location history KML file from Google Takeout\n"
        "3. The takeout-*.zip raw download from Google Takeout \nthat contains either of the above files")
    parser.add_argument("-o", "--output", dest="output", metavar="", type=str, required=False,
                        help="Path of heatmap HTML output file.", default="heatmap.html")
    args = parser.parse_args()
    data_file = args.files
    output_file = args.output
    
    generator = Generator()
    generator.run(data_file, output_file)
    # Check if browser is text-based
    if not isTextBasedBrowser(webbrowser.get()):
        print("Opening {} in browser...".format(output_file))
        webbrowser.open("file://" + os.path.realpath(output_file))
