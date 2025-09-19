#!/usr/bin/env python3

# This script based on example from https://github.com/seung-lab/cloud-volume/wiki/Example-Single-Machine-Dataset-Upload
import os
from concurrent.futures import ProcessPoolExecutor
import xml.etree.ElementTree as ET
import numpy as np
import tifffile as tf
import datetime
from cloudvolume import CloudVolume
from cloudvolume.lib import mkdir, touch

chunk_size = 16

input_file = '/vast/palmer/pi/kuan/exm/ms7e_iv_20x_FusionStitcher.ome.tiff'
output_path = mkdir('/vast/palmer/scratch/kuan/atk42/exm/ms7e_iv_20x_tifflist_subset/') # unlike os.mkdir doesn't crash on prexisting 

# Define the region you want to extract as a subset (e.g., [slice(0, 100), slice(0, 100), slice(0, 10)])
region = (slice(0, 4096), slice(2000, 6096), slice(0, 105))  # Adjust this as needed


def parse_ome_metadata(metadata):
    """Extract useful information from the OME metadata."""
    root = ET.fromstring(metadata)
    namespaces = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
    x_size = int(root.find('.//ome:Pixels', namespaces).get('SizeX'))
    y_size = int(root.find('.//ome:Pixels', namespaces).get('SizeY'))
    z_size = int(root.find('.//ome:Pixels', namespaces).get('SizeZ'))
    c_size = int(root.find('.//ome:Pixels', namespaces).get('SizeC'))
    t_size = int(root.find('.//ome:Pixels', namespaces).get('SizeT'))
    return x_size, y_size, z_size, c_size, t_size

# Load metadata to get dataset size
with tf.TiffFile(input_file) as tif: # Read OME metadata
    ome_metadata = tif.ome_metadata
    x_size, y_size, z_size, num_chan, t_size = parse_ome_metadata(ome_metadata)
    print(f"Image dimensions (X, Y, Z, Channels, Timepoints): ({x_size}, {y_size}, {z_size}, {num_chan}, {t_size})")    
        
z_size = chunk_size  # FOR TESTING

z_starts = range(0,z_size, chunk_size) # first and last section index 
print(z_size)

# Adjust z_size to be multiples of chunk_size
z_size_padded = z_size + (chunk_size - (z_size % chunk_size)) % chunk_size

info = CloudVolume.create_new_info(
	num_channels = num_chan,
	layer_type = 'image', # 'image' or 'segmentation'
	data_type = 'uint16', # can pick any popular uint
	encoding = 'raw', # see: https://github.com/seung-lab/cloud-volume/wiki/Compression-Choices
        resolution = [ 5, 5, 25 ], # X,Y,Z values in nanometers
	voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
	chunk_size = [ chunk_size, chunk_size, chunk_size], # rechunk of image X,Y,Z in voxels
	volume_size = [ x_size, y_size, z_size_padded], # X,Y,Z size in voxels
)

####### Should not need to edit beyond here

# If you're using amazon or the local file system, you can replace 'gs' with 's3' or 'file'
#vol = CloudVolume('gs://bucket/dataset/layer', info=info)
vol = CloudVolume('file://' + output_path, info=info, compress=False,)
vol.provenance.description = "Test"
vol.provenance.owners = ['aaron.kuan@yale.edu'] # list of contact email addresses

vol.commit_info() # generates gs://bucket/dataset/layer/info json file
vol.commit_provenance() # generates gs://bucket/dataset/layer/provenance json file

def process_chunk_multichan(z_start):
    for chan_idx in range(num_chan):
        z_end = min(z_start + chunk_size, z_size)
        z_start_chan = z_start + z_size * chan_idx
        z_end_chan = min(z_start_chan + chunk_size, z_size+chan_idx*z_size)
        print(f'Processing z slices {z_start_chan} to {z_end_chan - 1} (chan {chan_idx})')
        print(datetime.datetime.now())
        chunk = np.zeros((x_size, y_size, chunk_size, num_chan), dtype=np.uint16)
        # Open the OME-TIFF file in 'rb' mode to avoid loading the entire stack
        with tf.TiffFile(input_file) as tif:
            slice_range = tif.asarray(key=slice(z_start_chan, z_end_chan))
        slice_range = np.swapaxes(slice_range,0,2)
        print(slice_range.shape)
        # Insert the image into the correct position within the padded chunk
        chunk[:,:,z_start:z_end,chan_idx] = slice_range

    print(chunk.shape)
    vol[:, :, z_start:z_start + chunk_size,:] = chunk

def process_chunk(z_start):
    z_end = min(z_start + chunk_size, z_size)
    print(datetime.datetime.now())
    print(f'Processing z slices {z_start} to {z_end - 1}')
    
    chunk = np.zeros((x_size, y_size, chunk_size), dtype=np.uint16)
    
    # Open the OME-TIFF file in 'rb' mode to avoid loading the entire stack
    with tf.TiffFile(input_file) as tif:
        # Alternatively, you can specify a range of slices:
        slice_range = tif.asarray(key=slice(z_start, z_end+1))  # Loads slices 10 to 19
    
    slice_range = np.squeeze(slice_range[1,:,:,:]) # for testing squeeze only channel 1

    #for i, z in enumerate(range(z_start, z_end)):
    #    img_name = f'{file_header}{z:05d}.tif'
    #    print('Reading ', img_name)
    #    image = tifffile.imread(os.path.join(input_dir, img_name))
    #    image = np.swapaxes(image, 0, 1)
        
        # Insert the image into the correct position within the padded chunk
        # chunk[:image.shape[0], :image.shape[1], i] = image
    
    # Insert the image into the correct position within the padded chunk
    chunk[:slice_range.shape[0], :slice_range.shape[1], z_start:z_end] = slice_range
    
    if z_end - z_start < chunk_size:  # Padding in the Z dimension if necessary
        chunk[:, :, z_end - z_start:] = 0
    
    chunk = chunk[..., np.newaxis]  # Add channel dimension
    print(chunk.size)
    print(z_start)
    print(z_start + chunk_size)
    vol[:, :, z_start:z_start + chunk_size] = chunk
    
    # Insert the image into the correct position within the padded chunk
    #vol[:, :, z_start:z_start + chunk_size] = slice_range

    print(datetime.datetime.now())    
    #for z in range(z_start, z_end):
    #    touch(os.path.join(progress_dir, str(z)))

process_chunk_multichan(0)
#if __name__ == "__main__":
#    with ProcessPoolExecutor(max_workers=1) as executor:
#        executor.map(process_chunk, z_starts)

print('Done')
