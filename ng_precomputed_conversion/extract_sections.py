import os
from PIL import Image, ImageSequence
from multiprocessing import Pool
from tqdm import tqdm
import time
#import cv2
import tifffile
import numpy as np

# Set the maximum number of pixels to allow processing of very large images
Image.MAX_IMAGE_PIXELS = 100_000 * 100_000

def extract_subportion(args):
    image_path, output_path, x_fraction, y_fraction, convert_to_uint32, index = args
    try:
        # Load indexed image if it's a single-file TIFF
        if os.path.isfile(image_path):
            with tifffile.TiffFile(image_path) as tif:
                if len(tif.pages) == 1:  # Check if it's a single page TIFF
                    img = tif.pages[0].asarray()
                else:  # Load specific index if it's a multi-page TIFF
                    img = tif.pages[index].asarray()
        else:
            # Fall back to regular loading
            img = tifffile.imread(image_path)

        # Convert the image to uint32 if requested
        if convert_to_uint32:
            img = img.astype(np.uint32)
        
        # Calculate crop coordinates
        height, width = img.shape[:2]
        new_width = int(width * x_fraction)
        new_height = int(height * y_fraction)
        left = (width - new_width) // 2
        upper = (height - new_height) // 2
        right = left + new_width
        lower = upper + new_height

        # Perform cropping
        cropped_img = img[upper:lower, left:right]

        # Save cropped image
        cv2.imwrite(output_path, cropped_img)

        return True
    except Exception as e:
        print(f"Error processing {os.path.basename(image_path)}: {e}")
        return False

def extract_subportion_pil(args): # pillow doesn't have support for uint32?
    image_path, output_path, x_fraction, y_fraction, convert_to_uint32, index = args
    print(convert_to_uint32)
    try:
        with Image.open(image_path) as img:
            if img.format == 'TIFF' and img.is_animated:  # Check if it's a multi-image TIFF
                img.seek(index)
            # Convert the image to uint32 if requested
            if convert_to_uint32:
                # Ensure the image is in a mode that can be converted to 'I'
                if img.mode not in ['I', 'I;32']:
                    img = img.convert('I')
            width, height = img.size
            new_width = int(width * x_fraction)
            new_height = int(height * y_fraction)
            left = (width - new_width) // 2
            upper = (height - new_height) // 2
            right = left + new_width
            lower = upper + new_height

            cropped_img = img.crop((left, upper, right, lower))
            cropped_img.save(output_path)
            return True
    except Exception as e:
        print(f"Error processing {os.path.basename(image_path)}: {e}")
        return False
def extract_subportion_pil_xy(args): # specify minX minY width height
    image_path, output_path, minX, minY, width, height, convert_to_uint32, index = args
    try:
        with Image.open(image_path) as img:
            if img.format == 'TIFF' and img.is_animated:  # Check if it's a multi-image TIFF
                img.seek(index)
            # Convert the image to uint32 if requested
            if convert_to_uint32:
                # Ensure the image is in a mode that can be converted to 'I'
                if img.mode not in ['I', 'I;32']:
                    img = img.convert('I')
            left = minX
            upper = minY
            right = minX+width
            lower = minY+height
            cropped_img = img.crop((left, upper, right, lower))
            cropped_img.save(output_path)
            return True
    except Exception as e:
        print(f"Error processing {os.path.basename(image_path)}: {e}")
        return False

def process_subvolume(tasks, n_processes):
    with Pool(n_processes) as pool:
        with tqdm(total=len(tasks), desc="Extracting Subvolume") as pbar:
            results = [pool.apply_async(extract_subportion_pil_xy, args=(task,), callback=lambda x: pbar.update()) for task in tasks]
            pool.close()
            pool.join()

def extract_subvolume(input_path, output_path, minX, minY, width, height, n_processes, start_section=None, end_section=None, convert_to_unit32 = False):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if os.path.isdir(input_path):
        images = sorted([img for img in os.listdir(input_path) if img.endswith('.tif')])
        start_index = start_section if start_section is not None else 0
        end_index = end_section if end_section is not None else len(images)
        tasks = [(os.path.join(input_path, images[i]), os.path.join(output_path, f"subvolume_{images[i]}"), minX, minY, width, height, convert_to_unit32, None)
                 for i in range(start_index, end_index)]
    elif os.path.isfile(input_path):
        img = Image.open(input_path)
        total_frames = img.n_frames if hasattr(img, 'n_frames') else 1
        start_index = start_section if start_section is not None else 0
        end_index = end_section if end_section is not None else total_frames
        tasks = [(input_path, os.path.join(output_path, f"subvolume_{i:04d}.tif"), minX, minY, width, height,  convert_to_uint32, i)
                 for i in range(start_index, end_index)]
    else:
        print('Problem with path %s ' % input_path)
        return
    process_subvolume(tasks, n_processes)

subvolume_spec = (0.1, 0.1)  # x_fraction, y_fraction

output_path = '/home/atk42/kuan_lab_gibbs/exm/ms7e_iv_20x_tifflist_subset/'

# Optional: specify start_section and end_section
start_section = 0
end_section = 1246
minX = 4500
minY = 4500
width = 512 #9466
height = 512 #9522


convert_to_uint32 = False
n_processes = 1

print('loaded modules')
start_time = time.time()
extract_subvolume(input_path, output_path, minX, minY, width, height, n_processes, start_section, end_section+1, convert_to_uint32)
end_time = time.time()

print("Total time taken:", end_time - start_time, "seconds")
                                                                  


