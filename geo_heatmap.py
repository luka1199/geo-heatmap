#!/usr/bin/env python3

from argparse import ArgumentParser, RawTextHelpFormatter
import collections
import fnmatch
import folium
from folium.plugins import HeatMap
import ijson
import json
import os
from progressbar import ProgressBar, Bar, ETA, Percentage
from utils import *
import webbrowser
from xml.etree import ElementTree
from xml.dom import minidom
import zipfile


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0
        self.resetStats()

    def resetStats(self):
        self.stats = {
            "Data points": 0
        }

    @staticmethod
    def findTimestampKey(json_element):
        """Find the correct key for timestamps - Google changed this in early 2022.
        Earlier, the correct key was "timestampMs".
        Now, it is "timestamp".
        This function simply tries to find these keys in the first data element.
        """
        if "timestampMs" in json_element.keys():  # Old data
            key_timestamp = "timestampMs"
        else:  # New data
            key_timestamp = "timestamp"

        return key_timestamp

    def loadJSONData(self, json_file, date_range):
        """Loads the Google location data from the given json file.

        Arguments:
            json_file {file} -- An open file-like object with JSON-encoded
                Google location data.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
        """
        data = json.load(json_file)

        # Find the correct key for timestamps
        first_element = data["locations"][0]
        key_timestamp = self.findTimestampKey(first_element)

        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=len(data["locations"]), widgets=w) as pb:
            for i, loc in enumerate(data["locations"]):
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                           round(loc["longitudeE7"] / 1e7, 6))

                if timestampInRange(loc[key_timestamp], date_range):
                    self.updateCoord(coords)
                pb.update(i)

    def streamJSONData(self, json_file, date_range):
        """Stream the Google location data from the given json file.

        Arguments:
            json_file {file} -- An open file-like object with JSON-encoded
                Google location data.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
        """
        # Estimate location amount
        max_value_est = sum(1 for line in json_file) / 13
        json_file.seek(0)

        locations = ijson.items(json_file, "locations.item")
        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=max_value_est, widgets=w) as pb:
            for i, loc in enumerate(locations):
                # Find the correct key for timestamps
                # This is done in the loop because the data are streamed
                if i == 0:
                    key_timestamp = self.findTimestampKey(loc)

                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                            round(loc["longitudeE7"] / 1e7, 6))

                if timestampInRange(loc[key_timestamp], date_range):
                    self.updateCoord(coords)

                if i > max_value_est:
                    max_value_est = i
                    pb.max_value = i
                pb.update(i)

    def loadKMLData(self, file_name, date_range):
        """Loads the Google location data from the given KML file.

        Arguments:
            file_name {string or file} -- The name of the KML file
                (or an open file-like object) with the Google location data.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
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

    def loadGPXData(self, file_name, date_range):
        """Loads location data from the given GPX file.

        Arguments:
            file_name {string or file} -- The name of the GPX file
                (or an open file-like object) with the GPX data.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
        """
        xmldoc = minidom.parse(file_name)
        gxtrack = xmldoc.getElementsByTagName("trkpt")
        w = [Bar(), Percentage(), " ", ETA()]

        with ProgressBar(max_value=len(gxtrack), widgets=w) as pb:
            for i, trkpt in enumerate(gxtrack):
                lat = trkpt.getAttribute("lat")
                lon = trkpt.getAttribute("lon")
                coords = (round(float(lat), 6), round(float(lon), 6))
                date = trkpt.getElementsByTagName("time")[0].firstChild.data
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
        self.stats["Data points"] += 1
        if self.coordinates[coords] > self.max_magnitude:
            self.max_coordinates = coords
            self.max_magnitude = self.coordinates[coords]

    def generateMap(self, settings):
        """Generates the heatmap.

        Arguments:
            settings {dict} -- The settings for the heatmap.

        Returns:
            Map -- The Heatmap.
        """
        tiles = settings["tiles"]
        zoom_start = settings["zoom_start"]
        radius = settings["radius"]
        blur = settings["blur"]
        min_opacity = settings["min_opacity"]
        max_zoom = settings["max_zoom"]

        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=zoom_start,
                       tiles=tiles,
                       attr="<a href=https://github.com/luka1199/geo-heatmap>geo-heatmap</a>")

        # Generate heat map
        heatmap = HeatMap(map_data,
                          max_val=self.max_magnitude,
                          min_opacity=min_opacity,
                          radius=radius,
                          blur=blur,
                          max_zoom=max_zoom)

        m.add_child(heatmap)
        return m

    def run(self, data_files, output_file, date_range, stream_data, settings):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_files {list} -- List of names of the data files with the Google
                location data or the Google takeout ZIP archive.
            output_file {string} -- The name of the output file.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
            stream_data {bool} -- Stream option.
            settings {dict} -- The settings for the heatmap.
        """
        self.resetStats()

        for i, data_file in enumerate(data_files):
            print("\n({}/{}) Loading data from {}".format(
                i + 1,
                len(data_files) + 2,
                data_file))
            if data_file.endswith(".zip"):
                self.loadZIPData(data_file, date_range)
            elif data_file.endswith(".json"):
                with open(data_file) as json_file:
                    if stream_data:
                        self.streamJSONData(json_file, date_range)
                    else:
                        self.loadJSONData(json_file, date_range)
            elif data_file.endswith(".kml"):
                self.loadKMLData(data_file, date_range)
            elif data_file.endswith(".gpx"):
                self.loadGPXData(data_file, date_range)
            else:
                raise NotImplementedError(
                    "Unsupported file extension for {!r}".format(data_file))

        print("\n({}/{}) Generating heatmap".format(
            len(data_files) + 1,
            len(data_files) + 2))
        m = self.generateMap(settings)
        print("\n({}/{}) Saving map to {}\n".format(
            len(data_files) + 2,
            len(data_files) + 2,
            output_file))
        m.save(output_file)

        print("Stats:")
        for name, stat in self.stats.items():
            print("{}: {}".format(name, stat))
        print()

if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "files", metavar="file", type=str, nargs="+", help="Any of the following files:\n"
        "- Your location history JSON file from Google Takeout\n"
        "- Your location history KML file from Google Takeout\n"
        "- The takeout-*.zip raw download from Google Takeout \nthat contains either of the above files\n"
        "- A GPX file containing GPS tracks")
    parser.add_argument("-o", "--output", dest="output", type=str, required=False,
                        help="Path of heatmap HTML output file.", default="heatmap.html")
    parser.add_argument("--min-date", dest="min_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The earliest date from which you want to see data in the heatmap.")
    parser.add_argument("--max-date", dest="max_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The latest date from which you want to see data in the heatmap.")
    parser.add_argument("-s", "--stream", dest="stream", action="store_true", help="Option to iteratively load data.")
    parser.add_argument("--map", "-m", dest="map", metavar="MAP", type=str, required=False, default="OpenStreetMap",
                        help="The name of the map tiles you want to use.\n" \
                        "(e.g. 'OpenStreetMap', 'StamenTerrain', 'StamenToner', 'StamenWatercolor')")
    parser.add_argument("-z", "--zoom-start", dest="zoom_start", type=int, required=False,
                        help="The initial zoom level for the map. (default: %(default)s)", default=6)
    parser.add_argument("-r", "--radius", type=int, required=False,
                        help="The radius of each location point. (default: %(default)s)", default=7)
    parser.add_argument("-b", "--blur", type=int, required=False,
                        help="The amount of blur. (default: %(default)s)", default=4)
    parser.add_argument("-mo", "--min-opacity", dest="min_opacity", type=float, required=False,
                        help="The minimum opacity of the heatmap. (default: %(default)s)", default=0.2)
    parser.add_argument("-mz", "--max-zoom", dest="max_zoom", type=int, required=False,
                        help="The maximum zoom of the heatmap. (default: %(default)s)", default=4)


    args = parser.parse_args()
    data_file = args.files
    output_file = args.output
    date_range = args.min_date, args.max_date
    stream_data = args.stream
    settings = {
        "tiles": args.map,
        "zoom_start": args.zoom_start,
        "radius": args.radius,
        "blur": args.blur,
        "min_opacity": args.min_opacity,
        "max_zoom": args.max_zoom
    }

    generator = Generator()
    generator.run(data_file, output_file, date_range, stream_data, settings)
    # Check if browser is text-based
    if not isTextBasedBrowser(webbrowser.get()):
        try:
            print("[info] Opening {} in browser".format(output_file))
            webbrowser.open("file://" + os.path.realpath(output_file))
        except webbrowser.Error:
            print("[info] No runnable browser found. Open {} manually.".format(
                output_file))
            print("[info] Path to heatmap file: \"{}\"".format(os.path.abspath(output_file)))
