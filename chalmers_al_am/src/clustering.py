#
# Created on Sun Oct 29 2023
#
# by Isac Lazar
#
# This script performs clustering on the registered stacks of elemental maps. It is based on that every pixel in the registered stack is a part of a time series
# Thus it segments each stack into spatial regions that show similar behavior over time.
# Saves the labels as labels.npy
# Based on a JSON file, an X number of clusters will be computed.
# clustering()
# KMeans()
# Hierarchical() # maybe implement sometime