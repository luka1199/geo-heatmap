# geo-heatmap

This is a script that generates an interactive geo heatmap from your Google location history data using Python, `folium` and OpenStreetMap.

<p align="center"><img src="https://user-images.githubusercontent.com/45404400/63515170-7a9cd280-c4ea-11e9-8875-e693622ac26e.png" alt="screenshot" width="400"></p>

## Getting Started

## 1. Get Your Location Data

Here you can find out how to download your Google data: <https://support.google.com/accounts/answer/3024190?hl=en></br>
Here you can download all of the data that Google has stored on you: <https://takeout.google.com/>

To use this script, you only need to select and download your "Location History", which Google will provide to you as a JSON file by default.

### 2. Clone This Repository
On <https://github.com/luka1199/geo-heatmap>, click the green "Clone or Download" button at the top right of the page. If you want to get started with this script more quickly, click the "Download ZIP" button, and extract the ZIP somewhere on your computer.

### 3. Install Dependencies
In a command prompt or Terminal window, navigate to the directory containing this repository's files. Then, type the following, and press enter:

```
pip install -r requirements.txt
```

### 4. Run the Script
In the same command prompt or Terminal window, type the following, and press enter:
```
python geo_heatmap.py <file>
```
Replace the string `<file>` from above with the path to the `LocationHistory.json` JSON file from Google Takeout.

### 5. Review the Results

The script will generate a HTML file named `heatmap.html`. This file will automatically open in your browser once the script completes. Enjoy!

### FAQ

#### I'm getting an "Out of Memory" or `MemoryError` error when I try to run the script. What's going on?
Your `LocationHistory.json` file is probably huge, and Python is running out of memory when the script tries to parse that file.

To fix this, download and install the 64-bit version of Python. To do this:
1. Go to (python.org)[https://www.python.org/downloads/].
2. Click the link corresponding to your OS next to "Looking for Python with a different OS?"
3. Click the "Latest Python 3 Release" link.
4. Scroll down to "Files".
5. Click to download the x64 release. For example, on Windows, that's the "Windows x86-64 executable installer" link.
6. Install!
