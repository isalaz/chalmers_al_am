#
# Created on Thu Oct 26 2023
#
# by Isac Lazar
#
#This script contains functions for processing the raw data from the P06 experiment
# build_xrf_dataset(root_path: str, verbose: bool=False, config_file: str=None) - > None:
# find_unique_sample_names(base_directory: str) -> Set[str]:
# With helper functions:
# interpolate()
# temperatures()
# pixel_absolute_times()
# pixel_heating_times(threshold: float)
import argparse
import glob
import os
from typing import Set
import numpy as np
import datetime
import h5py
import natsort
import traceback
from scipy.interpolate import griddata
from dask.distributed import Client, as_completed
from dask import delayed
import dask
I0_SCALING_FACTOR = 1e4 #dont change 

def printer(s, verbose=False):
    if verbose:
        print(s)

class Scan:
    """
    Represents a single scan, encapsulating the metadata and file paths associated with it.

    Attributes:
        root_path (str): The root directory where the scan data is stored.
        sample_name (str): The name of the sample associated with this scan.
        scan_number (int): The numerical identifier for this scan.
        scan_str (str): A string representation of the scan number, zero-padded to 5 digits.
        meta_data_path (str): The full file path to the scan's metadata file.
        verbose (bool): Flag indicating whether to print additional output.

    Methods:
        __init__: Constructs a new Scan instance with the provided parameters.

    Parameters:
        root_path (str): The path to the root directory containing scan data.
        sample_name (str): The name of the sample to be associated with the scan.
        scan_number (int): The scan's unique number, which will be zero-padded in the file name.
        verbose (bool, optional): Enables verbose output if set to True. Defaults to False.

    """
    def __init__(self, root_path, sample_name, scan_number, verbose=False):
        self.root_path = root_path
        self.sample_name = sample_name
        self.scan_number = scan_number
        self.scan_str = 'scan_' + str(scan_number).zfill(5)
        self.meta_data_path = os.path.join(root_path,'raw', sample_name, self.scan_str + '.nxs')
        self.verbose=verbose
        
    def calc_absolute_times(self):
        """
        Calculates the absolute times for each data point (spectrum) within the scan based on the metadata and data files.

        This method reads the start and end times from the scan's metadata file and calculates the absolute time for
        each subsequent data point by reading the delta trigger times from the corresponding .nxs data files.
        
        The times are calculated in seconds as Unix timestamps, representing the number of seconds since the Unix epoch.

        Side Effects:
            - Populates the `self.absolute_times` attribute with the calculated absolute times.

        Raises:
            - FileNotFoundError: If the metadata file or data files do not exist at the specified paths.
            - ValueError: If the times in the metadata or data files cannot be parsed.

        Note:
            - This method relies on the presence of a specific HDF5 structure within the .nxs files.
            - Time precision is printed if verbose is True.
        """
        
        with h5py.File(self.meta_data_path, 'r') as f:
            start_time = f['scan/start_time'][()].decode('utf-8')
            end_time = f['scan/end_time'][()].decode('utf-8')
            format_str = "%Y-%m-%dT%H:%M:%S.%f%z"
            # Parse date string into datetime object
            start_time = datetime.datetime.strptime(start_time, format_str)
            end_time = datetime.datetime.strptime(end_time, format_str)
        
        time_path = os.path.join(self.root_path,'raw', self.sample_name, self.scan_str, "scantime_01" )
        time_files = natsort.natsorted(glob.glob(os.path.join(time_path, "*.nxs" )))
        if len(time_files) > 0:
            dtimes = []
            for f in time_files:
                with h5py.File(f, 'r') as f_:
                    
                    dtime = f_['entry/data/deltatriggertime'][()]
                    dtimes.extend(list(dtime))
            dtimes = np.array(dtimes)
            
            cumtimes = np.cumsum(dtimes, dtype=np.float32)
            times_seconds = np.round(cumtimes/1e6).astype(int) #dtimes are in µs
            absolute_times = times_seconds + start_time.timestamp()
            
            self.absolute_times = absolute_times
        else:
            raise Exception("No time files found")
        
    def gather_xrf_intensities(self):
        """
        Gathers X-ray fluorescence (XRF) intensity data from .nxs files associated with the scan.

        This method collects XRF intensity data from multiple detector channels, sums up the spectra
        across these channels, and stores the aggregated data.

        The method iterates over all detector modules or channel chunks, merges them, and appends
        them to the attribute `self.I`. The resulting attribute `self.I` will contain a NumPy array
        of the summed spectra for all channels for the whole scan.

        Side Effects:
            - Sets the `self.I` attribute with the collected and summed XRF intensity data.

        Raises:
            - AssertionError: If the number of .nxs files is inconsistent across channels.
            - FileNotFoundError: If the expected .nxs files are not found.
            - ValueError: If there are issues with reading the data from .nxs files.

        Note:
            - The method assumes a specific file and data structure within the .nxs files.
            - Verbose output will log the progress and details of the data gathering process.
        """
        processor_channels = glob.glob(os.path.join(self.root_path,'raw', self.sample_name, self.scan_str, 'xspress3*'))
    
        processor_ch_files = {}
        
        I = []
        #collect all .nxs files
        for processor_ch in processor_channels:
            processor_ch_files[processor_ch] = natsort.natsorted(glob.glob(os.path.join(processor_ch, "*.nxs" )))
         
        lengths = [len(lst) for lst in processor_ch_files.values()]
        assert all(length == lengths[0] for length in lengths), "Not all lists are of the same length."
        I = None
        #iterate through all detector modules/channel chunks, merge them and append them to I 
        for nxs_files_tuple in zip(*processor_ch_files.values()):
            # 'items' is a tuple containing the i-th element from each list
            # Process the first elements of all lists here
            chunk_I = None
            for nxs_file in nxs_files_tuple:
                printer(f'Loading {nxs_file}', self.verbose)
                with h5py.File(nxs_file, 'r') as f:
                    channels = f['entry/instrument/xspress3']
                    for ch in channels:
                        printer(f'Extracting channel {ch}', self.verbose)
                        ch_chunk = channels[ch]['histogram'][()] #ch_chunk contains approximately 500 spectra
                        printer(f'Shape of ch_chunk is {ch_chunk.shape}', self.verbose)
                        if chunk_I is not None :
                            printer('Merging to chunk', self.verbose)
                            chunk_I = chunk_I + ch_chunk
                        else: #first iteration
                            printer('Setting first channel as chunk', self.verbose)
                            chunk_I = ch_chunk
                        
                      
            #chunk_I contains the summed spectra of all channels in a chunk
            if I is not None:
                printer('Appending merged chunk to intensities',self.verbose)
                I = np.append(I, chunk_I, axis=0)
                printer(f'Shape of I is {I.shape}', self.verbose)
            else: #first iteration
                printer('Setting first merged chunk as intensities', self.verbose)
                I = chunk_I
                printer(f'Shape of I is {I.shape}', self.verbose)
        
        self.I = I
        printer(f'Finished loading fluo data. Shape of I is {I.shape}', self.verbose)
        printer(f'Mean counts per spectra is {I.mean(axis=0).sum()}', self.verbose)
                        
               
                    
    def load_positions(self):
        """
        Loads the positioner encoder data for both 'fast' and 'slow' axes from an HDF5 file.
        Also reads the position of the sample from the metadata file.

        The method reads 'encoder_fast' and 'encoder_slow' datasets from a file named "positions.h5"
        located in the scan's 'processed' subdirectory, and assigns the data to the attributes 
        `self.positions_fast` and `self.positions_slow` respectively.

        Side Effects:
            - Sets the `self.positions_fast` attribute with the fast axis position data.
            - Sets the `self.positions_slow` attribute with the slow axis position data.

        Raises:
            - FileNotFoundError: If "positions.h5" is not found in the expected path.
            - KeyError: If the expected datasets are not found within the file.
        """
        positions_path = os.path.join(self.root_path,'processed', self.sample_name, self.scan_str, "positions.h5")
        with h5py.File(positions_path, 'r') as f:
            encoder_fast = f['data/encoder_fast/data'][()]
            encoder_slow = f['data/encoder_slow/data'][()]
        self.positions_fast = encoder_fast
        self.positions_slow = encoder_slow
        
        
    def load_I0(self):
        """
        Loads the I0 (incident beam intensity) data from an HDF5 file.

        The method reads the 'ion_chamber_nano' dataset from a file named "counter.h5" located
        in the scan's 'data' subdirectory within 'processed', and assigns the data to the attribute
        `self.I0`.

        Side Effects:
            - Sets the `self.I0` attribute with the I0 data.
            - Prints the shape and mean of the I0 data if verbose is True.

        Raises:
            - FileNotFoundError: If "counter.h5" is not found in the expected path.
            - KeyError: If the 'ion_chamber_nano' dataset is not found within the file.
        """
        I0_path = os.path.join(self.root_path,'processed', self.sample_name, self.scan_str, "data", "counter.h5")
        with h5py.File(I0_path, 'r') as f:
            I0 = f['data/ion_chamber_nano'][()]
        self.I0 = I0
        printer(self.I0.shape, self.verbose)
        printer(self.I0.mean(), self.verbose)
        
    def load_metadata(self):
        """
        Extracts some metadata values
        Extracts the command arguments used to execute the scan at the beamline.
        Extracts the position of the sample stage
        """
        with h5py.File(self.meta_data_path, 'r') as f:
            # extract scan command and set motor commands
            command = f['/scan/program_name'].attrs['scan_command']
            command_list = parse_scan_command(command)
            self.fast_m_start, self.fast_m_end, self.fast_m_steps = command_list['fast_start'], command_list['fast_stop'], command_list['fast_steps']
            self.slow_m_start, self.slow_m_end, self.slow_m_steps = command_list['slow_start'], command_list['slow_stop'], command_list['slow_steps']
            self.dwell = command_list['dwell']
            self.fast_motor = command_list['fast_motor']
            self.slow_motor = command_list['slow_motor']
            printer(f'Fast start {self.fast_m_start} um, fast end {self.fast_m_end} um, fast steps {self.fast_m_steps}', self.verbose)
            printer(f'Slow start {self.slow_m_start} um, slow end {self.slow_m_end} um, slow steps {self.slow_m_steps}', self.verbose)
            printer(f'Dwell time {self.dwell} s', self.verbose)
            
            # extract sample stage parameters 
            stage_params = {}
       
            stage_group = f['/scan/sample/transformations']
            for param in stage_group:
                stage_params[param] = {'value':stage_group[param][0], 'units':stage_group[param].attrs['units']}
            self.stage_params = stage_params
     
                
            
            

    def interpolate(self):
        """
        Interpolates the intensity and absolute time data onto a regular grid defined by the scan parameters.

        This method creates a target grid based on the defined start, end, and number of steps for the fast
        and slow motors. It then uses the `griddata` function from `scipy.interpolate` to interpolate the 
        intensity data (`self.I`) and absolute times (`self.absolute_times`) from their original irregular grid 
        to the target grid. The intensity data is also normalied to the incoming beam intensity before saved

        The interpolation assumes that any missing spectra in `self.I` are at the end of the scan and thus 
        truncates the position arrays to match the length of `self.I`.

        Side Effects:
            - Sets `self.I_interp` with the interpolated intensity data.
            - Sets `self.abs_times_interp` with the interpolated absolute times.

        Raises:
            - ValueError: If the interpolation fails due to incorrect grid dimensions or other issues with the data.
        """
        
        # target grid to interpolate to
        fasti,slowi = np.meshgrid(np.linspace(self.fast_m_start, self.fast_m_end, self.fast_m_steps),
                                   np.linspace(self.slow_m_start, self.slow_m_end, self.slow_m_steps))
     
        
        I_normalised = self.I*I0_SCALING_FACTOR/((self.I0[:, None]*self.dwell))
       
  
        absolute_times = self.absolute_times.copy()
       
          
            
        positions_fast = self.positions_fast.copy()
        positions_slow = self.positions_slow.copy()
        #fix for missing spectra or missing positions assuming they are at the end of the scan
        if self.positions_fast.shape[0] > self.I.shape[0]:
            
            positions_fast = positions_fast[0:self.I.shape[0]]
            positions_slow = positions_slow[0:self.I.shape[0]]
        elif self.positions_fast.shape[0] < self.I.shape[0]:
            I_normalised = I_normalised[0:positions_fast.shape[0]]
           
            absolute_times = absolute_times[0:positions_fast.shape[0]]
            
        # interpolate
        
      
        self.I_interp = griddata((positions_slow,positions_fast), I_normalised, (slowi,fasti),method='nearest')
        self.fast_m_interp = fasti
        self.slow_m_interp = slowi
        #interpolate absolute times
        
        self.abs_times_interp = griddata((positions_slow,positions_fast), absolute_times,(slowi,fasti),method='nearest')
    
        
    def save_processed_scan(self):
        save_path = os.path.join(self.root_path,'process', self.sample_name, self.scan_str )
        if not os.path.exists(save_path):
            # Create a new directory because it does not exist 
            os.makedirs(save_path)
            
        printer(f'Saving scannr {self.scan_number}', self.verbose)
        with  h5py.File(os.path.join(save_path, self.scan_str + ".h5"), 'w') as save_f:
            
            ds = save_f.create_dataset("I", data=self.I_interp)
            ds.attrs['units'] = 'a.u.'
            save_f.create_group("positioners")
            ds = save_f.create_dataset('/positioners/fast_m_interp', data=self.fast_m_interp)
            if self.fast_motor in ['samy', 'samz']:
                ds.attrs['units'] = 'mm'
            else:
                ds.attrs['units'] = 'um'
            
            ds = save_f.create_dataset('/positioners/slow_m_interp', data=self.slow_m_interp)
            if self.fast_motor in ['samy', 'samz']:
                ds.attrs['units'] = 'mm'
            else:   
                ds.attrs['units'] = 'um'
           
            ds = save_f.create_dataset('absolute_times_interp', data=self.abs_times_interp)
            ds.attrs['units'] = 's'
            ds = save_f.create_dataset('dwell', data=self.dwell)
            ds.attrs['units'] = 's'
            save_f.create_dataset('I0_SCALING_FACTOR', data=I0_SCALING_FACTOR)
            
            save_f.create_group('stage_params')
            for param in self.stage_params:
                ds =save_f.create_dataset(f'stage_params/{param}', data=self.stage_params[param]['value'])
                ds.attrs['units'] = self.stage_params[param]['units']
        printer(f'Saved scannr {self.scan_number}', self.verbose)


def parse_scan_command(command: str) -> dict:
    command_list = command.split(' ')
    d_scan = {}
    d_scan['type'] = command_list[0]
    ### Get motors
    # 
    d_scan['fast_motor'] = command_list[1]
    d_scan['fast_start'] = float(command_list[2])
    d_scan['fast_stop']  = float(command_list[3])
    ### 
    if d_scan['type'] == 'cmesh':
        d_scan['fast_steps'] = int(command_list[4])
        d_scan['slow_motor'] = command_list[5]
        d_scan['slow_start'] = float(command_list[6])
        d_scan['slow_stop']  = float(command_list[7])
        #the slow motor is always step scan
        d_scan['slow_steps'] = int(command_list[8]) + 1
        d_scan['dwell'] = float(command_list[9])
       
    elif d_scan['type'] == 'jmesh': # handles the jmesh
        d_scan['fast_steps'] = int(command_list[4]) + 1
        d_scan['slow_motor'] = command_list[6]
        d_scan['slow_start'] = float(command_list[7])
        d_scan['slow_stop']  = float(command_list[8])
        d_scan['slow_steps'] = int(command_list[9])+1
        d_scan['dwell'] = float(command_list[11])
    elif d_scan['type'] == 'mesh':
        d_scan['fast_steps'] = int(command_list[4]) + 1 
        d_scan['slow_motor'] = command_list[5]
        d_scan['slow_start'] = float(command_list[6])
        d_scan['slow_stop']  = float(command_list[7])
       
        d_scan['slow_steps'] = int(command_list[8]) + 1
        d_scan['dwell'] = float(command_list[9])

    else:
        raise Exception('Scan type ' +d_scan['type'] + ' is neither cmesh or jmesh. Should skip it')
        
    return d_scan

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

def build_temperatures_file(root_path: str) -> None:
    """This function loads the log from the digital heater at the p06 beamline.
    It then concatinates them into a single file called "temperatures.txt" in the process folder.
    This file contains time in seconds (absolute/unix time) and the cell temperature.
    In the heater log files, the times for each mesuerement is in H:M:S and does not include the date. The date is written in the header. 
    Since the time can start over at midnight the script takes this into consideration """
    
    def extract_last_header_and_data(log_text):
        last_header_index = log_text.rfind("Digiheater 3.2") - 16 
        last_data = log_text[last_header_index:]
        return last_data

    def extract_temperatures(log_text):
        header_index = log_text.rfind("sample\ttime\tTset[C]\tTmeas[C]")
        log_data = log_text[header_index:]
        lines = log_data.strip().split('\n')
        headers = lines[0].split('\t')
        time_index = headers.index('time')
        tmeas_index = headers.index('Tmeas[C]')
        temperature_data = []

        for line in lines[1:]:
            values = line.split('\t')
            time_str = values[time_index]
            tmeas = float(values[tmeas_index])
            #process the hundreds of a second
            HMS, hunS = time_str.split('.')
            
            time_str = '.'.join([HMS, str(int((int(hunS)*1e4))).zfill(6)])
            
            temperature_data.append((time_str, tmeas))

        return temperature_data
    def combine_date_and_time(date_str, time_str):
        dt_str = f"{date_str} {time_str}"
        try:
            dt = datetime.datetime.strptime(dt_str, '%d/%m/%y %H:%M:%S.%f')
        except:
            print(dt_str)
        return dt
    def extract_date(log_text):
        date_line_index = 0
        date_str = log_text[date_line_index:date_line_index + 9]
        # Remove single quotes around the year (e.g., '22 -> 22)
        date_str = date_str.replace("'", "")
        return date_str
    
    source_folder = os.path.join(root_path, 'Climate_Lund Users_Digiheater data')
    # Get the list of files in the source folder
    files = glob.glob(os.path.join(source_folder, '*.log'))
    all_temperatures = []
    for f_ in files:
        with open(f_, 'r') as f:
            log_text = f.read()
            last_data =  extract_last_header_and_data(log_text)
            temperature_data = extract_temperatures(last_data)
            
            
            date_str = extract_date(last_data)
            last_dt = None
            current_delta_days = 0
            for time_str, tmeas in temperature_data:
                # Combine date from log with time from measured points
                dt = combine_date_and_time(date_str, time_str)
                dt += datetime.timedelta(days=current_delta_days)  # Adjust the date
                # Get the Unix timestamp
                unix_timestamp = dt.timestamp()
                # Check for midnight wrap-around
                if last_dt is not None:
                    if dt.timestamp() < last_dt.timestamp():
                        dt += datetime.timedelta(days=1)  # Adjust the date to the next day
                        current_delta_days +=1
                        
                        
                unix_timestamp = dt.timestamp()
                all_temperatures.append((unix_timestamp, tmeas))
                last_dt = dt
    # Sort the data based on timestamp
    all_temperatures.sort(key=lambda x: x[0])
    
    # Write the data to the temperatures.txt file
    with open(os.path.join(root_path, 'process','temperatures.txt'), 'w') as output_file:
        # Write the header
        output_file.write("t/s\tT/degC\n")
    
        for timestamp, temperature in all_temperatures:
            output_file.write(f"{timestamp}\t{temperature}\n")


            
# Dask delayed processing function
@delayed
def process_scan(root_path, sample_name, scan_number, verbose):
    try:
        s = Scan(root_path, sample_name, scan_number, verbose=verbose)
        s.calc_absolute_times()
        s.gather_xrf_intensities()
        s.load_positions()
        s.load_metadata()
        s.load_I0()
        s.interpolate()
        s.save_processed_scan()
        return scan_number, None  # Return the scan number and None for error
    except Exception as e:
        print(f'Error on scan {scan_number}')
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return scan_number, traceback_str  # Return the scan number and the error
    


def build_xrf_dataset(root_path: str, sample_names: Set, verbose: bool=False, config_file: str=None) -> None:

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
    print('Initialising dask client for parallel computing')
    client = Client()
    print(f'Number of cores found: {len(client.ncores())}')
    


    futures = []
    for sample_name in sample_names:
        sample_raw_dir = os.path.join(root_path, 'raw', sample_name)
        print(f'Processing {sample_name}')
        scan_files = glob.glob(os.path.join(sample_raw_dir, 'scan*.nxs'))
        scan_numbers = [int(os.path.basename(fn).split('.')[0].split('_')[1]) for fn in scan_files]
        scan_numbers = natsort.natsorted(scan_numbers)

        # Create Dask delayed tasks for each scan
        for scan_number in scan_numbers:
            future = process_scan(root_path, sample_name, scan_number, verbose)
            futures.append(future)

    # Compute all tasks in parallel
    results = client.compute(futures)

    # Gather results
    failed_scans = []
    for future, result in as_completed(results, with_results=True):
        scan_number, error = result
        if error:
            failed_scans.append(scan_number)

    # Handle failed scans
    for sample_name in sample_names:
        print(f'Finished processing {sample_name}.')
        if failed_scans:
            print(f'Failed on scan numbers: {sorted(failed_scans)}')
    client.shutdown()

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process P06 data')
    
    # Required argument for root_path
    parser.add_argument('root_path', type=str, help='The root path containing xrf experiment data.')
    
    # Optional argument for specific sample name
    parser.add_argument('--sample_name', type=str, help='A specific sample name to look for.', default=None)
    parser.add_argument('--verbose', type=str, help='Print debug info', default=False)
    
    args = parser.parse_args()
    
    unique_sample_names = find_unique_sample_names(args.root_path)
   
    print('Sample names found:')
    for name in unique_sample_names:
        print(name)

    
    if unique_sample_names:
        print('Found data directories')
        if args.sample_name:
         
            if args.sample_name in unique_sample_names:
                printer('Building temperatures file', verbose=args.verbose)
                #build_temperatures_file(args.root_path)
                print(f"Sample name {args.sample_name} exists in the directory.")
                build_xrf_dataset(args.root_path, set([args.sample_name]), verbose=args.verbose)
            else:
                print(f"Sample name {args.sample_name} does not exist in the directory.")
            
        else:
            print(f"Unique sample names in the directory are: {unique_sample_names}")
            printer('Building temperatures file', verbose=args.verbose)
            #build_temperatures_file(args.root_path)
            build_xrf_dataset(args.root_path, unique_sample_names, verbose=args.verbose)   
    else:
        print('No data directories found')