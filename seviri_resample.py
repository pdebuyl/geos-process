import satpy
import pyresample
import numpy as np
import argparse

SEVIRI_CHANNELS = ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087',
                   'IR_097', 'IR_108', 'IR_120', 'IR_134']

parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='+')
parser.add_argument('--reader', default='seviri_l1b_native')
parser.add_argument('--out', required=True)
args = parser.parse_args()

sev_scene = satpy.Scene(reader=args.reader, filenames=args.input)
sev_scene.load(SEVIRI_CHANNELS)

projection = {'proj': 'latlong', 'datum': 'WGS84'}

ad = pyresample.AreaDefinition("euro_eqc", "lat/lon over Europe", "eqc",
                               width=2000, height=1000, projection=projection,
                               area_extent=(-60, 20, 40, 70))
ss_scene = sev_scene.resample(ad)

ss_scene.save_datasets(writer='cf', datasets=SEVIRI_CHANNELS, filename=args.out, exclude_attrs=['raw_metadata'], include_lonlats=False)

