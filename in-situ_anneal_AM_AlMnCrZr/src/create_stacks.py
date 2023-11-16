#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
# This script reorganises the images produced by xrf_line_intensities.py and xrf_pymca_fitting.py
# Based on a provided look_up table excel sheet, it puts elemental maps in a common folder if they are of 
# the same sample and scan type e.g otf roi1 prod.
#It also updates the mongodb scans database with a type if the scan belongs to a scan type
# The functions in this scripts takes an excel file lookup table as input. The excel file is for 
# a specific beamline. The different sheets inside it are named after sample_names, however they are not exact matches in their formatting to the database and folder names.
# This fact does not matter since every scan number is unique. There is a column called Scan Number
# and a column called Scan Types. 
# This script finds all the unique Scan Types. By looking at the databse entries, all the scans with the same type that also 
# are on the same sample should be organised into a stack, with the name of the scan type.
# Every stack should be contained in a new hdf5 file named {Scan Type}.h5. There should be a group called unregistred,
# beneath that is a group called line_intensities, and beneath that are datasets consisting of stacks of different elements such as Mn_Ka
# It also puts the pixel times datasets in this stack form as well. There should be a dataset under unregistered, that is called
# pixel_times, and is a stack of the corresponding pixel times
# The script also creates a new collection called stacks in the MongoDB. Here each entry has a scan_type,
# beamline and sample_name field. It also has a field called scan_numbers which is a list containing the unqie scan_numbers in the stack
import pandas as pd
import pymongo
import h5py
import os
import numpy as np
from typing import List, Dict, Tuple
def read_excel_lookup_table(excel_path: str) -> pd.DataFrame:
    """
    Reads the Excel lookup table and returns a DataFrame with scan numbers and types.
    
    Args:
    - excel_path (str): Path to the Excel lookup table.
    
    Returns:
    - DataFrame: A DataFrame with the contents of the Excel lookup table,
                 with columns for 'Scan Number' and 'Scan Types'.
    """
    # Assuming the Excel file has a consistent structure with 'Scan Number' and 'Scan Type' columns
    # across all sheets. Concatenates all sheets into a single DataFrame.
    xl = pd.ExcelFile(excel_path)
    df_list = []
    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)[['Scan Number', 'Scan Type']]  # Extract only the required columns
        # Remove rows where 'Scan Type' is NaN
        df = df.dropna(subset=['Scan Type'])

        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)
def organize_scans_into_stacks(beamline : str, df: pd.DataFrame, base_folder: str, db: pymongo.database.Database, stacks : Dict) -> None:
    """
    Organizes scans into stacks by looking up the sample name from the database for each scan number,
    and then grouping by sample name and scan type. Creates HDF5 files for each scan_type.

    Args:
    - beamline (str) : Name of beamline, e.g. P06
    - df (pd.DataFrame): DataFrame containing scan numbers and scan types.
    - base_folder (str): The base directory where HDF5 files will be stored.
    - db (pymongo.database.Database): The MongoDB database instance where scan documents are stored.
    - stacks (dict) : Dictionary to be populated with (sample_name, scan_type) as keys and
        a list of scan numbers as value

    Returns:
    - None
    """
    df = df.sort_values(by='Scan Number', ascending=True)  # make sure scan numbers in the stacks will be ascending
    

    # Iterate over the DataFrame rows
    for index, row in df.iterrows():
        scan_number = row['Scan Number']
        scan_type = row['Scan Type']

        # Query the database for the sample name using the scan number
        scan_doc = db.scans.find_one({'beamline' : beamline, 'scan_number': scan_number})
        if scan_doc:
            sample_name = scan_doc['sample_name']
            
            # Create a unique key for each sample_name and scan_type combination
            stack_key = (sample_name, scan_type)
            
            # Initialize the group in the dictionary if it doesn't exist
            if stack_key not in stacks:
                stacks[stack_key] = []

            # Append the scan number to the group
            stacks[stack_key].append(scan_number)

    # Create HDF5 files for each group
    for (sample_name, scan_type), scan_numbers in stacks.items():
        create_hdf5_stack(beamline, scan_type, sample_name, scan_numbers, base_folder, db)
def stacker(data_stack: List[np.ndarray]) -> np.ndarray:
    """
    Takes a list of 2D arrays in data_stack, and stacks them along the 0-axis.
    Handles the situation when not all 2D arrays are of the exact same shape by padding 
    smaller 2D arrays with NaN values to match the largest array. 

    Args:
    - data_stack (List[np.ndarray]): List of 2D numpy arrays.

    Returns:
    - np.ndarray: A 3D numpy array after stacking the padded 2D arrays.
    """
    if not data_stack:
        return np.array([])  # Return an empty array if the list is empty

    # Find the maximum shape in terms of rows and columns
    max_rows = max(arr.shape[0] for arr in data_stack)
    max_cols = max(arr.shape[1] for arr in data_stack)

    # Function to pad arrays to the maximum size
    def pad_array(arr, max_rows, max_cols):
        padded = np.full((max_rows, max_cols), np.nan, dtype=arr.dtype)
        padded[:arr.shape[0], :arr.shape[1]] = arr
        return padded

    # Pad each 2D array to the maximum shape and stack them
    padded_stack = [pad_array(arr, max_rows, max_cols) for arr in data_stack]
    return np.stack(padded_stack, axis=0)

def create_hdf5_stack(beamline : str, scan_type: str, sample_name: str, scan_numbers: List[int], base_folder: str, db: pymongo.database.Database) -> None:
    """
    Creates a new HDF5 file for a given scan type and sample name, containing stacks of elemental maps,
    pixel times, and position datasets with their associated metadata.

    Args:
    - beamline (str) : Name of beamline, e.g. P06
    - scan_type (str): The type of the scan to create a stack for.
    - sample_name (str): The name of the sample to create a stack for.
    - scan_numbers (List[int]): The list of scan numbers that will be included in the stack.
    - base_folder (str): The base directory where the HDF5 file will be stored.
    - db (pymongo.database.Database): The MongoDB database instance where scan documents are stored.

    Returns:
    - None
    """
    # Define the HDF5 file path
    hdf5_file_path = os.path.join(base_folder, sample_name, "stacks", f"{scan_type}.h5")
    
    # Create the base folder if it does not exist
    os.makedirs(os.path.dirname(hdf5_file_path), exist_ok=True)

    # Open a new HDF5 file in write mode
    with h5py.File(hdf5_file_path, 'w') as hdf5_file:
        # Create the 'unregistered' group
        hdf5_file.create_dataset('scan_numbers', data=scan_numbers, dtype=int)
        unregistered_group = hdf5_file.create_group('unregistered')

        # Create the 'line_intensities' and 'positions' groups
        line_intensities_group = unregistered_group.create_group('line_intensities')
        positions_group = unregistered_group.create_group('positions')

        # Initialize dictionaries to store stacks of data
        element_stacks = {}
        pixel_times_stack = []
        positions_fast_stack = []
        positions_slow_stack = []
        units = {}

        # Iterate over scan numbers to populate the stacks
        for scan_number in scan_numbers:
            # Retrieve the scan document from MongoDB
            scan_doc = db.scans.find_one({'beamline' : beamline, 'scan_number': scan_number})
            
            if not scan_doc:
                print(f"Scan number {scan_number} not found. Skipping.")
                continue

            # Open the HDF5 file for this scan
            with h5py.File(scan_doc['file_path'], 'r') as scan_hdf5:
                # Stack pixel times
                if 'unix_time' in scan_doc['datasets']:
                    pixel_times_stack.append(scan_hdf5[scan_doc['datasets']['unix_time']['internal_path']][()])
                    units['unix_time'] = scan_doc['datasets']['unix_time']['units']

                # Stack positions
                if 'positions_fast' in scan_doc['datasets']:
                    positions_fast_stack.append(scan_hdf5[scan_doc['datasets']['positions_fast']['internal_path']][()])
                    units['positions_fast'] = scan_doc['datasets']['positions_fast']['units']
                if 'positions_slow' in scan_doc['datasets']:
                    positions_slow_stack.append(scan_hdf5[scan_doc['datasets']['positions_slow']['internal_path']][()])
                    units['positions_slow'] = scan_doc['datasets']['positions_slow']['units']

                # Stack elemental line intensities
                for element, data_info in scan_doc['datasets']['line_intensities'].items():
                    element_data = scan_hdf5[data_info['internal_path']][()]
                    if element not in element_stacks:
                        element_stacks[element] = [element_data]
                        units[element] = data_info['units']
                    else:
                        element_stacks[element].append(element_data)

        # Write the stacked data to the new HDF5 file and include units metadata
        for element, data_stack in element_stacks.items():
            try:
                stacked_data = stacker(data_stack)
                ds = line_intensities_group.create_dataset(element, data=stacked_data)
                ds.attrs['units'] = units[element]
            except Exception as e:
                print(f'Shapes in stack of element {element}')
                for d in data_stack:
                    print(d.shape)

        if pixel_times_stack:
            stacked_pixel_times = stacker(pixel_times_stack)
            ds = unregistered_group.create_dataset('unix_time', data=stacked_pixel_times)
            ds.attrs['units'] = units['unix_time']

        if positions_fast_stack:
            stacked_positions_fast = stacker(positions_fast_stack)
            ds = positions_group.create_dataset('positions_fast', data=stacked_positions_fast)
            ds.attrs['units'] = units['positions_fast']

        if positions_slow_stack:
            stacked_positions_slow = stacker(positions_slow_stack)
            ds = positions_group.create_dataset('positions_slow', data=stacked_positions_slow)
            ds.attrs['units'] = units['positions_slow']

    print(f"Created HDF5 file for sample '{sample_name}' with scan type '{scan_type}' containing {len(scan_numbers)} scans.")


def update_mongodb_scans(beamline : str, df: pd.DataFrame, db: pymongo.database.Database) -> None:
    """
    Updates the 'scans' collection in MongoDB with the scan types.
    
    Args:
    - beamline (str) : Name of beamline, e.g. P06
    - df (pd.DataFrame): DataFrame containing scan numbers and types.
    - db (pymongo.database.Database): The MongoDB database instance where documents are stored.
    
    
    Returns:
    - None
    """
    # Retrieve the 'scans' collection
    
    scans_collection = db['scans']

    # Iterate through the DataFrame and update each scan with its type
    for index, row in df.iterrows():
        scan_number = row['Scan Number']
        scan_type = row['Scan Type']
        # Update the document where the scan number matches
        scans_collection.update_one(
            {'beamline' : beamline, 'scan_number': scan_number},
            {'$set': {'scan_type': scan_type}},
            upsert=False  # Assuming that the document already exists
        )
def create_mongodb_stacks_collection(base_folder : str, beamline : str, stacks: Dict[Tuple[str, str], List[int]], db: pymongo.database.Database) -> None:
    """
    Creates and populates a 'stacks' collection in MongoDB.
    
    Args:
    - base_folder (str): The base directory where the HDF5 file will be stored.
    - beamline (str) : Name of beamline, e.g. P06
    - stacks (Dict[Tuple[str, str], List[int]]): A dictionary with keys as a tuple of sample_name and scan_type, and values as a list of scan_numbers.
    - db (pymongo.database.Database): The MongoDB database instance where documents are stored.
    
    Returns:
    - None
    """
    
    stacks_collection = db['stacks']
    

    # Iterate through the stacks dictionary and create documents for the 'stacks' collection
    for (sample_name, scan_type), scan_numbers in stacks.items():
        # Create a query for the unique combination of beamline, sample_name, and scan_type
        query = {
            'beamline': beamline,
            'sample_name': sample_name,
            'scan_type': scan_type
        }
        file_path = os.path.join(base_folder, sample_name, "stacks", f"{scan_type}.h5")
    # Create a document for the stack
        stack_document = {
            'beamline': beamline,
            'sample_name': sample_name,
            'scan_type': scan_type,
            'scan_numbers': scan_numbers,
            'file_path' : file_path
        }
        
        # Replace the existing document or insert a new one if it doesn't exist
        stacks_collection.replace_one(query, stack_document, upsert=True)


def main(beamline : str, excel_path: str, base_folder: str, mongo_uri: str, db_name: str):
    """
    The main function that coordinates the execution of the script.
    
    Args:
    - beamline (str) : name of beamline e.g. P06
    - excel_path (str): Path to the Excel lookup table.
    - base_folder (str): The base directory where HDF5 files will be stored.
    - mongo_uri (str): The URI string to connect to the MongoDB server.
    - db_name (str): The name of the database where the collections are stored.
    
    Returns:
    - None
    """
    
    # Step 1: Read the Excel lookup table
    df = read_excel_lookup_table(excel_path)

    # Step 2: Connect to MongoDB
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    
    stacks_collection = db['stacks']
    # create a compund index for beamline, sample name and scan type. These in combination are always unique,
    # this prevents duplicate entries whe rerunning this script.
    stacks_collection.create_index( [("beamline", pymongo.DESCENDING), ("sample_name", pymongo.ASCENDING), ('scan_type', pymongo.ASCENDING)],  unique=True )

    # Initialize a dictionary to hold the scan stacks information
    stacks = {}

    try:
        # Step 3: Organize scans into stacks and create HDF5 files
        organize_scans_into_stacks(beamline, df, base_folder, db, stacks)
        
        # Step 4: Update MongoDB 'scans' collection with scan types
        update_mongodb_scans(beamline, df, db)
        
        # Step 5: Create MongoDB 'stacks' collection
        create_mongodb_stacks_collection(base_folder, beamline, stacks, db)
    finally:
        # Step 6: Close the MongoDB connection
        client.close()

    # Print a completion message
    print("Script execution completed successfully.")

# The script would be executed by calling the main function with the necessary arguments.
# main('path/to/lookup_table.xlsx', '/path/to/base_folder', 'mongodb://localhost:27017/', 'your_db_name')
if __name__ == '__main__':
    beamline = 'P06'
    mongo_uri = 'mongodb://localhost/'
    db_name = "in_situ_fluo"
    base_path = '/data/lazari/data/chalmers_al_am/Al_AM_P06/process'
    xl_path = "/data/lazari/data/chalmers_al_am/Al_AM_P06/logbook_look_up_table.xlsx"
    main(beamline=beamline, excel_path=xl_path, base_folder=base_path, 
         mongo_uri=mongo_uri, db_name=db_name)