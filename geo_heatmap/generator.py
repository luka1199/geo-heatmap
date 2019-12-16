#!/usr/bin/env python3

import collections
import fnmatch
import json
import zipfile
from xml.dom import minidom

import folium
import ijson
from folium.plugins import HeatMap
from progressbar import ETA, Bar, Percentage, ProgressBar

from .utils import *


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
                coords = (round(loc["latitudeE7"] / 1e7, 6),
                          round(loc["longitudeE7"] / 1e7, 6))

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

    def generateMap(self, tiles, map_zoom_start=6, heatmap_radius=7,
                    heatmap_blur=4, heatmap_min_opacity=0.2,
                    heatmap_max_zoom=4):
        map_data = [(coords[0], coords[1], magnitude)
                    for coords, magnitude in self.coordinates.items()]

        # Generate map
        m = folium.Map(location=self.max_coordinates,
                       zoom_start=map_zoom_start,
                       tiles=tiles)

        # Generate heat map
        heatmap = HeatMap(map_data,
                          max_val=self.max_magnitude,
                          min_opacity=heatmap_min_opacity,
                          radius=heatmap_radius,
                          blur=heatmap_blur,
                          max_zoom=heatmap_max_zoom)

        m.add_child(heatmap)
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
