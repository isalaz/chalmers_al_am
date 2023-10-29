#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
#This scripts registers (aligns) all the images in a stack, to correct for sample drift during the experiment.
# By default, registration is based on the elemental maps of Mn_Ka
# It uses three different strategies for registration
# (1) Cross correlation by openCVs findTransformECC()
# If (1) does not converge, the script looks for the files points1.csv and points2.csv. These should contain coordinates of points
# on two successive images, that are determined to be the same sample coordinate. This is strategy (2).
# Based on the points1 and point2, we calculate an initial guess for the transformation matrix that is then fed to the findTransformECC algorithm()
#If (1) still fails, the initial guess is used for the final transform.
# If (1) fails, and there are no points1 and points2 files, it falls back to the 3rd option
# (3) Using feature detection with openCV ORB detection. The transform found by this method is then fed to (1)
# If (1) fails when being fed with the transform from (3) the script does not align the stack and produces an error.

# Finally, the transformations are applied to pixel_times and pixel_heating_times as well.

# stack_registration()
# cross_correlation()
# manual_points()
# ORB()
# concat_transforms()
# register_stack()

