#
# Created on Fri Oct 27 2023
#
# by Isac Lazar
#
#%%
  
import matplotlib.pyplot as plt
from figuretools.JEOL300F_loading import load_dm3_by_unique_number
from figuretools.plotting_utils import square_crop, plot_circles_along_line, create_parallelogram, create_scale_bar, plot_image_with_physical_size, interactive_plotting
import os

import json
 
font = {'family' : 'Arial','weight' : 'normal'} 
plt.rc('font', **font)      

plt.rcParams['text.usetex'] = False # TeX rendering

 
def BF_DF_SAED310_SAED594(**kwargs):
    from matplotlib.patches import Circle
    '''
    Function for plotting the figure. Below are the parameters that can be set. By default they are read from the
    json config file that has the same name as the function
    # #########Define constants applying to all subplots#############################################################################
    # p["scale_bar_fs"]  # font size of scale bars
    # p["titles_fs"]  # font size of title texts
    # p["annotation_fs"] # font size of annotation texts
    # p["annotation_linewidths"]  # linewidth of annotations
    # p["letter_label_x_padding_ratio"]  #left padding in terms of ratio of x-axis width
    # p["letter_label_y_padding_ratio"]  # #top padding in terms of ratio of y-axis height
    # p["title_x_padding_ratio"]  #right padding in terms of ratio of x-axis width
    # p["title_y_padding_ratio"]  # #top padding in terms of ratio of y-axis height
    
    # p["sb_position_x_A_B"], p["sb_position_y_A_B"]
    # p["sb_size_width_A_B"], p["sb_size_height_A_B"] 
    # p["sb_unit_A_B"] 
    
    # p["sb_position_x_C_D"], p["sb_position_y_C_D"] 
    # p["sb_size_width_C_D"], p["sb_size_height_C_D"] 
    # p["sb_unit_C_D"] 
    
    # p["diff_spots_circle_radius"] 
   
    # ####################### params specific to each subplot
    # #### A 
    # p["title_A"] 
    # p["im_limits_min_A"], p["im_limits_max_A"] 
    
    # p["aperture_circle_radius_A"]
    # p["aperture_circle_pos_x_A"], aperture_circle_pos_y_A
    # p["aperture_circle_label_A"] 
    
    # ####B
    # p["title_B"] 
    # p["im_limits_min_B"], p["im_limits_max_B"]
    
    # ####C
    # p["title_C"]
    # p["im_limits_min_C"], p["im_limits_max_C"] 
    # p["pg_center_x_C"], p["pg_center_y_C"] 
    # p["pg_width_C"], p["pg_height_C"] 
    # p["pg_angle_C"]
    # p["pg_rotation_angle_C"] 
    # # labeled spots in direction 1
    # p["line_start_dir1_x_C"], p["line_start_dir1_y_C"] 
    # p["line_end_dir1_x_C"], p["line_end_dir1_y_C"] 
    # p["n_diff_spot_circles_dir1_C"] # number of diffraction spot circles in the first direction
    # p["diff_spots_circle_labels_dir1_C"] =# labels for the diffraction spots in the first direction
    
    # p["diff_spot_for_DF_x_C"], p["diff_spot_for_DF_y_C"]
    
    # # labeled spots in direction 2
    # p["line_start_dir2_x_C"], p["line_start_dir2_y_C"] 
    # p["line_end_dir2_x_C"], p["line_end_dir2_y_C"] 
    # p["n_diff_spot_circles_dir2_C"] # number of diffraction spot circles in the second direction
    # p["diff_spots_circle_labels_dir2_C"] # labels for the diffraction spots in the second direction

    
    # ####D
    # p["title_D"] 
    # p["im_limits_min_D"], p["im_limits_max_D"] 
    # p["pg_center_x_D"], p["pg_center_y_D"] 
    # p["pg_width_D"], p["pg_height_D"] 
    # p["pg_angle_D"]
    # p["pg_rotation_angle_D"] 
    
    #  # labeled spots in direction 1
    # p["line_start_dir1_x_D"], p["line_start_dir1_y_D"]
    # p["line_end_dir1_x_D"], p["line_end_dir1_y_D"]
    # p["n_diff_spot_circles_dir1_D"]# number of diffraction spot circles in the first direction
    # p["diff_spots_circle_labels_dir1_D"] # labels for the diffraction spots in the first direction
    
    # # labeled spots in direction 2
    # p["line_start_dir2_x_D"], p["line_start_dir2_y_D"]
    # p["line_end_dir2_x_D"], p["line_end_dir2_y_D"] 
    # p["n_diff_spot_circles_dir2_D"]  # number of diffraction spot circles in the first direction
    # p["diff_spots_circle_labels_dir2_D"] # labels for the diffraction spots in the first direction
    
    
    ####################################################################################
   '''
    ### Load parameter values from JSON file with same name as script
    # Opening JSON file
    try:
        with open(__file__.split('.')[0] + '.json') as json_file:
            p = json.load(json_file)
    except Exception as e:
        print('Could not find JSON file with figure parameters')
        print(e)
        return
    ## handle any parameter values passed as **kwargs
    p.update((k, kwargs[k]) for k in p.keys() & kwargs.keys())

    
    root_path = r"C:\Users\Isac Lazar\OneDrive - Lund University\Dokument\Projekt\Chalmers Al-AM\data\JEOL3000F\2023-10-12\raw"
    im_nr1 = 150
    im_nr2 = 160
    im_nr3 = 221
    im_nr4 = 192
    
 
    im1, md1 = load_dm3_by_unique_number(root_path, im_nr1)
    im2, md2 = load_dm3_by_unique_number(root_path, im_nr2)
    im3, md3 = load_dm3_by_unique_number(root_path, im_nr3)
    im4, md4 = load_dm3_by_unique_number(root_path, im_nr4)
    
    im3 = square_crop(im3)
    im4 = square_crop(im4)
  


  
    
    fig = plt.figure(figsize=(6,6), dpi=150)
    axs = fig.subplots(2,2)

    #subplot 0,0 A
    curr_ax = axs[0,0]
    plot_image_with_physical_size(ax=curr_ax, im=im1, x_scale=md1['axis-1']['scale'], y_scale=md1['axis-0']['scale'],
                                  show_axis=False, cmap='gray', vmin=p["im_limits_min_A"], vmax=p["im_limits_max_A"])
    x_width = curr_ax.get_xlim()[1] -  curr_ax.get_xlim()[0] 
    y_width = curr_ax.get_ylim()[1] -  curr_ax.get_ylim()[0] 
    curr_ax.text(x=x_width*p["letter_label_x_padding_ratio"], y=y_width*(1- p["letter_label_y_padding_ratio"]), 
                s='A', ha='left', va='top', color='white', fontsize=p["titles_fs"])
    # create title text
    curr_ax.text(x=x_width*(1 - p["title_x_padding_ratio"]),y= y_width*(1 - p["title_y_padding_ratio"]), 
                 s=p["title_A"], ha='right', va='top', color='white', fontsize=p["titles_fs"])  


    # Call the function to create the scale bar and text
    create_scale_bar(curr_ax, position=(p["sb_position_x_A_B"], p["sb_position_y_A_B"]), size=(p["sb_size_width_A_B"], p["sb_size_height_A_B"]), 
                     unit=p["sb_unit_A_B"], fontsize=p["scale_bar_fs"])
    
    # add aperture circle 
    c = Circle((p["aperture_circle_pos_x_A"], p["aperture_circle_pos_y_A"]), radius=p["aperture_circle_radius_A"], 
               fill=False, color='r', linewidth=p["annotation_linewidths"])
    curr_ax.add_patch(c)
    # add annotation for aperture circle
    curr_ax.text(x=p["aperture_circle_pos_x_A"]+p["aperture_circle_radius_A"]*1.2, y=p["aperture_circle_pos_y_A"],
                 s=p["aperture_circle_label_A"], fontsize=p["annotation_fs"], color='w', ha='left', va='center')

    #subplot 0,1 B
    curr_ax = axs[0,1]
    plot_image_with_physical_size(ax=curr_ax, im=im2, x_scale=md2['axis-1']['scale'], y_scale=md2['axis-0']['scale'],
                                  show_axis=False, cmap='gray', vmin=p["im_limits_min_B"], vmax=p["im_limits_max_B"])
    x_width = curr_ax.get_xlim()[1] -  curr_ax.get_xlim()[0]
    y_width = curr_ax.get_ylim()[1] -  curr_ax.get_ylim()[0] 
    curr_ax.text(x=x_width*p["letter_label_x_padding_ratio"], y=y_width*(1- p["letter_label_y_padding_ratio"]), 
                s='B', ha='left', va='top', color='white', fontsize=p["titles_fs"])
     # create title text
    curr_ax.text(x=x_width*(1 - p["title_x_padding_ratio"]),y= y_width*(1 - p["title_y_padding_ratio"]), 
                 s=p["title_B"], ha='right', va='top', color='white', fontsize=p["titles_fs"])  


    # Call the function to create the scale bar and text
    create_scale_bar(curr_ax, position=(p["sb_position_x_A_B"], p["sb_position_y_A_B"]), size=(p["sb_size_width_A_B"], p["sb_size_height_A_B"]), 
                     unit=p["sb_unit_A_B"], fontsize=p["scale_bar_fs"])
   
    #subplot 1,0 C

    curr_ax = axs[1,0]
    plot_image_with_physical_size(ax=curr_ax, im=im3, x_scale=md3['axis-1']['scale'], y_scale=md3['axis-0']['scale'],
                                  show_axis=False, cmap='gray', vmin=p["im_limits_min_C"], vmax=p["im_limits_max_C"])
    x_width = curr_ax.get_xlim()[1] -  curr_ax.get_xlim()[0]
    y_width = curr_ax.get_ylim()[1] -  curr_ax.get_ylim()[0]
    curr_ax.text(x=x_width*p["letter_label_x_padding_ratio"], y=y_width*(1- p["letter_label_y_padding_ratio"]), 
                s='C', ha='left', va='top', color='white', fontsize=p["titles_fs"])
    # create title text
    
    curr_ax.text(x=x_width*(1 - p["title_x_padding_ratio"]),y= y_width*(1 - p["title_y_padding_ratio"]), 
                 s=p["title_C"], ha='right', va='top', color='white', fontsize=p["titles_fs"])  



    # Call the function to create the scale bar and text
    create_scale_bar(curr_ax, position=(p["sb_position_x_C_D"], p["sb_position_y_C_D"]), size=(p["sb_size_width_C_D"], p["sb_size_height_C_D"]), 
                     unit=p["sb_unit_C_D"], fontsize=p["scale_bar_fs"])
    # create parallelogram indicating reciprocal unit cell
    create_parallelogram(ax=curr_ax, center=(p["pg_center_x_C"], p["pg_center_y_C"]), width=p["pg_width_C"], height=p["pg_height_C"], 
                              smallest_angle=p["pg_angle_C"], rotation_angle=p["pg_rotation_angle_C"], edgecolor='white', linewidth=p["annotation_linewidths"])

    
    # index a few diffraction spots along one direction
    plot_circles_along_line(curr_ax, line_start=(p["line_start_dir1_x_C"], p["line_start_dir1_y_C"]), line_end=(p["line_end_dir1_x_C"], p["line_end_dir1_y_C"]), 
                            n_circles=p["n_diff_spot_circles_dir1_C"], labels=p["diff_spots_circle_labels_dir1_C"], radius=p["diff_spots_circle_radius"], 
                            plot_line=False, fill=False, fontsize=p["annotation_fs"], linewidth=p["annotation_linewidths"], color='white')
    
    # add a red circle indicating the diffraction spot used for DF TEM
    c = Circle((p["diff_spot_for_DF_x_C"], p["diff_spot_for_DF_y_C"]), radius=p["diff_spots_circle_radius"], 
               linewidth=p["annotation_linewidths"],fill=False, color='r')
    curr_ax.add_patch(c)
    curr_ax.text(x=p["diff_spot_for_DF_x_C"]-0.45, y=p["diff_spot_for_DF_y_C"], s='DF TEM', fontsize=p["annotation_fs"], color='white', ha='right', va='center' )

        

    plot_circles_along_line(curr_ax, line_start=(p["line_start_dir2_x_C"], p["line_start_dir2_y_C"]), line_end=(p["line_end_dir2_x_C"], p["line_end_dir2_y_C"]), n_circles=p["n_diff_spot_circles_dir2_C"], 
                            labels=p["diff_spots_circle_labels_dir2_C"], radius=p["diff_spots_circle_radius"], plot_line=False, fill=False, 
                            color='white', fontsize=p["annotation_fs"], linewidth=p["annotation_linewidths"])
    
    

    ## subplot 1,1 D
    curr_ax = axs[1,1]
    plot_image_with_physical_size(ax=curr_ax, im=im4, x_scale=md4['axis-1']['scale'], y_scale=md4['axis-0']['scale'],
                                  show_axis=False, cmap='gray', vmin=p["im_limits_min_D"], vmax=p["im_limits_max_D"])
    x_width = curr_ax.get_xlim()[1] -  curr_ax.get_xlim()[0]
    y_width = curr_ax.get_ylim()[1] -  curr_ax.get_ylim()[0]
    curr_ax.text(x=x_width*p["letter_label_x_padding_ratio"], y=y_width*(1- p["letter_label_y_padding_ratio"]), 
                s='D', ha='left', va='top', color='white', fontsize=p["titles_fs"])
    #create title text
    curr_ax.text(x=x_width*(1 - p["title_x_padding_ratio"]),y= y_width*(1 - p["title_y_padding_ratio"]), 
                 s=p["title_D"], ha='right', va='top', color='white', fontsize=p["titles_fs"])  


    # Call the function to create the scale bar and text
    create_scale_bar(curr_ax, position=(p["sb_position_x_C_D"], p["sb_position_y_C_D"]), size=(p["sb_size_width_C_D"], p["sb_size_height_C_D"]), 
                     unit=p["sb_unit_C_D"], fontsize=p["scale_bar_fs"])

    create_parallelogram(ax=curr_ax,center=(p["pg_center_x_D"], p["pg_center_y_D"]), width=p["pg_width_D"], height=p["pg_height_D"], smallest_angle=p["pg_angle_D"], 
                            rotation_angle=p["pg_rotation_angle_D"], edgecolor='white', linewidth=p["annotation_linewidths"])

    
   
    plot_circles_along_line(curr_ax, line_start=(p["line_start_dir1_x_D"], p["line_start_dir1_y_D"]), line_end=(p["line_end_dir1_x_D"], p["line_end_dir1_y_D"]),
                            n_circles=p["n_diff_spot_circles_dir1_D"], 
                            labels=p["diff_spots_circle_labels_dir1_D"], radius=p["diff_spots_circle_radius"], plot_line=False, 
                            fill=False, color='white', linewidth=p["annotation_linewidths"], fontsize=p["annotation_fs"])


        
 
    plot_circles_along_line(curr_ax, line_start=(p["line_start_dir2_x_D"], p["line_start_dir2_y_D"]), line_end=(p["line_end_dir2_x_D"], p["line_end_dir2_y_D"]), n_circles=p["n_diff_spot_circles_dir2_D"], 
                            labels=p["diff_spots_circle_labels_dir2_D"], radius=p["diff_spots_circle_radius"], plot_line=False, fill=False, 
                            color='white', fontsize=p["annotation_fs"], linewidth=p["annotation_linewidths"])
   

    fig.tight_layout()
    #plt.show()
    out_path = r"C:\Users\Isac Lazar\Documents\Software\chalmers_al_am\chalmers_al_am\out"

    plt.savefig(os.path.join(out_path, 'BF_DF_SAED310_SAED594.png'), dpi=600)
    plt.savefig(os.path.join(out_path, 'BF_DF_SAED310_SAED594.svg'), dpi=600)
    plt.rcParams['svg.fonttype'] = 'none' # making sure texts are saved as texts and not paths. This assumes that the machine opening the svg file has the font installed
    plt.savefig(os.path.join(out_path, 'BF_DF_SAED310_SAED594_editable_text.svg'), dpi=600)
    
#%%
if __name__ == '__main__':
    BF_DF_SAED310_SAED594()
    #interactive_plotting(BF_DF_SAED310_SAED594, ['im_limits_min_A', 'im_limits_max_A'],
                        # [(-1000, 1000, 10), (0, 3000, 10)])
# %%
