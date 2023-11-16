#%%
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
#This scripts registers (aligns) all the images in a stack, to correct for sample drift during the experiment.
# By default, registration is based on the elemental maps of Mn_Ka
# It uses three different strategies for registration
# (1) Cross correlation by openCVs findTransformECC()
# If (1) does not converge, the script looks for the files points1.csv and points2.csv. These should contain coordinates of points
# on two successive images, that are determined to be the same sample coordinate. This is strategy (2).
# Based on the points1 and point2, we calculate an initial guess for the transformation matrix that is then fed to the findTransformECC algorithm()
#If (1) still fails, the initial guess is used for the final transform.
# If (1) fails, and there are no points1 and points2 files, it falls back to the 3rd option
# (3) Using feature detection with openCV ORB detection. The transform found by this method is then fed to (1)
# If (1) fails when being fed with the transform from (3) the script does not align the stack and produces an error.

# Finally, the transformations are applied to pixel_times and pixel_heating_times as well.

# stack_registration()
# cross_correlation()
# manual_points()
# ORB()
# concat_transforms()
# register_stack()
import cv2
from typing import List, Dict
import pymongo
import h5py
import matplotlib.pyplot as plt

from PIL import Image
import numpy as np
def preprocess(img, vmin=None, vmax=None): 
    img = img.copy()
    if (vmin is not None) and (vmax is not None):
        #scale to contrast provided by vmin and vmax
        img[img>vmax] =vmax
        img[img < vmin] = vmin
        img = img -vmin #values start at 0

    else:
        #scale intensities to +- 2*std from mean
        l = 2
    
        mu = np.mean(img)
        std = img.std()
        img[img < mu-l*std] = mu -l*std
        img[img > mu +l*std] = mu + l*std
        img = img-img.min()


    
    

    
    
    img = np.round(255*img/img.max()).astype(np.uint8) # scale to 255 values and convert to uint8
    
    return img


def crop_nans(stack: np.ndarray) -> np.ndarray:
    """Checks if any of the images in the stack are padded with NaN values. 
    If so, crops all stacks to eliminate them. Returns a stack where all images have the same shape.
    
    Args:
    - stack : (np.ndarray) : list of arrays all of the same shape. 
    
    Returns:
    - cropped_stack : (np.ndarray) : list of arrays where none of them are padded with nan values. 
    All arrays have the same shape.
    """

    # Initialize min/max indices for rows and columns for each array
    rows_min, rows_max = [], []
    cols_min, cols_max = [], []
    print(f'initial shape: {stack.shape}')
    # Find the bounding box of non-NaN values for each array
    for array in stack:
        # Get indices where the array is not NaN
        not_nan_indices = np.argwhere(~np.isnan(array))
        
        # Find the min/max for rows and columns
        rows_min.append(not_nan_indices[:, 0].min())
        rows_max.append(not_nan_indices[:, 0].max())
        cols_min.append(not_nan_indices[:, 1].min())
        cols_max.append(not_nan_indices[:, 1].max())

    # Determine the overall min/max indices to crop all arrays
    overall_min_row = max(rows_min)
    overall_max_row = min(rows_max)
    overall_min_col = max(cols_min)
    overall_max_col = min(cols_max)

    # Crop all arrays to the determined overall bounding box
    cropped_stack = np.stack([array[overall_min_row:overall_max_row+1, overall_min_col:overall_max_col+1] for array in stack], axis=0)
    print(f'cropped shape {cropped_stack.shape}')
    return cropped_stack


def ORB_align(prev_frame, frame, mask, vmin=None, vmax=None):
    MAX_FEATURES = 1000
    
    # Detect ORB features and compute descriptors.
    orb = cv2.ORB_create(nfeatures=MAX_FEATURES, patchSize=50)

    prev_frame = preprocess(prev_frame, vmin, vmax)
    frame = preprocess(frame, vmin, vmax)
   
    keypoints1, descriptors1 = orb.detectAndCompute(prev_frame, mask=mask)
    keypoints2, descriptors2 = orb.detectAndCompute(frame,  mask=mask)

    # Match features.
    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = matcher.match(descriptors1, descriptors2, None)
    if (matches is None) or (len(matches) <3):
        print("ORB feature detection did not find enough matches")
        raise AssertionError
   
    # Sort matches by score
    matches= sorted(matches, key=lambda x: x.distance, reverse=False)
    # Keep 3 matches as input for the getAffineTransform
    numMatches = 3
    matches = matches[:numMatches]

    # Extract location of matches
    points1 = np.zeros((len(matches), 2), dtype=np.float32)
    points2 = np.zeros((len(matches), 2), dtype=np.float32)
 
    for i, match in enumerate(matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt
 
    # Calculate the transformation matrix using cv2.getAffineTransform()
    M= cv2.getAffineTransform(points1[0:3] , points2[0:3])

    return M



def find_one_transform(prev_frame, frame, mask=None, vmin=None,vmax=None, initial_transform=None ):
    '''Transforms frame to align with prev_frame using translation, scale and rotation
    First uses the intensity based Enhanced Correlation Coefficient (ECC) from opencv to find transformation matrix
    For large shifts, ECC may fail. If it does not converge an initial guess of the transformation is therefore calculated first.
    The initial guess is calculated by the ORB feature matching in opencv
    Args:
    prev_frame : image to align to
    frame : image that should be aligned
    vmin,vmax : optional, minimum and maximum values for image scaling. If not provided, the color range will be scaled to +- 2 std. 
        image scaling is necessary for converting images into uint8 for the ORB algorithm. Will not affect dtype of aligned_frame
    mask: any areas that should not be considered as a mask of 1's and 0's
    initial_orb: Indicate if the initial transform should be calculated based on ORB feature matching first. Default False
    initial_guess: transform matrix as optional initial guess. Default None
    returns:
    - aligned_frame: frame shifted to align with prev_frame
    - transform: matrix used to align frame to prev_frame'''
   
    
    if np.isnan(frame).any() or  np.isnan(prev_frame).any():
        print('Arrays contains nans, aborting')
        raise ValueError
       
    frame = frame.copy().astype(np.float32)
    prev_frame = prev_frame.copy().astype(np.float32)
    if mask is None:
        mask = np.ones(shape=frame.shape, dtype=np.uint8)

    #Initialise transformation matrix to default identity matrix
    if initial_transform is None:
        transform = np.eye(2, 3, dtype=np.float32)
    #Or if provided initialise transformtion matrix to a guess
    else: 
        transform = initial_transform.astype(np.float32)
    
    try:
        retval, transform = cv2.findTransformECC(prev_frame, frame, transform, cv2.MOTION_AFFINE, inputMask=mask)
        return transform

   
    except Exception as e:
        print(e)
            
        print("ECC algorithm failed to converge with identity intitialisation matrix. Calculating rough alignment using ORB first")
        try:
            transform = ORB_align(prev_frame, frame, mask, vmin, vmax)
            transform = transform.astype(np.float32)
            print("ORB feature detection success. Will be used as initialisation matrix. Rerunning ECC")
            try:
                retval, transform = cv2.findTransformECC(prev_frame, frame, transform, cv2.MOTION_AFFINE, inputMask=mask)
               
                raise Exception
            except:
                print("ECC algorithm failed with given initialisation matrix. Aborting")
                raise Exception
                    
        except: 
            print("ORB feature detection did not find enough matches. Aborting")
            raise Exception
def find_transforms(doc : Dict, ref_element : str):
    """
    Args:
    - doc (str) : document from  MongoDB with metadata about stack
    - ref_element (str) : elemental map used for registration, e.g. Mn_Ka. Transformations found for this elemnt will be applied to all other stacks
    returns:
    - transforms (List[np.ndarray]) : list of transforms"""
    with h5py.File(doc['file_path'], 'r') as f:
        stack = f[f'/unregistered/line_intensities/{ref_element}'][()]
        stack = crop_nans(stack)
        transforms = []
        prev_frame = None
        
        for i, frame in enumerate(stack):
            
            if prev_frame is None:
                # If this is the first frame, set it as the previous frame 
                prev_frame = frame
                #append a transform that does nothing when applied
                transforms.append(np.eye(2, 3, dtype=np.float32))
        
                continue
            try:
                t = find_one_transform(prev_frame, frame)
                transforms.append(t)
            except:
                print("failed matching scan: " + str(doc['scan_numbers'][i]) + " with scan: " +  str(doc['scan_numbers'][i-1]))
    return transforms
                
def apply_transforms(stack : np.ndarray, transforms : List[np.ndarray]) -> np.ndarray:
    aligned_stack = []
    # Transforms in their current state describe the transformation between two subsequent images
    # Convert all transforms so that they describe the transform with respect to the very first frame in the stack.
    for i in range(np.shape(transforms)[0]):
        
    
        #flip the order of the transforms so that the matrix multiplication is correct
        # last transform will come first
        ts = np.flip(transforms[0:i+1],axis=0)
        #fix so that it has the correct shape
        final_transform = np.vstack((ts[0], [0, 0, 1]))
        # Chain all the transforms up until this frame i
        for j in range(1,len(ts)):
            final_transform = final_transform@np.vstack((ts[j], [0, 0, 1]))
        #apply the chained transform to the current frame
        frame = stack[i]
        aligned_stack.append(cv2.warpAffine(frame, final_transform[0:2,:], (frame.shape[1], frame.shape[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderValue=np.nan))
    return np.stack(aligned_stack, axis=0)
       
       

    

        

def register_stacks(beamline : str = None, sample_name : str = None, scan_type : str = None) -> None:
    client = pymongo.MongoClient('mongodb://localhost/')
    db = client['in_situ_fluo']
    stack_coll = db['stacks']
    query = {}
    if beamline is not None:
        query['beamline'] = beamline
    if sample_name is not None:
        query['sample_name'] = sample_name
    if scan_type is not None:
        query['scan_type'] = scan_type

    stack_docs = stack_coll.find(query)
    ref_element = 'Mn_Ka'
    try:
        for doc in stack_docs:
            print('Registering ' + doc['beamline'] + " " + doc['sample_name'] + " " + doc['scan_type'])
            transforms = find_transforms(doc, ref_element)
            with h5py.File(doc['file_path'], 'r+') as f:
                unregistered_line_intensities = f['/unregistered/line_intensities']
                registered_line_intensities = f.require_group('/registered/line_intensities')
                
                for element in unregistered_line_intensities:
                    element_stack = unregistered_line_intensities[element][()]
                    registered_element_stack = apply_transforms(element_stack, transforms)
                    ds = registered_line_intensities.create_dataset(name=element, data=registered_element_stack)
                    ds.attrs['units'] = 'a.u.'
                    ds.attrs['ref_element'] = ref_element
                    
                    
    finally:
        client.close()
        
        
#%%
    
    
if __name__ == '__main__':
    beamline = 'P06'
    sample_name = '08_alloy_C_lamella_A_roco'
    scan_type = 'cmesh prod'
    register_stacks(beamline, sample_name, scan_type)





# %%
