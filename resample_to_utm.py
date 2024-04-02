#!/usr/bin/env python3
"""Resample geostationary satellite data to UTM vignettes

Author: Pierre de Buyl
Status: draft
"""

import argparse
import cartopy
from glob import glob
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import pyresample
import satpy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('glob', help="glob pattern for input data")
parser.add_argument('--reader', help="Satpy reader name", default="seviri_l1b_hrit")
args = parser.parse_args()


# Load one channel of SEVIRI
composite = 'ash'

scn = satpy.Scene(reader=args.reader, filenames=glob(args.glob))
scn.load([composite])

if composite not in ['natural_color', 'ash']:
    vmin = float(scn[composite].min().compute())
    vmax = float(scn[composite].max().compute())
else:
    vmin = None
    vmax = None

def zone_from_lon(lon):
    """Return UTM zone."""
    if lon < -180 or lon >=180:
        raise ValueError("Invalid input longitude")
    return int((lon+180)/6) + 1

def restack(data):
    """Change a NumPy array from the shape [3,Nx,Ny] to [Nx,Ny,3]

    This is necessary for displaying the array as a color image with matplotlib.
    """
    if data.shape[0] == 3:
        s = []
        for i in range(3):
            x = data[i,:,:]
            x_min = x.min()
            x_max = x.max()
            x = (x-x_min)/(x_max-x_min)
            s.append(x)
        data = np.dstack(s)
    else:
        data = scn_ad[composite]
    return data

def restack_ash(data):
    """Change a NumPy array from the shape [3,...] to [...,3] and set range to (0,1)

    Only suitable for the ASH RGB composite
    """
    ranges = [(-4,2), (-4,+5), (243, 303)]
    s = []
    for i in range(3):
        x_min, x_max = ranges[i]
        x = np.clip(data[i,:,:], x_min, x_max)
        x = (x-x_min)/(x_max-x_min)
        s.append(x)
    data = np.dstack(s)
    return data

# ash: -4,+2 -4,+5 243,303

lons = np.linspace(-60, 40, 21)[:-1]
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

    w = h = 281
    ad = pyresample.geometry.AreaDefinition('myUTM', 'UTM test zone', 'myUTM', f"+proj=utm +zone={zone}", w, h,
                                            area_extent)

    scn_ad = scn.resample(ad)
    scn_ad.load([composite])

    params = {
        'figure.figsize': (1, 1),
        'figure.subplot.left' : 0.,
        'figure.subplot.right' : 1.,
        'figure.subplot.bottom' : 0.,
        'figure.subplot.top' : 1.,
        'figure.dpi': w,
    }
    plt.rcParams.update(params)

    plt.clf()
    plt.gcf().add_subplot(aspect=1)
    if vmin is not None and vmax is not None:
        plt.imshow(scn_ad[composite], vmin=vmin, vmax=vmax)
    elif composite == 'ash':
        data = restack_ash(scn_ad[composite])
        plt.imshow(data)
    else:
        data = restack(scn_ad[composite])
        plt.imshow(data)

    if degree_area:
        plt.savefig(f"/tmp/tiles/EC_{composite}_DEG_{90-lat}_{180+lon}.png")
    else:
        plt.savefig(f"/tmp/tiles/EC_{composite}_DIS_{90-lat}_{180+lon}.png")

if 0:
    plot_crs = ad.to_cartopy_crs()
    ax = plt.axes(projection=ad.to_cartopy_crs())
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    plt.imshow(scn_ad[composite], transform=plot_crs, extent=plot_crs.bounds, origin='upper')
    plt.colorbar()
    plt.show()
