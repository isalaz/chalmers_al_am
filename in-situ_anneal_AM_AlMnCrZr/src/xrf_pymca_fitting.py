#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
#This script creates elemental maps (tiff images) from xrf datasets (both ID16B and P06), by fitting the peaks of X-ray emissions
# It uses pymca for fitting, and thus requires a pymca .config file that describes the experiment and sample geometry, and the fitting parameters.
#The config file also includes what elements to be included in the fit. It is assumed that one config file is present in each sample directory. 
# If it is provided, this is overriden.
# setup_pymca()
#xrf_pymca_fitting()