# geo-heatmap

A script that generates an interactive geo heatmap from your location data provided by google using folium and OpenStreetMap.

<p align="center"><img src="https://user-images.githubusercontent.com/45404400/63515170-7a9cd280-c4ea-11e9-8875-e693622ac26e.png" alt="screenshot" width="400"></p>

## How to get your location data

Here you can find out how to download your google data: <https://support.google.com/accounts/answer/3024190?hl=en></br>
Here you can download your google data: <https://takeout.google.com/>

For this script you just have to download your location history, which is provided by google as JSON file.

## Getting Started

### Dependencies
```
pip install -r requirements.txt
```

### Run the script
```
python geo_heatmap.py <file>
```
Enter JSON file name as the file argument.

The script will generate a HTML file named `heatmap.html` which will automatically open in your browser.
