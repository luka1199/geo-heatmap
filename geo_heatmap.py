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
from datetime import datetime


TEXT_BASED_BROWSERS = [webbrowser.GenericBrowser, webbrowser.Elinks]


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0
        
    def timestampInRange(self, timestamp, date_range):
        """Returns if the timestamp is in the date range.
        
        Arguments:
            timestamp {str} -- A timestamp (in ms).
            date_range {tuple} -- A tuple of strings representing the date range. 
            (min_date, max_date) (Date format: yyyy-mm-dd)
        """
        if date_range == (None, None):
            return True
        date_str = datetime.fromtimestamp(
            int(timestamp) / 1000).strftime("%Y-%m-%d")
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date_range[0] == None:
            min_date = None
        else:
            min_date = datetime.strptime(date_range[0], "%Y-%m-%d")
        if date_range[1] == None:
            max_date = None
        else:
            max_date = datetime.strptime(date_range[1], "%Y-%m-%d")
            
        return (min_date is None or min_date <= date) and \
            (max_date is None or max_date >= date)


    def loadJSONData(self, json_file, date_range):
        """Loads the Google location data from the given json file.

        Arguments:
            json_file -- An open file-like object with JSON-encoded
                Google location data.
        """
        data = json.load(json_file)
        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=len(data["locations"]),
                         widgets=w) as pb:
            for i, loc in enumerate(data["locations"]):
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                           round(loc["longitudeE7"] / 1e7, 6))
                
                if self.timestampInRange(loc['timestampMs'], date_range):
                    self.updateCoord(coords)
                pb.update(i)

    def loadKMLData(self, file_name, date_range):
        """Loads the Google location data from the given KML file.

        Arguments:
            file_name {string or file} -- The name of the KML file
                (or an open file-like object) with the Google location data.
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
                coords = (loc[1], loc[0])

                if self.timestampInRange(loc['timestampMs'], date_range):
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

    def run(self, data_files, output_file, date_range):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_files {list} -- List of names of the data files with the Google
                location data or the Goole takeout ZIP archive.
            output_file {string} -- The name of the output file.
        """
        for data_file in data_files:
            print("Loading data from {}...".format(data_file))
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
    parser.add_argument("--min-date", dest="min_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The earliest date from which you want to see data in the heatmap.")
    parser.add_argument("--max-date", dest="max_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The latest date from which you want to see data in the heatmap.")
    args = parser.parse_args()
    data_file = args.files
    output_file = args.output
    date_range = args.min_date, args.max_date
    
    generator = Generator()
    generator.run(data_file, output_file, date_range)
    # Check if browser is text-based
    if not isTextBasedBrowser(webbrowser.get()):
        print("Opening {} in browser...".format(output_file))
        webbrowser.open("file://" + os.path.realpath(output_file))
