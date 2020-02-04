from math import sqrt, atan2, cos, sin, pi
from random import uniform

# arithmetic

def cbrt(n):
    return n ** (1. / 3)


#geometry

def dist2(c1, c2):
    return sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def c2p(c):
    x,y = c
    rho = sqrt(x**2 + y**2)
    phi = atan2(y, x)
    return (rho,phi)

def p2c(p):
    rho,phi = p
    x = rho * cos(phi)
    y = rho * sin(phi)
    return (x,y)

def rel_pol(me, other):
    #return polar coordinates of *other* with origin at *me*
    x1,y1 = me
    x2,y2 = other
    return c2p((x2-x1, y2-y1))

def rand_phi():
    return uniform(-pi, pi)
