#!/usr/bin/env python3
"""Resample geostationary satellite data to UTM vignettes

Author: Pierre de Buyl
Status: draft
"""

import argparse
import cartopy
from glob import glob
import h5py
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import pyresample
import satpy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', help="filename or glob pattern for input data")
parser.add_argument('--output', help="Start of path for output data")
parser.add_argument('--reader', help="Satpy reader name", default="seviri_l1b_hrit")
parser.add_argument('--channels', help="Channels to load", nargs='+')
parser.add_argument('--lon0', help="Central longitude of area", type=float, default=-10.)
args = parser.parse_args()


scn = satpy.Scene(reader=args.reader, filenames=glob(args.input))
scn.load(args.channels)

def zone_from_lon(lon):
    """Return UTM zone."""
    if lon < -180 or lon >=180:
        raise ValueError("Invalid input longitude")
    return int((lon+180)/6) + 1

lons = np.linspace(-50, 50, 21)[:-1] + args.lon0
lats = np.linspace(20, 70, 11)[::-1][:-1]
all_ll = list(itertools.product(lons, lats))

degree_area = False

for i in range(len(all_ll)):

    lon, lat = all_ll[i]

    zone = zone_from_lon(lon)
    area_ll = (lon, lat-5, lon+5, lat)
    crs = pyproj.CRS.from_proj4(f"+proj=utm +zone={zone}")

    proj = pyproj.Transformer.from_crs(crs.geodetic_crs, crs)

    lower_left = proj.transform(area_ll[0], area_ll[1])
    upper_right = proj.transform(area_ll[2], area_ll[3])
    if degree_area:
        area_extent = (lower_left[0], lower_left[1], upper_right[0], upper_right[1])
    else:
        area_extent = (lower_left[0], lower_left[1], lower_left[0]+5e5, lower_left[1]+5e5)

    print(f"{zone=} {area_ll=}")

    w = h = 256
    ad = pyresample.geometry.AreaDefinition('myUTM', 'UTM test zone', 'myUTM', f"+proj=utm +zone={zone}", w, h,
                                            area_extent)

    scn_ad = scn.resample(ad)
    scn_ad.load(args.channels)

    output = f"{args.output}_DEG_{90-lat}_{180+lon}.h5"

    with h5py.File(output, 'w') as out:
        for c in args.channels:
            out[c] = scn_ad[c]

