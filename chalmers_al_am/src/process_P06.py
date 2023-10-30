#
# Created on Thu Oct 26 2023
#
# by Isac Lazar
#
#This script contains functions for processing the raw data from the P06 experiment
# build_xrf_dataset(root_path: str, verbose: bool=False, config_file: str=None) - > None:
# find_unique_sample_names(base_directory: str) -> Set[str]:
# With helper functions:
# interpolation()
# temperatures()
# pixel_absolute_times()
# pixel_heating_times(threshold: float)
import argparse
import glob
import os
from typing import Set

def find_unique_sample_names(base_directory: str) -> Set[str]:
    """
    Finds unique sample names based on the file paths that follow the pattern "scan*.nxs"
    in subsubdirectories under the given base directory.
    
    Parameters:
    - base_directory (str): The path to the base directory containing sample subdirectories.
    
    Returns:
    - Set[str]: A set of unique sample names.
    """
    # Use glob to find all files in raw subsubdirectories that match the pattern "scan*.nxs"
    files = glob.glob(os.path.join(base_directory, 'raw', '*',"scan*.nxs"))
    
    # Initialize an empty set to store unique sample names
    unique_sample_names = set()
    
    # Iterate over the found files to extract the unique sample names
    for file in files:
        # Split the file path to get the directory components
        dir_components = file.split(os.sep)
        
        # Get the sample name, which should be one directory level above the file
        sample_name = dir_components[-2]
        
        # Add it to the set (which ensures uniqueness)
        unique_sample_names.add(sample_name)
    
    return unique_sample_names

def build_xrf_dataset(root_path: str, verbose: bool=False, config_file: str=None) -> None:
    """
    Processes X-Ray Fluorescence (XRF) data based on the given root directory 
    and places the processed data into a specified output directory.

    Parameters:
    - root_path (str): The root directory where the raw XRF data is stored. The function 
      will look for relevant files in this directory and its subdirectories.
    - verbose (bool, optional): Whether to print detailed progress information. Defaults to False.
    - config_file (str, optional): The path to a JSON configuration file specifying additional 
      options for data processing. If None, default settings will be used, which is to look for the config file with the same name as the script.

    Side Effects:
    - Processes the XRF data and places it into an output directory specified either in 
      the `config_file` or by default rules.
      
    Raises:
    - FileNotFoundError: If `root_path` does not exist or is not a directory.
    - ValueError: If `config_file` is provided but contains invalid settings."""
    unique_sample_names = find_unique_sample_names(root_path)
    for sample_name in unique_sample_names:
        sample_raw_dir = os.path.join(root_path, 'raw', sample_name)
        scan_numbers = glob.glob(os.path.join(sample_raw_dir, 'scan*.nxs'))
        scan_numbers = [int(os.path.basename(fn).split('.')[0].split('_')[1]) for fn in scan_numbers]
        for scan_number in scan_numbers:
            print(scan_number)
    
    
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process P06 data')
    
    # Required argument for root_path
    parser.add_argument('root_path', type=str, help='The root path containing xrf experiment data.')
    
    # Optional argument for specific sample name
    parser.add_argument('--sample_name', type=str, help='A specific sample name to look for.', default=None)
    
    args = parser.parse_args()
    
    unique_sample_names = find_unique_sample_names(args.root_path)
   
    print('Sample names found:')
    for name in unique_sample_names:
        print(name)

    
    if args.sample_name:
         
        if args.sample_name in unique_sample_names:
            print(f"Sample name {args.sample_name} exists in the directory.")
        else:
            print(f"Sample name {args.sample_name} does not exist in the directory.")
    else:
        print(f"Unique sample names in the directory are: {unique_sample_names}")
        build_xrf_dataset(args.root_path)   