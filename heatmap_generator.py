
import folium
from folium.plugins import HeatMap
import pandas as pd
from argparse import ArgumentParser


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', dest='csv', type=str, required=False,
                        help='Path to CSV data file', default='heatmap.csv')
    parser.add_argument('-o', '--output', dest='output', type=str, required=False,
                        help='Path of html geographical heatmap', default='heatmap.html')
    parser.add_argument('-ml', '--map_location', nargs='+', dest='map_location', type=str, required=False,
                        help='Latitude and Longitude of Map (Northing, Easting)', default=['55.0', '24.0'])
    parser.add_argument('-mzs', '--map_zoom_start', dest='map_zoom_start', type=int, required=False,
                        help='Initial zoom level for the map', default=7)
    parser.add_argument('-hmr', '--heatmap_radius', dest='heatmap_radius', type=int, required=False,
                        help='Heatmap radius of each “point” of the heatmap', default=5)
    parser.add_argument('-hmb', '--headmap_blur', dest='heatmap_blur', type=int, required=False,
                        help='Heatmap amount of blur', default=5)
    parser.add_argument('-hmmo', '--heatmap_min_opocity', dest='heatmap_min_opocity', type=float, required=False,
                        help='Heatmap minimum opacity the heat will start at', default=0.2)
    parser.add_argument('-hmmz', '--heatmap_max_zoom', dest='heatmap_max_zoom', type=int, required=False,
                        help='Heatmap max zoom', default=4)
    parser.add_argument('-mt', '--map_tiles', dest='tiles', type=str, required=False,
                        help='Map tileset to use', default='OpenStreetMap')
    parser.add_argument('-mv', '--max_value', dest='max_value', type=str, required=False,
                        help='Max magnitude value')

    args = parser.parse_args()

    print("\nHeatmap setting:")
    print('-' * 50)
    for i in vars(args):
        print(str(i) + ' - ' + str(getattr(args, i)))

    print('-' * 50)

    try:
        location = [float(i) for i in args.map_location]

        for_map = pd.read_csv(args.csv, sep=';')

        max_amount = float(args.max_value) if args.max_value else float(for_map['magnitude'].max())
        hmap = folium.Map(location=location,
                          zoom_start=args.map_zoom_start,
                          tiles=args.tiles)

        hmap_data = [[row['lat'], row['lon'], row['magnitude']] for index, row in for_map.iterrows()]

        hm = folium.plugins.HeatMap(hmap_data,
                                    max_val=max_amount,
                                    min_opacity=args.heatmap_min_opocity,
                                    radius=args.heatmap_radius,
                                    blur=args.heatmap_blur,
                                    max_zoom=args.heatmap_max_zoom)

        hmap.add_child(hm)

        hmap.save(args.output)

        print('Output: %s' % args.output)
    except:
        import traceback
        print('Error occurred!')
        print(traceback.format_exc())
