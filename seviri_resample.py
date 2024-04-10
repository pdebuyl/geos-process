import satpy
import pyresample
import numpy as np
import argparse
import h5py
import xarray as xr

satpy.config.set(tmp_dir='/tmp')

SEVIRI_CHANNELS = ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_087',
                   'IR_097', 'IR_108', 'IR_120', 'IR_134']

ASH_CHANNELS = ['ash_red', 'ash_green', 'ash_blue']

parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='+')
parser.add_argument('--reader', default='seviri_l1b_native')
parser.add_argument('--ash', action='store_true')
parser.add_argument('--cobra')
parser.add_argument('--out')
args = parser.parse_args()

sev_scene = satpy.Scene(reader=args.reader, filenames=args.input)
if args.ash:
    SEVIRI_CHANNELS = SEVIRI_CHANNELS + ASH_CHANNELS

sev_scene.load(SEVIRI_CHANNELS)

sev_scene['ash_red'].data = ( (sev_scene['ash_red'].data + 4)/6 * 255).clip(0, 255).astype(np.uint8)
sev_scene['ash_green'].data = ( (sev_scene['ash_green'].data + 4)/9 * 255).clip(0, 255).astype(np.uint8)
sev_scene['ash_blue'].data = ( (sev_scene['ash_blue'].data - 243)/(303.-243.) * 255).clip(0, 255).astype(np.uint8)

if args.cobra:
    # add extra component
    copy_attrs = {'start_time': sev_scene['VIS006'].attrs['start_time'], 'area': sev_scene['VIS006'].attrs['area'], 'standard_name': 'COBRA Ice'}
    with h5py.File(args.cobra, 'r') as a:
        sev_scene['COBRA_Ice'] = xr.DataArray(a['Data Fields/Ice'][...], attrs=copy_attrs, dims=sev_scene['VIS006'].dims)
    SEVIRI_CHANNELS += ['COBRA_Ice']

projection = {'proj': 'latlong', 'datum': 'WGS84'}

ad = pyresample.AreaDefinition("euro_eqc", "lat/lon over Europe", "eqc",
                               width=2500, height=1250, projection=projection,
                               area_extent=(-60, 20, 40, 70))
ss_scene = sev_scene.resample(ad)

if args.out:
    ss_scene.save_datasets(writer='cf', datasets=SEVIRI_CHANNELS, filename=args.out, exclude_attrs=['raw_metadata'], include_lonlats=False)
elif args.ash:
    ss_scene.show(ASH_CHANNELS[0])
else:
    ss_scene.show(SEVIRI_CHANNELS[0])

