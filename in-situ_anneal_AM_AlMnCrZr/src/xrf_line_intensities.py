#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
# This script creates elemental maps (tiff images) from xrf datasets (both ID16B and P06), based on the spectral intensities inside some ROI, 
# where the energies are specified by a json config file
# create_line_intensities()
# 
import h5py
import numpy as np
import pymongo
from PIL import Image
import json

def process_scan(doc: dict, config: dict) -> dict:
    """
    Processes a single X-ray fluorescence (XRF) scan document by calculating the line intensities for each element within specified regions of interest (ROIs).

    This function:
    1. Opens the HDF5 file corresponding to the scan, as specified in the 'file_path' field of the document.
    2. Extracts the XRF intensity data array 'I' from the HDF5 file.
    3. For each element defined in the configuration's 'rois', sums the intensities within the specified ROI range across all pixels, creating a dataset of line intensities for that element.
    4. Updates or creates datasets within the 'line_intensities' group in the HDF5 file for each element, including attributes for units and the channel ROI.
    5. Constructs a dictionary with paths to the datasets and their metadata, which will be used to update the MongoDB document.

    Args:
    - doc (dict): A dictionary representing the scan document from the MongoDB database.
    - config (dict): A dictionary containing the configuration settings, including 'rois' for different elements.

    Returns:
    - dict: A dictionary with keys in the form 'datasets.line_intensities', where each key corresponds to a dictionary with metadata and paths to the updated datasets in the HDF5 file.
    """
    hdf5_path = doc['file_path']
    print(doc['scan_number'])
    line_intensities = {}
    with h5py.File(hdf5_path, 'r+') as f:
        I = f['I'][()]
        if 'line_intensities' not in f:
            images_group = f.create_group('line_intensities')
        for element, roi in config['rois'].items():  # Assuming rois is a dict
            I_roi = I[:, :, roi[0]:roi[1]].sum(axis=2)
            dset_path = f'line_intensities/{element}'
            if dset_path not in f:
                dset = f.create_dataset(dset_path, data=I_roi)
            else:
                dset = f[dset_path]
                dset[...] = I_roi
            dset.attrs['units'] = 'a.u.'
            dset.attrs['channel_roi'] = roi
            line_intensities[element] = {
                'internal_path': dset_path,
                'units': 'a.u.',
                'channel_roi': roi
            }
    return {'datasets.line_intensities': line_intensities}
        
            

def create_line_intensities(beamline: str, config_path: str) -> None:
    """
    Connects to a MongoDB database and processes X-ray fluorescence (XRF) scan data by computing line intensities.

    The function performs these steps:
    1. Connects to the 'in_situ_fluo' database on the local MongoDB server.
    2. Retrieves documents from the 'scans' collection that match the specified beamline.
    3. Loads a configuration JSON file to identify regions of interest (ROIs) for each element present in the scan data.
    4. For each scan document, reads the HDF5 file specified in the document's 'file_path', processes the XRF data to calculate the sum of intensities across the specified ROIs for each element, and updates the HDF5 file with new datasets corresponding to these line intensities.
    5. Prepares a bulk update operation with the new line intensity data to update the MongoDB documents.
    6. Executes the bulk update on the 'scans' collection to include references to the newly created line intensity datasets.
    7. Closes the MongoDB connection.

    Args:
    - beamline (str): The name of the beamline, used to filter documents for processing.
    - config_path (str): The file system path to the JSON configuration file that specifies the ROIs for each element.

    Returns:
    - None: No return value. The function outputs the status of the operations and any errors encountered during processing.
    """
    mongo_client = pymongo.MongoClient('localhost', 27017)
    db = mongo_client['in_situ_fluo']
    collection = db['scans']
    docs = collection.find({'beamline': beamline})
    
    with open(config_path, 'r') as f:
        config_j = json.load(f)
        config = config_j[beamline]
        print(config)

    bulk_operations = [] # List of operations that will be sent to the db
    # Process each scan, and collect the update operations
    for doc in docs:
        scan_number = doc['scan_number']
        try:
            update = process_scan(doc, config)
            # Create an UpdateOne operation for the document
            bulk_op = pymongo.UpdateOne({'_id': doc['_id']}, {'$set': update})
            bulk_operations.append(bulk_op)
        except Exception as e:
            print(f'Error on {scan_number}')
            print(e.with_traceback())
        

    # Execute the bulk update to the db
    if bulk_operations:
        result = collection.bulk_write(bulk_operations)
        print(f"Updated {result.modified_count} documents")

    mongo_client.close()
    
if __name__ == '__main__':
    beamline = 'P06'
    fname = __file__.split('.')[0]

    config_path = f'{fname}.json'
    create_line_intensities(beamline, config_path)
    
        