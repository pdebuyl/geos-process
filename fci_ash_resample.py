import satpy
import pyresample
import numpy as np
import argparse
from glob import glob
from satpy.writers import get_enhanced_image
import xarray as xr

FCI_IR_CHANNELS = [ 'ir_105', 'ir_123', 'ir_133', 'ir_38', 'ir_87', 'ir_97', 'nir_13',
                 'nir_16', 'nir_22', 'wv_63', 'wv_73' ]

FCI_VIS_CHANNELS = [ 'vis_04', 'vis_05', 'vis_06', 'vis_08', 'vis_09' ]

ASH_CHANNELS = ['ash_red', 'ash_green', 'ash_blue']

parser = argparse.ArgumentParser()
parser.add_argument('--composite', default='natural_color')
parser.add_argument('--dir', default='.')
parser.add_argument('--out', required=True)
parser.add_argument('--resampler', default='nearest')
parser.add_argument('--region', required=True)
parser.add_argument('--utm_lon0', type=float)
parser.add_argument('--utm_side', choices=["left", "right"])
args = parser.parse_args()

if False:
    assert args.utm_lon0 is not None
    assert args.utm_side is not None

ad = pyresample.load_area("RSS_areas.yaml", args.region)

filenames = glob(args.dir+"/W*FDHSI*BODY*.nc")

scene = satpy.Scene(reader="fci_l1c_nc", filenames=filenames)

scene.load(FCI_IR_CHANNELS, upper_right_corner='NE')
scene.load([args.composite], upper_right_corner='NE')

ss_scene = scene.resample(ad, resampler=args.resampler, radius_of_influence=5000)

ss_scene.load(FCI_IR_CHANNELS+[args.composite])

if args.out:
    ss_scene.save_dataset(args.composite, filename=f"{args.out}_{args.region}.png")

#im = get_enhanced_image(ss_scene[args.composite])
#data, mode = im.finalize()
#data_t = data.transpose('y', 'x', 'bands')

#ss_scene[args.composite].data = data[:3,:,:]

# copy_attrs = {'start_time': ss_scene['ir_105'].attrs['start_time'], 'area': ss_scene['ir_105'].attrs['area'], 'standard_name': 'ash_red'}
# ss_scene['ash_red'] = xr.DataArray(data_t[:,:,0], attrs=copy_attrs, dims=ss_scene['ir_105'].dims)
# copy_attrs['standard_name'] = 'ash_green'
# ss_scene['ash_green'] = xr.DataArray(data_t[:,:,1], attrs=copy_attrs, dims=ss_scene['ir_105'].dims)
# copy_attrs['standard_name'] = 'ash_blue'
# ss_scene['ash_blue'] = xr.DataArray(data_t[:,:,2], attrs=copy_attrs, dims=ss_scene['ir_105'].dims)


if args.out:
    ss_scene.save_datasets(writer='cf', datasets=FCI_IR_CHANNELS+[args.composite],
                           filename=f"{args.out}_{args.region}.nc", exclude_attrs=['raw_metadata'], include_lonlats=False)
