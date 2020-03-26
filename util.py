from math import hypot, atan2, cos, sin, pi
from random import uniform

# arithmetic

def cbrt(n):
    return n ** (1. / 3)

epsilon = 0.00000000001  # larger than machine precision, small enough



# geometry

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

def angle(phi, psi):
    dif = abs(phi - psi)
    if dif > pi:
        return 2*pi - dif
    else:
        return dif

def wrap_angle(phi):
    # convert angle to [0, 2pi)
    return phi - 2*pi * (phi//(2*pi))


def subtract_intervals(intervals):
    # returns the intervals on the circle not covered by the input
    if not intervals:
        return [(0, 2*pi)]
    if any([left-right>=2*pi for right,left in intervals]):
        return []
    endpoints = [(0,0)]
    open_ints = 0
    for right,left in intervals:
        left = wrap_angle(left)
        right = wrap_angle(right)
        endpoints.append((left, -1))
        endpoints.append((right, 1))
        if right > left:
            open_ints += 1
    endpoints.sort(reverse=True)
    leftovers = []
    last_right = None
    while len(endpoints) > 0:
        e_p, open_inc = endpoints.pop()
        open_ints += open_inc
        if open_ints == 0:
            last_right = e_p
        elif last_right is not None:
            leftovers.append((last_right, e_p))
            last_right = None
    if open_ints == 0:
        leftovers[0] = (last_right, leftovers[0][1])
    return leftovers