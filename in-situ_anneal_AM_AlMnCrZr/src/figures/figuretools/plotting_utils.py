import hyperspy.api as hs
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.patches import Rectangle
import matplotlib as mpl
import numpy as np
import os
import glob
from typing import List, Callable
from inspect import signature, Parameter
import ipywidgets as widgets
from ipywidgets import interactive
from IPython.display import display


def create_parallelogram(ax: mpl.axes._axes.Axes, center: tuple, width: float, height: float, smallest_angle: float, rotation_angle: float, edgecolor: str = 'r', linewidth: float = 2) -> None:
    # Calculate the coordinates of the four vertices of the parallelogram
    half_width = width / 2
    half_height = height / 2
    skew_angle = 90-smallest_angle
    skew_matrix = np.array([[1,0 ], [np.tan(np.radians(skew_angle)), 1]])  # Corrected
    rotate_matrix = np.array([[np.cos(np.radians(rotation_angle)), -np.sin(np.radians(rotation_angle))],
                             [np.sin(np.radians(rotation_angle)), np.cos(np.radians(rotation_angle))]])
    vertices = np.array([
        [-half_width, -half_height],
        [half_width, -half_height],
        [half_width, half_height],
        [-half_width, half_height]
    ])
    # Apply skew and rotation transformations
    
    vertices = np.matmul(rotate_matrix, np.matmul(skew_matrix, vertices.T)).T + center
    # Create a Polygon patch
    parallelogram = Polygon(vertices, closed=True, edgecolor=edgecolor, linewidth=linewidth, facecolor='none')
    

    ax.add_patch(parallelogram)
def create_scale_bar(ax: mpl.axes._axes.Axes, position: tuple, size: tuple, unit: str, color:str = 'white', fontsize: float = 12):
    from matplotlib.text import Text
    '''
    Create a scale overline and text for an image.

    Parameters:
        position (tuple): The position of the scale overline (x, y) in the image.
        size (tuple): The size of the scale bar (width, height) in the image.
        unit (str): The unit of measurement for the scale bar (e.g., 'mm', 'cm').
        color (str): The color of the scale bar and text (default is 'white').
        fontsize (int): The fontsize for the text (default is 12).

    
    '''
    x, y = position
    width, height =  size
    scale_bar = Rectangle((x, y), width, height, edgecolor=color, facecolor=color)
    text_x = x + width / 2
    text_y = y + height*1.6
    text = f"{width} {unit}"
    
    ax.add_patch(scale_bar)
    
   
    ax.text(x=text_x, y=text_y, s=text, fontsize=fontsize, color=color, ha='center')


def plot_circles_along_line(ax: mpl.axes._axes.Axes, line_start: tuple, line_end: tuple, n_circles: int, plot_line: bool=False, labels: list = None, radius: float = 0.4, fontsize: float = 10, ha='left', va='center',**kwargs):
    # Extract x and y coordinates of the line start and end points
    x_start, y_start = line_start
    x_end, y_end = line_end

    # Calculate the step size to evenly distribute circles
    dx = (x_end - x_start) / (n_circles-1)
    dy = (y_end - y_start) / (n_circles-1)

    # Plot the line
    if plot_line:
        ax.plot([x_start, x_end], [y_start, y_end], color='b')

    # Plot circles along the line
    for i in range(n_circles):
        # Calculate the center of each circle
        x_circle = x_start + i * dx
        y_circle = y_start + i * dy

     

        # Plot the circle
        circle = plt.Circle((x_circle, y_circle), radius=radius,**kwargs)
        ax.add_patch(circle)
         # Annotate the circle with its label
        if labels is not None and i < len(labels):
            ax.annotate(labels[i], (x_circle+1.4*radius, y_circle-1.4*radius), color='w', fontsize=fontsize,
                        ha=ha, va=va)

def plot_image_with_physical_size(ax: mpl.axes._axes.Axes, im: np.array, x_scale: float, y_scale: float, show_axis: bool=True, **kwargs):
    """
    Plot an image with specified physical size for each pixel using the extent keyword.

    Parameters:
        ax: mpl.axes._axes.Axes object to plot image on
        im: image to be plotted
        x_scale: size of pixels in x direction
        y_scale: size of pixels in y direction
        show_axis (bool): If numbers on the axes should be plotted (default True)

    """
     
   
    height, width = im.shape[:2]
    extent = (0, width * x_scale, 0, height * y_scale)
    ax.imshow(im, extent=extent, **kwargs)
    
    if not show_axis:
        ax.axis('off')

def square_crop(image: np.array) -> np.array:
    '''Crops the largest dimension of a 2D array to the smallest dimension'''
    min_dim = np.min(image.shape)
    max_dim_idx = np.argmax(image.shape)
    difference = image.shape[max_dim_idx] - min_dim
    start = int(np.round(difference/2))
    end = int(np.round(image.shape[max_dim_idx] - difference/2))
    if max_dim_idx ==1:
        image = image[:,start:end]
    else:
        image = image[start:end, :]
    return image
    
def interactive_plotting(plot_function: Callable, args_to_interact: List[str], sranges: List[tuple]) -> None:
    """
    Creates an interactive plotting widget for a given plotting function.
    Only works if run as a notebook. (Scripts can be executed as notebook cells in VSCode)
    
    Parameters
    ----------
    plot_function : Callable
        The plotting function for which to create interactive sliders.
        
    args_to_interact : List[str]
        A list of argument names for which sliders should be created.
    sranges: List[tuple]
        A list of 3-tuples specifying the (start, end, step) of the slider
        
    Returns
    -------
    None
        Displays the interactive widget but does not return anything.
    """
    
    # Extract the arguments and default values from the plotting function
    sig = signature(plot_function)
    parameters = sig.parameters
    param_values = {name: param.default if param.default != Parameter.empty else 0 for name, param in parameters.items()}

    # Create sliders only for arguments specified in args_to_interact
    sliders = {}
    for arg, srange in zip(args_to_interact, sranges):
        default_value = param_values.get(arg, 0)
        sliders[arg] = widgets.FloatSlider(value=default_value, min=srange[0], max=srange[1], step=srange[2])

    # Create an interactive widget
    w = interactive(plot_function, **sliders)
    
    # Display the widget
    display(w)
   