# In-situ Anneal AM AlMnCrZr


## Characterization research on Al-Mn-Cr-Zr alloys specifically designed for additive manufacturing (AM)


https://github.com/isalaz/chalmers_al_am/assets/54549507/20bc54fb-14a8-4aaa-ae27-6faffb2a5b25

This repository contains the code used to process data and produce figures that were used in the manuscript [In situ Imaging of Precipitate Formation in Additively Manufactured Al-Alloys by Scanning X-ray Fluorescence](https://www.arxiv.org/abs/2311.14529). 

It includes loading, processing and modeling of data from various experiments. 

For papers concerning the development of the alloy see papers by Bharat Mehta et. al.:
[Al–Mn–Cr–Zr-based alloys tailored for powder bed fusion-laser beam process: Alloy design, printability, resulting microstructure and alloy properties](https://www.doi.org/10.1557/s43578-022-00533-1)

[Effect of precipitation kinetics on microstructure and properties of novel Al-Mn-Cr-Zr based alloys developed for powder bed fusion – laser beam process](https://www.doi.org/10.1016/j.jallcom.2022.165870)


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


