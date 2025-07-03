import satpy
import pyresample
import numpy as np
import argparse
import h5py
import xarray as xr
import itertools
import pyproj

#satpy.config.set(config_path=['./etc'])
satpy.config.set(tmp_dir='/tmp')

SEVIRI_CHANNELS = ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087',
                   'IR_097', 'IR_108', 'IR_120', 'IR_134']

ASH_CHANNELS = ['ash_red', 'ash_green', 'ash_blue']

parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='+')
parser.add_argument('--reader', default='seviri_l1b_native')
parser.add_argument('--ash', action='store_true')
parser.add_argument('--create-lat-lon', action='store_true')
parser.add_argument('--grid002', action='store_true')
parser.add_argument('--cobra')
parser.add_argument('--lon0', help="Central longitude of area for UTM vignetting", type=float, default=-10.)
parser.add_argument('--utm', action='store_true')
parser.add_argument('--out')
args = parser.parse_args()

sev_scene = satpy.Scene(reader=args.reader, filenames=args.input)
if args.ash:
    SEVIRI_CHANNELS = SEVIRI_CHANNELS + ASH_CHANNELS

sev_scene.load(ASH_CHANNELS, upper_right_corner='NE')

sev_scene['ash_red'].data = ( (sev_scene['ash_red'].data + 4)/6 * 255).clip(0, 255).astype(np.uint8)
sev_scene['ash_green'].data = ( (sev_scene['ash_green'].data + 4)/9 * 255).clip(0, 255).astype(np.uint8)
sev_scene['ash_blue'].data = ( (sev_scene['ash_blue'].data - 243)/(303.-243.) * 255).clip(0, 255).astype(np.uint8)

if args.cobra:
    # add extra component
    copy_attrs = {'start_time': sev_scene['VIS006'].attrs['start_time'], 'area': sev_scene['VIS006'].attrs['area'], 'standard_name': 'COBRA Ice'}
    with h5py.File(args.cobra, 'r') as a:
        sev_scene['COBRA_Ice'] = xr.DataArray(a['Data Fields/Ice'][...], attrs=copy_attrs, dims=sev_scene['VIS006'].dims)
    SEVIRI_CHANNELS += ['COBRA_Ice']


# Resampling on a regular lat-lon grid

projection = {'proj': 'latlong', 'datum': 'WGS84'}

w = 2500
h = 1250
if args.grid002:
    w *= 2
    h *= 2

ad = pyresample.AreaDefinition("euro_eqc", "lat/lon over Europe", "eqc",
                               width=w, height=h, projection=projection,
                               area_extent=(-60, 20, 40, 70))
ss_scene = sev_scene.resample(ad)

if args.out:
    ss_scene.save_datasets(writer='cf', datasets=ASH_CHANNELS, filename=args.out+".nc", exclude_attrs=['raw_metadata'], include_lonlats=False)
elif args.ash:
    ss_scene.show(ASH_CHANNELS[0])
else:
    ss_scene.show(SEVIRI_CHANNELS[0])


def zone_from_lon(lon):
    """Return UTM zone."""
    if lon < -180 or lon >=180:
        raise ValueError("Invalid input longitude")
    return int((lon+180)/6) + 1

lons = np.linspace(-50, 50, 21)[:-1] + args.lon0
lats = np.linspace(20, 70, 11)[::-1][:-1]
all_ll = list(itertools.product(lons, lats))

if args.utm:
  for i in range(len(all_ll)):

    lon, lat = all_ll[i]

    zone = zone_from_lon(lon)
    area_ll = (lon, lat-5, lon+5, lat)
    crs = pyproj.CRS.from_proj4(f"+proj=utm +zone={zone}")

    proj = pyproj.Transformer.from_crs(crs.geodetic_crs, crs)

    lower_left = proj.transform(area_ll[0], area_ll[1])
    upper_right = proj.transform(area_ll[2], area_ll[3])
    area_extent = (lower_left[0], lower_left[1], lower_left[0]+5e5, lower_left[1]+5e5)

    print(f"Resampling for {zone=} {area_ll=}")

    w = h = 256
    ad = pyresample.geometry.AreaDefinition('myUTM', 'UTM zone', 'myUTM', f"+proj=utm +zone={zone}", w, h,
                                            area_extent)

    utm_scene = sev_scene.resample(ad)
    utm_scene.load(SEVIRI_CHANNELS)

    output = f"{args.out}_UTM_{90-lat}_{180+lon}.h5"

    print(f"Writing UTM sample to {output}")
    with h5py.File(output, 'w') as out:
        for c in SEVIRI_CHANNELS:
            out[c] = utm_scene[c]

    if args.create_lat_lon:
        output = f"{args.out}_DEG_{90-lat}_{180+lon}_latitude_longitude.h5"
        lons, lats = ad.get_lonlats()
        with h5py.File(output, 'w') as out:
            out['longitude'] = lons
            out['latitude'] = lats

