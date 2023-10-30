#
# Created on Thu Oct 26 2023
#
# by Isac Lazar
#
import argparse
import os
import json

def main(args):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Load settings from the JSON configuration file
    if args.config_file:
        with open(args.config_file, 'r') as config_file:
            config = json.load(config_file)
        args.experiments = config.get('experiments', args.experiments)
        args.output_path = config.get('output_path', args.output_path)
        args.verbose = config.get('verbose', args.verbose)
        args.overwrite = config.get('overwrite', args.overwrite)

    
    if not os.path.exists(args.root_dir):
        print(f"Error: The specified root directory '{args.root_dir}' does not exist.")
        return

    
    if not args.output_path:
        # Set out_dir to the "out" directory relative to the current working directory
        out_dir = os.path.join(os.path.dirname(script_dir), "out")

    

    # Check if the necessary directory exist; create if not
    if not os.path.exists(out_dir):
        print(f'Out directory does not exist. Creating it')
        os.makedirs(out_dir)
    available_experiments = []
    for experiment in args.experiments:
        if not os.path.exists(os.path.join(args.root_dir, experiment)):
            print(f'Experiment data for {experiment} does not exist. Check the directory name?')
        else:
            print(f'Found experiment data for {experiment}')
            available_experiments.append(experiment)
    if len(available_experiments) == 0:
        print("No experiment data found. Quitting")
        return
    args.experiments = available_experiments
            

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data processing script")
    parser.add_argument("root_dir", type=str, help="Path to the root data directory")
    parser.add_argument("--experiments", type=str, default=["P06", "ID16B", "JEOL3000F"], nargs='+', help="Experiment or session names")
    parser.add_argument("--output-path", type=str, help="Path to the 'out' folder")
    parser.add_argument("--config-file", type=str, help="Path to a configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing files in 'out'")
    
    args = parser.parse_args()
    main(args)