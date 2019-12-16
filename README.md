# Geo Heatmap

![screenshot](https://user-images.githubusercontent.com/45404400/63515170-7a9cd280-c4ea-11e9-8875-e693622ac26e.png)

This is a script that generates an interactive geo heatmap from your Google location history data using Python, Folium and OpenStreetMap.

## Getting Started

### 1. Install Python 3+

If you don't already have Python 3+ installed, grab it from <https://www.python.org/downloads/>. You'll want to download install the latest version of **Python 3.x**. As of 2019-11-22, that is Version 3.8.

For ease of python version handling, I'd recommend installing it through [pyenv](https://github.com/pyenv/pyenv#installation).

### 2. Get Your Location Data

Here you can find out how to download your Google data: <https://support.google.com/accounts/answer/3024190?hl=en></br>
Here you can download all of the data that Google has stored on you: <https://takeout.google.com/>

To use this script, you only need to select and download your "Location History", which Google will provide to you as a JSON file by default. KML is also an output option and is accepted for this program.

### 3. Install the script

In a [command prompt or Terminal window](https://tutorial.djangogirls.org/en/intro_to_command_line/#what-is-the-command-line), [navigate to the directory](https://tutorial.djangogirls.org/en/intro_to_command_line/#change-current-directory) containing the location data files. Then, type the following, and press enter:

```shell
pip install geo-heatmap
```

### 4. Run the Script

In the same command prompt or Terminal window, type the following, and press enter:

```shell
geo-heatmap <file> [<file> ...]
```

Replace the string `<file>` from above with the path to any of the following files:

1. The `Location History.json` JSON file from Google Takeout
2. The `Location History.kml` KML file from Google Takeout
3. The `takeout-*.zip` raw download from Google Takeout that contains either of the above files

#### Examples:

Single file:

```shell
geo-heatmap C:\Users\Testuser\Desktop\locations.json
```

```shell
geo-heatmap "C:\Users\Testuser\Desktop\Location History.json"
```

```shell
geo-heatmap locations.json
```

Multiple files:

```shell
geo-heatmap locations.json locations.kml takeout.zip
```

Using the stream option (for users with Memory Errors):

```shell
geo-heatmap -s locations.json
```

Set a date range:

```shell
geo-heatmap --min-date 2017-01-02 --max-date 2018-12-30 locations.json
```

#### Usage:

```
usage: geo-heatmap [-h] [-o] [--min-date YYYY-MM-DD]
                      [--max-date YYYY-MM-DD] [-s] [--map MAP]
                      file [file ...]

positional arguments:
  file                  Any of the following files:
                        1. Your location history JSON file from Google Takeout
                        2. Your location history KML file from Google Takeout
                        3. The takeout-*.zip raw download from Google Takeout
                        that contains either of the above files

optional arguments:
  -h, --help            show this help message and exit
  -o , --output         Path of heatmap HTML output file.
  --min-date YYYY-MM-DD
                        The earliest date from which you want to see data in the heatmap.
  --max-date YYYY-MM-DD
                        The latest date from which you want to see data in the heatmap.
  -s, --stream          Option to iteratively load data.
  --map MAP, -m MAP     The name of the map tiles you want to use.
                        (e.g. 'OpenStreetMap', 'StamenTerrain', 'StamenToner', 'StamenWatercolor')
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
geo-heatmap -s <file>
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

## Development

This project is using [Poetry](https://python-poetry.org/) to manage dependencies. You can install it by following their guide.

If you would like to develop on this further, after cloning this repository and navigating into it you can get up and running with the following:

```shell
poetry install
poetry run geo-heatmap
```
