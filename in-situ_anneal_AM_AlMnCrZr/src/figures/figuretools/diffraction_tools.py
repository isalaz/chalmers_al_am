import numpy as np
def angle_vectors_general(u, v, a, b, c):
    '''a, b, and c are lattice vectors in euclidean space
    u and v are vectors with miller indices'''
    V = np.dot(a, np.cross(b,c))
    a_ = np.cross(b,c)/V
    b_ = np.cross(c,a)/V
    c_ = np.cross(a,b)/V
    
    u_ = u[0]*a_ + u[1]*b_ + u[2]*c_
    v_ = v[0]*a_ + v[1]*b_ + v[2]*c_
    
    angle = np.rad2deg(np.arccos(np.dot(u_, v_)/(np.linalg.norm(u_)*np.linalg.norm(v_))))
    if angle > 90:
        return 180-angle
    return angle
def cubic_lattice(a):
    a_vector = a*np.array([1, 0, 0])
    b_vector = a*np.array([0, 1, 0])
    c_vector = a*np.array([0, 0, 1])
    return a_vector, b_vector, c_vector
def orthorombic_lattice(a, b, c):
    a_vector = a*np.array([1, 0, 0])
    b_vector = b*np.array([0, 1, 0])
    c_vector = c*np.array([0, 0, 1])
    return a_vector, b_vector, c_vector
    