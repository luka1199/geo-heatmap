#!/usr/bin/env python3

from argparse import ArgumentParser, RawTextHelpFormatter
import collections
import fnmatch
import folium
from folium.plugins import HeatMap
import ijson
import json
import os
from geopy import Nominatim
from progressbar import ProgressBar, Bar, ETA, Percentage
from utils import *
import webbrowser
from xml.etree import ElementTree
from xml.dom import minidom
import zipfile
import datetime
from folium.plugins import HeatMapWithTime
import pandas as pd
from folium.plugins import MarkerCluster


class Generator:
    def __init__(self):
        self.coordinates = collections.defaultdict(int)
        self.max_coordinates = (0, 0)
        self.max_magnitude = 0

    def loadJSONData(self, json_file, date_range):
        """Loads the Google location data from the given json file.

        Arguments:
            json_file {file} -- An open file-like object with JSON-encoded
                Google location data.
            date_range {tuple} -- A tuple containing the min-date and max-date.
                e.g.: (None, None), (None, '2019-01-01'), ('2017-02-11'), ('2019-01-01')
        """
        data = json.load(json_file)
        w = [Bar(), Percentage(), " ", ETA()]
        with ProgressBar(max_value=len(data["locations"]), widgets=w) as pb:
            for i, loc in enumerate(data["locations"]):
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue

                timestamp = int(loc['timestampMs'])
                year = datetime.datetime.fromtimestamp(timestamp / 1000).year
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                          round(loc["longitudeE7"] / 1e7, 6), year)

                if timestampInRange(loc['timestampMs'], date_range):
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
                if "latitudeE7" not in loc or "longitudeE7" not in loc:
                    continue
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                          round(loc["longitudeE7"] / 1e7, 6))

                if timestampInRange(loc['timestampMs'], date_range):
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
            "#service-tile-LOCATION_HISTORY > button > div.service_summary > div > h1["
            "data-english-name=LOCATION_HISTORY]")
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
            self.max_coordinates = coords[0], coords[1]
            self.max_magnitude = self.coordinates[coords]

    def generateMap(self, tiles, map_zoom_start=6, heatmap_radius=7,
                    heatmap_blur=4, heatmap_min_opacity=0.2,
                    heatmap_max_zoom=4):

        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        map_data_with_year = [(coords[0], coords[1], magnitude, coords[2])
                              for coords, magnitude in self.coordinates.items()]

        df_data = pd.DataFrame(map_data_with_year, columns=['Lat', 'Long', 'Weight', 'Year'])

        year_list = df_data.Year.sort_values().unique()

        map_data_by_year = []
        for year in year_list:
            map_data_by_year.append(df_data.loc[df_data.Year == year,
                                                ['Lat', 'Long', 'Weight']].groupby(
                ['Lat', 'Long']).sum().reset_index().values.tolist())

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=map_zoom_start,
                       tiles=tiles)

        world_imagery = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

        folium.TileLayer(tiles=world_imagery, name="World Imagery",
                         attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community').add_to(
            m)
        folium.TileLayer(tiles='Stamen Terrain', name='Stamen Terrain').add_to(m)
        folium.TileLayer('cartodbdark_matter', name='Dark Matter').add_to(m)

        # Generate heat map

        heatmap = HeatMap(map_data,
                          max_val=self.max_magnitude,
                          min_opacity=heatmap_min_opacity,
                          radius=heatmap_radius,
                          blur=heatmap_blur,
                          max_zoom=heatmap_max_zoom).add_to(folium.FeatureGroup(name="Combined HeatMap").add_to(m))

        locator = Nominatim(user_agent="geocoder", timeout=None)

        timesVisited = [x[2] for x in map_data]
        timesVisited.sort(reverse=True)
        top20Visited = timesVisited[19]

        marker_group = folium.FeatureGroup(name="Markers")
        mc = MarkerCluster()

        for lat, lon, freq in map_data:
            if freq >= top20Visited:
                coordinates = lat, lon
                location = locator.reverse(coordinates)

                times_visited = location.address + "\nVisited " + str(freq) + " times"

                mc.add_child(folium.Marker(location=[lat, lon], popup=times_visited))


        folium.plugins.HeatMapWithTime(map_data_by_year, name = "HeatMap by Year", index= year_list.tolist(),
                                       min_opacity=heatmap_min_opacity,
                                       radius=heatmap_radius,
                                       gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}).add_to(m)

        mc.add_to(marker_group)
        marker_group.add_to(m)

        folium.LayerControl().add_to(m)

        return m

    def run(self, data_files, output_file, date_range, stream_data, tiles):
        """Load the data, generate the heatmap and save it.

        Arguments:
            data_files {list} -- List of names of the data files with the Google
                location data or the Google takeout ZIP archive.
            output_file {string} -- The name of the output file.
        """
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
            else:
                raise NotImplementedError(
                    "Unsupported file extension for {!r}".format(data_file))

        print("\n({}/{}) Generating heatmap".format(
            len(data_files) + 1,
            len(data_files) + 2))
        m = self.generateMap(tiles)
        print("\n({}/{}) Saving map to {}\n".format(
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
                                                           "3. The takeout-*.zip raw download from Google Takeout "
                                                           "\nthat contains either of the above files")
    parser.add_argument("-o", "--output", dest="output", metavar="", type=str, required=False,
                        help="Path of heatmap HTML output file.", default="heatmap.html")
    parser.add_argument("--min-date", dest="min_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The earliest date from which you want to see data in the heatmap.")
    parser.add_argument("--max-date", dest="max_date", metavar="YYYY-MM-DD", type=str, required=False,
                        help="The latest date from which you want to see data in the heatmap.")
    parser.add_argument("-s", "--stream", dest="stream", action="store_true", help="Option to iteratively load data.")
    parser.add_argument("--map", "-m", dest="map", metavar="MAP", type=str, required=False, default="OpenStreetMap",
                        help="The name of the map tiles you want to use.\n" \
                             "(e.g. 'OpenStreetMap', 'StamenTerrain', 'StamenToner', 'StamenWatercolor')")

    args = parser.parse_args()
    data_file = args.files
    output_file = args.output
    date_range = args.min_date, args.max_date
    tiles = args.map
    stream_data = args.stream

    generator = Generator()
    generator.run(data_file, output_file, date_range, stream_data, tiles)
    # Check if browser is text-based
    if not isTextBasedBrowser(webbrowser.get()):
        try:
            print("[info] Opening {} in browser".format(output_file))
            webbrowser.open("file://" + os.path.realpath(output_file))
        except webbrowser.Error:
            print("[info] No runnable browser found. Open {} manually.".format(
                output_file))
            print("[info] Path to heatmap file: \"{}\"".format(os.path.abspath(output_file)))
