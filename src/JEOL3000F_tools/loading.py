#
# Created on Fri Oct 27 2023
#
# by Isac Lazar
#
import numpy as np
import hyperspy.api as hs
import glob
import os
def correct_pixel_scaling(s: hs.signals.Signal2D) -> None:
    '''If the image loaded into the signal is a diffraction pattern, change the 
    physical size spec of the pixels according to calibration'''
    DIFF_PATT_CALIB_SCALE_FACTOR = 40.25/40 #found by calibrating against pure Al lattice parameter 4.0509 Å
    #check if it is a diffraction pattern
    if s.axes_manager[0].units == '1/nm':
        
        s.axes_manager[0].scale = s.axes_manager[0].scale*DIFF_PATT_CALIB_SCALE_FACTOR
        
    if s.axes_manager[1].units == '1/nm':
        
        s.axes_manager[1].scale = s.axes_manager[1].scale*DIFF_PATT_CALIB_SCALE_FACTOR
def load_dm3_image(fname: str) -> (np.array, dict):
    import hyperspy.api as hs
    '''Loads dm3 (Gatan Digital Micrograph) images using the HyperSpy library
    Parameters:
        fname: path to dm3 image file
        
    Returns:
        np.array: image as numpy array
        dict: dictionary of metadata
        '''
    s = hs.load(fname)
    correct_pixel_scaling(s)
    im = s.data
    #get metadata from Hyperspy Signal
    metadata = s.metadata.as_dictionary()
    # Get the relevant metadata
    md = metadata['General']
    md.update(metadata['Acquisition_instrument'])
    # Get the metadata about scaling and units
    md.update(s.axes_manager.as_dictionary())
    
    return im, md

def load_dm3_by_unique_number(root_path: str, im_nr: int) -> (np.array, dict):
    '''Loads the microscope image with the unique image number, present somewhere in the root path
    Parameters:
        str root_path: path to look for .dm3 files
        int im_nr: the unique image number
    Returns:
    
        np.array: image as numpy array
        dict: dictionary of metadata
        
        '''
        
    files = glob.glob(os.path.join(root_path, '**/*.dm3'), recursive=True)
    frame_nr = str(im_nr).zfill(4)
    frame_fn = [s for s in files if frame_nr in s][0]
    
    im, md = load_dm3_image(frame_fn)
    
    return im, md
