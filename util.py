from math import hypot, atan2, cos, sin, pi
from random import uniform

# arithmetic

def cbrt(n):
    return n ** (1. / 3)

#larger than machine precision, small enough
epsilon = 0.00000000001


#geometry

def dist2(c1, c2):
    x1,y1 = c1
    x2,y2 = c2
    return hypot(x2-x1, y2-y1)

def c2p(c):
    x,y = c
    rho = hypot(x, y)
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

def rel_phi(me, other):
    x1,y1 = me
    x2,y2 = other
    return atan2(y2-y1, x2-x1)

def rand_phi():
    return uniform(-pi, pi)
