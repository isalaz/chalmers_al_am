#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
# This script takes in stacks of images, and produces movies of them. Given a json config, it can also create an rgb movie based on 3 elements
# movie_maker()
# create_rgb() #maybe this one should be in figures/figuretools ?

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from glob import glob
import pandas as pd
import os
from natsort import natsorted
from ipywidgets import interact
import pymongo
import matplotlib.animation as animation
from pathlib import Path
import h5py
def movie_maker(beamline : str = None, sample_name : str = None, scan_type : str = None):
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
    element_names = ['Mn_Ka', 'Cr_Ka']
    
    
    for doc in stack_docs:
        try:
            print('Producing movie of ' + doc['beamline'] + " " + doc['sample_name'] + " " + doc['scan_type'])
            with h5py.File(doc['file_path'], 'r') as f:
                
                stack_group = f[f'/registered/line_intensities']
                elements_stacks = {}
                for element in element_names:
                    ims = stack_group[element][()]
                    ims = ims/np.nanmax(ims) #normalise to 1
                    elements_stacks[element] =  ims
                    stack_shape = stack_group[element][()].shape
                    dtype = stack_group[element][()].dtype
                images_layered = np.zeros(shape=stack_shape[:] + (3,), dtype=dtype)
                for idx, element in enumerate(element_names):
                    images_layered[:,:,:, idx] = elements_stacks[element]
            
            script_dir = Path(__file__).parent
            folder_save_path = os.path.join(script_dir, 'out', 'movies', doc['beamline'], doc['sample_name'])
            if not os.path.exists(folder_save_path):
                os.makedirs(folder_save_path)
            fn = doc['scan_type'] + '_rgb_' + '_'.join(element_names) + '.mp4'
            save_path = os.path.join(folder_save_path, fn)


            fig, ax = plt.subplots()

            def animate(im_nr):
    
                plt.imshow(images_layered[im_nr,:, :, :], origin='upper')
    
    
                
                plt.axis('off')

                # Create an animation object from a plotting variable
            ani = animation.FuncAnimation(fig, animate, frames=range(0, images_layered.shape[0]), interval=1)

            if images_layered.shape[0] > 10 :
                fps = 2
            else:
                fps = 1
            ani.save(save_path, writer='ffmpeg', fps=fps, dpi=600)
        except Exception as e:
            print(e)
                    
                    
                
                


if __name__ == '__main__':
    movie_maker()