import hyperspy.api as hs
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.patches import Rectangle
import numpy as np
import os
import glob

def correct_pixel_scaling(s: hs.signals.Signal2D) -> None:
    '''If the image loaded into the signal is a diffraction pattern, change the 
    physical size spec of the pixels according to calibration'''
    DIFF_PATT_CALIB_SCALE_FACTOR = 40.25/40 #found by calibrating against pure Al lattice parameter 4.0509 Å
    #check if it is a diffraction pattern
    if s.axes_manager[0].units == '1/nm':
        print('Correcting physical scale of axis 0 to calibration')
        s.axes_manager[0].scale = s.axes_manager[0].scale*DIFF_PATT_CALIB_SCALE_FACTOR
        
    if s.axes_manager[1].units == '1/nm':
        print('Correcting physical scale of axis 0 to calibration')
        s.axes_manager[1].scale = s.axes_manager[1].scale*DIFF_PATT_CALIB_SCALE_FACTOR

def load_2d_image(root_path: str, im_nr: int) -> hs.signals.Signal2D:
    '''Loads the microscope image with the unique image number, present somewhere in the root path
    Args:
        str root_path: path to look for .dm3 files
        int im_nr: the unique image number'''
    files = glob.glob(os.path.join(root_path, '**/*.dm3'), recursive=True)
    frame_nr = str(im_nr).zfill(4)
    frame_fn = [s for s in files if frame_nr in s][0]
    print(f'Loading {frame_fn}')
    s = hs.load(frame_fn)
    correct_pixel_scaling(s)
    return s
    

def create_parallelogram(center: tuple, width: float, height: float, smallest_angle: float, rotation_angle: float, edgecolor='r', linewidth=2):
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

    return parallelogram
def create_scale_bar(ax, position: tuple, size: tuple, unit: str, color='white', fontsize=12):
    from matplotlib.text import Text
    '''
    Create a scale overline and text for an image.

    Parameters:
        position (tuple): The position of the scale overline (x, y) in the image.
        size (tuple): The size of the scale bar (width, height) in the image.
        unit (str): The unit of measurement for the scale bar (e.g., 'mm', 'cm').
        color (str): The color of the scale bar and text (default is 'white').
        fontsize (int): The fontsize for the text (default is 12).

    Returns:
        tuple: A tuple containing a Rectangle patch representing the scale bar and
        a tuple containing the text, its position, and fontsize.
    '''
    x, y = position
    width, height =  size
    scale_bar = Rectangle((x, y), width, height, edgecolor=color, facecolor=color)
    text_x = x + width / 2
    text_y = y + height*1.6
    text = f"{width} {unit}"
    
    ax.add_patch(scale_bar)
    
   
    ax.text(x=text_x, y=text_y, s=text, fontsize=fontsize, color=color, ha='center')


def plot_circles_along_line(ax, line_start: tuple, line_end: tuple, n_circles: int, plot_line: bool=False, labels: list = None, radius=0.4,fontsize=10, **kwargs):
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

        # Define the radius of the circles (you can adjust this as needed)
        

        # Plot the circle
        circle = plt.Circle((x_circle, y_circle), radius=radius,**kwargs)
        ax.add_patch(circle)
         # Annotate the circle with its label
        if labels is not None and i < len(labels):
            ax.annotate(labels[i], (x_circle+1.4*radius, y_circle), color='w', fontsize=fontsize,
                        ha='left', va='center')

def plot_image_with_physical_size(s: hs.signals.Signal2D, ax, square_crop=False, show_axis: bool=True, **kwargs):
    """
    Plot an image with specified physical size for each pixel using the extent keyword.

    Parameters:
        s: Signal2D to be plotted
        show_axis (bool): If numbers on the axes should be plotted (default true)

    Returns:
        matplotlib.axes._axes.Axes: The axis object for further modifications.

    """
    image = s.data
    if square_crop:
        min_dim = np.min(image.shape)
        max_dim_idx = np.argmax(image.shape)
        difference = image.shape[max_dim_idx] - min_dim
        start = int(np.round(difference/2))
        end = int(np.round(image.shape[max_dim_idx] - difference/2))
        if max_dim_idx ==1:
            image = image[:,start:end]
        else:
            image = image[start:end, :]
        
    pixel_size_x = s.axes_manager['x'].scale
    pixel_size_y = s.axes_manager['y'].scale
    
    height, width = image.shape[:2]
    extent = (0, width * pixel_size_x, 0, height * pixel_size_y)
    ax.imshow(image, extent=extent, **kwargs)
    
    if not show_axis:
        ax.axis('off')
    
