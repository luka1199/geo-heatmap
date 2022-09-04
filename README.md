# Geo Heatmap

<p align="center"><img src="https://user-images.githubusercontent.com/45404400/63515170-7a9cd280-c4ea-11e9-8875-e693622ac26e.png" alt="screenshot" width="400"></p>

This is a script that generates an interactive geo heatmap from your Google location history data using Python, Folium and OpenStreetMap.

## Getting Started

### 1. Install Python 3+

If you don't already have Python 3+ installed, grab it from <https://www.python.org/downloads/>. You'll want to download install the latest version of **Python 3.x**. As of 2019-11-22, that is Version 3.8.

### 2. Get Your Location Data

Here you can find out how to download your Google data: <https://support.google.com/accounts/answer/3024190?hl=en></br>
Here you can download all of the data that Google has stored on you: <https://takeout.google.com/>

To use this script, you only need to select and download your "Location History", which Google will provide to you as a JSON file by default.  KML is also an output option and is accepted for this program.

You can also import [GPS Exchange Format (GPX)](https://en.wikipedia.org/wiki/GPS_Exchange_Format) files,
e.g. from a GPS tracker.

### 3. Clone This Repository

On <https://github.com/luka1199/geo-heatmap>, click the green "Clone or Download" button at the top right of the page. If you want to get started with this script more quickly, click the "Download ZIP" button, and extract the ZIP somewhere on your computer.

### 4. Install Dependencies

In a [command prompt or Terminal window](https://tutorial.djangogirls.org/en/intro_to_command_line/#what-is-the-command-line), [navigate to the directory](https://tutorial.djangogirls.org/en/intro_to_command_line/#change-current-directory) containing this repository's files. Then, type the following, and press enter:

```shell
pip install -r requirements.txt
```

### 5. Run the Script

In the same command prompt or Terminal window, type the following, and press enter:

```shell
python geo_heatmap.py <file> [<file> ...]
```

Replace the string `<file>` from above with the path to any of the following files:

- The `Location History.json` JSON file from Google Takeout
- The `Location History.kml` KML file from Google Takeout
- The `takeout-*.zip` raw download from Google Takeout that contains either of the above files
- A [GPS Exchange Format (GPX)](https://en.wikipedia.org/wiki/GPS_Exchange_Format) file

#### Examples:

Single file:

```shell
python geo_heatmap.py C:\Users\Testuser\Desktop\Records.json
```

```shell
python geo_heatmap.py "C:\Users\Testuser\Desktop\Location History.json"
```

```shell
python geo_heatmap.py Records.json
```

Multiple files:

```shell
python geo_heatmap.py Records.json locations.kml takeout.zip
```

Using the stream option (for users with Memory Errors):

```shell
python geo_heatmap.py -s Records.json
```

Set a date range:

```shell
python geo_heatmap.py --min-date 2017-01-02 --max-date 2018-12-30 Records.json
```

Advanced heatmap settings:

```shell
python geo_heatmap.py -z 15 -r 12 -b 7 -mo 0.3 -mz 20 Records.json
```

#### Usage:

```
usage: geo_heatmap.py [-h] [-o OUTPUT] [--min-date YYYY-MM-DD]
                      [--max-date YYYY-MM-DD] [-s] [--map MAP] [-z ZOOM_START]
                      [-r RADIUS] [-b BLUR] [-mo MIN_OPACITY] [-mz MAX_ZOOM]
                      file [file ...]

positional arguments:
  file                  Any of the following files:
                        - Your location history JSON file from Google Takeout
                        - Your location history KML file from Google Takeout
                        - The takeout-*.zip raw download from Google Takeout
                        that contains either of the above files
                        - A GPX file containing GPS tracks

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path of heatmap HTML output file.
  --min-date YYYY-MM-DD
                        The earliest date from which you want to see data in the heatmap.
  --max-date YYYY-MM-DD
                        The latest date from which you want to see data in the heatmap.
  -s, --stream          Option to iteratively load data.
  --map MAP, -m MAP     The name of the map tiles you want to use.
                        (e.g. 'OpenStreetMap', 'StamenTerrain', 'StamenToner', 'StamenWatercolor')
  -z ZOOM_START, --zoom-start ZOOM_START
                        The initial zoom level for the map. (default: 6)
  -r RADIUS, --radius RADIUS
                        The radius of each location point. (default: 7)
  -b BLUR, --blur BLUR  The amount of blur. (default: 4)
  -mo MIN_OPACITY, --min-opacity MIN_OPACITY
                        The minimum opacity of the heatmap. (default: 0.2)
  -mz MAX_ZOOM, --max-zoom MAX_ZOOM
                        The maximum zoom of the heatmap. (default: 4)
```

### 6. Review the Results

The script will generate a HTML file named `heatmap.html`. This file will automatically open in your browser once the script completes. Enjoy!

## FAQ

### I'm getting an "Out of Memory" error or `MemoryError` when I try to run the script. What's going on?

Your `LocationHistory.json` file is probably huge, and Python is running out of memory when the script tries to parse that file.

To fix this, download and install the 64-bit version of Python. To do this:

1. Go to [python.org](https://www.python.org/downloads/).
2. Click the link corresponding to your OS next to "Looking for Python with a different OS?"
3. Click the "Latest Python 3 Release" link.
4. Scroll down to "Files".
5. Click to download the x64 release. For example, on Windows, that's the "Windows x86-64 executable installer" link.
6. Install!

If this does not fix the issue you can use the stream option:

```shell
python geo_heatmap.py -s <file>
```

This will be slower but will use much less memory to load your location data.

### I'm getting a `SyntaxError` when running `pip install -r requirements.txt` or `python geo_heatmap.py <file>`. What am I doing wrong?

You are probably using the python interpreter to run these commands. Try to run them in cmd.exe or Windows PowerShell (Windows) or the Terminal (Linux, MacOS).

### I'm getting the error message `TypeError: __init__() got an unexpected keyword argument 'max_value'`. What can I do to fix this?

Try to run:

```shell
pip uninstall progressbar
pip install progressbar2
```

You probably have progressbar installed, which uses `maxval` as an argument for `__init__`. Progressbar2 uses `max_value`.
