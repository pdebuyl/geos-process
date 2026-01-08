import argparse
import glob
import hdf5plugin
import os
import pathlib
import pyresample

def custom_ash(input_scene, query_dict, standard_name='ash'):
    """
    Create a custom ash composite based on the DataQuery entries in `query_dict`.
    """

    ash_r_compositor = satpy.composites.arithmetic.DifferenceCompositor("ash_r")
    ash_g_compositor = satpy.composites.arithmetic.DifferenceCompositor("ash_g")
    ash_compositor = satpy.composites.core.GenericCompositor("ash")

    r = ash_r_compositor([input_scene[queries['r'][0]], input_scene[queries['r'][1]]])
    g = ash_g_compositor([input_scene[queries['g'][0]], input_scene[queries['g'][1]]])
    b = input_scene[queries['b'][0]]

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
args = parser.parse_args()

etc = pathlib.Path(__file__).parent / 'etc_custom_ash_wmo'
os.environ['SATPY_CONFIG_PATH'] = etc.as_posix()

import satpy
import satpy.composites.arithmetic

# Define area definition for region of interest
ad = pyresample.load_area("/home/pierre/code/geos-process/RSS_areas.yaml", args.region)

# Create queries per RGB channel and wavelength
queries = {'r': [], 'g': [], 'b': []}
ash_wl = {'r': (12.3, 10.5), 'g': (10.5, 8.7), 'b': (10.5,)}
for channel in ash_wl.keys():
    for wl, resolution in zip(ash_wl[channel], getattr(args, channel)):
        q = satpy.DataQuery(wavelength=wl, resolution=resolution)
        queries[channel].append(q)

# Create the scene, load the queries, resample, and call the custom ash composite
fn = glob.glob(args.data + '/W*FCI*BODY*.nc')
scn = satpy.Scene(filenames=fn, reader='fci_l1c_nc')
scn.load([*queries['r'], *queries['g'], *queries['b']])
scn_2 = scn.resample(ad, resampler='gradient_search')
scn_2['ash'] = custom_ash(scn_2, queries, args.standard_name)

scn_2.save_dataset('ash', writer='simple_image', filename=args.out)
