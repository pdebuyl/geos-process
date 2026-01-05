import pathlib
import hdf5plugin
import argparse
import pyresample
import glob
import numpy as np
import os

parser = argparse.ArgumentParser()
parser.add_argument('--slot', required=True)
parser.add_argument('--composite', default='ash')
parser.add_argument('--out', default='.')
parser.add_argument('--config', required=True)
parser.add_argument('--region', required=True)
args = parser.parse_args()

if args.config.startswith('/'):
    os.environ['SATPY_CONFIG_PATH'] = args.config
else:
    etc = pathlib.Path(__file__).parent / args.config
    os.environ['SATPY_CONFIG_PATH'] = etc.as_posix()

import satpy
from satpy import Scene

fnames = glob.glob('/home/pierre/RS_DATA/MTG/MTI1_202503101400/W*FCI*RAD*BODY*.nc')
print(len(fnames), "files found")

ad = pyresample.load_area("RSS_areas.yaml", args.region)

scn = Scene(reader='fci_l1c_nc', filenames=fnames)
print("scene read")
scn.load([args.composite], upper_right_corner='NE')
print("scene loaded")

euro_scn = scn.resample(ad, resampler='gradient_search', radius_of_influence=50000)
euro_scn.load([args.composite])
euro_scn.save_datasets(
    filename=args.out+"_MTI1_{name}_{start_time:%Y%m%d%H%M}_"+args.region+".png",
)

