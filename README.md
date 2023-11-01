# Chalmers Al AM
## Characterization research on Al alloys specifically designed for additive manufacturing (AM), developed at Chalmers University of Technology


https://github.com/isalaz/chalmers_al_am/assets/54549507/20bc54fb-14a8-4aaa-ae27-6faffb2a5b25


For papers concerning the development of the alloy see :
Bharat Mehta

This repository contains the code used to produce figures, images and tables that were used in manuscripts. It includes loading, processing and modeling of data from various experiments. 
### Scanning X-ray Fluorescence measurements (XRF). 
These experiments were performed at two separate synchrotron facilities
- ID16B beamline at the European Synchrotron Research Facility (ESRF) in Grenoble
  - Scanning X-ray fluorescence
  - Heating/cooling ramps
- P06 beamline at the PETRA III synchrotron, DESY, Hamburg
  - Scanning X-ray fluorescence
  - Simultanueous acquisition of transmission diffraction for Coherent Diffraction Imaging
    - Using the Eiger4M 2D detector
### (S)TEM
These experiments were performed using the JEOL 3000F microscope at nCHREM, Lund Unviersity, Sweden. 
Data from this experiment consists of 
- TEM mode imaging (S)
  - Bright field TEM imaging
  - Selected Area Electron Diffraction (SAED)
  - Dark Field TEM imaging
- STEM mode imaging
  - HAADF mode
- EDX/EDS elemental mapping 
  - Spectral images as data cubes (.raw + .rpl)
  - Point acquisitions as individual spectra

## Running specific scripts
If you want to run a specific script, such as a single script for generating a figure, here are the steps.
Make sure your current working directory is the /src directory
```
cd /src
```
```
python -m package.module.script
```
Example 
```
python -m figure_scripts.BF_DF_SAED310_SAED594 
```
