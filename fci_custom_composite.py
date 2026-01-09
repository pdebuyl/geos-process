import argparse
import glob
import hdf5plugin
import json
import os
import pathlib
import pyresample
import xarray as xr


def sbaf_single(band, coefs):
    """
    Apply a polynomial SBAF correction.
    """
    data = coefs[1]*band.data + coefs[0]
    for i, coef in enumerate(coefs[2:]):
        data += coef*band.data**(i+2)
    res = xr.DataArray(data, dims=band.dims, attrs=band.attrs, coords=band.coords)
    return res


def custom_ash(input_scene, query_dict, standard_name='ash', sbaf_coefs=None):
    """
    Create a custom ash composite based on the DataQuery entries in `query_dict`.
    """

    ash_r_compositor = satpy.composites.arithmetic.DifferenceCompositor("ash_r")
    ash_g_compositor = satpy.composites.arithmetic.DifferenceCompositor("ash_g")
    ash_compositor = satpy.composites.core.GenericCompositor("ash")

    r_123 = input_scene[queries['r'][0]]
    r_105 = input_scene[queries['r'][1]]
    g_105 = input_scene[queries['g'][0]]
    g_087 = input_scene[queries['g'][1]]
    b_105 = input_scene[queries['b'][0]]
    if sbaf_coefs is not None:
        r_123 = sbaf_single(r_123, sbaf_coefs['ir_123'])
        r_105 = sbaf_single(r_105, sbaf_coefs['ir_105'])
        g_105 = sbaf_single(g_105, sbaf_coefs['ir_105'])
        g_087 = sbaf_single(g_087, sbaf_coefs['ir_87'])
        b_105 = sbaf_single(b_105, sbaf_coefs['ir_105'])
    r = ash_r_compositor([r_123, r_105])
    g = ash_g_compositor([g_105, g_087])
    b = b_105

    ash = ash_compositor([r, g, b])
    ash.attrs['standard_name'] = standard_name

    return ash


parser = argparse.ArgumentParser()
parser.add_argument('-r', nargs=2, default=(2000, 2000), type=int)
parser.add_argument('-g', nargs=2, default=(1000, 2000), type=int)
parser.add_argument('-b', nargs=1, default=(1000,), type=int)
parser.add_argument('--out', required=True)
parser.add_argument('--data', required=True)
parser.add_argument('--region', default='econtrail_002')
parser.add_argument('--standard-name', default='ash')
parser.add_argument('--sbaf', action='store_true')
args = parser.parse_args()

etc = pathlib.Path(__file__).parent / 'etc_custom_ash_wmo'
os.environ['SATPY_CONFIG_PATH'] = etc.as_posix()

import satpy
import satpy.composites.arithmetic
import satpy.modifiers
import geos_utils


# Define area definition for region of interest
ad = pyresample.load_area("RSS_areas.yaml", args.region)
if args.sbaf:
    with open("goes_fci_ash_bands.json", 'r') as f:
        coefs = json.load(f)
else:
    coefs = None

# Create queries per RGB channel and wavelength
queries = {'r': [], 'g': [], 'b': []}
ash_wl = {'r': (12.3, 10.5), 'g': (10.5, 8.7), 'b': (10.5,)}
ash_name = {'r': ('ir_123', 'ir_105'), 'g': ('ir_105', 'ir_87'), 'b': ('ir_105',)}
for channel in ash_name.keys():
    for name, resolution in zip(ash_name[channel], getattr(args, channel)):
        q = satpy.DataQuery(name=name, resolution=resolution)
        queries[channel].append(q)

# Create the scene, load the queries, resample, and call the custom ash composite
fn = glob.glob(args.data + '/W*FCI*BODY*.nc')
scn = satpy.Scene(filenames=fn, reader='fci_l1c_nc')

scn.load([*queries['r'], *queries['g'], *queries['b']])
scn_2 = scn.resample(ad, resampler='gradient_search')
scn_2['ash'] = custom_ash(scn_2, queries, args.standard_name, sbaf_coefs=coefs)

scn_2.save_dataset('ash', writer='simple_image', filename=args.out)
