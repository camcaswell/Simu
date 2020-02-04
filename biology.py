from util import *

from math import log

def derive_reach(mass):
    # mass ~ length^3, reach is about half of length
    return 0.5 * cbrt(mass)

def derive_max_energy(mass):
    return 1.5 * mass

def derive_max_speed(mass):
    # https://www.sciencemag.org/news/2017/07/why-midsized-animals-are-fastest-earth
    # https://www.wolframalpha.com/input/?i=plot+%28-2%2F27%29x%5E3+-+%281%2F3%29x%5E2+%2B+%2817%2F9%29x+%2B+%28220%2F27%29
    # 1kg = 35 mass, 50km/hr = 10 speed
    x = log(mass/35)/log(10)
    return (-2/27)*x**3 - (1/3)*x**2 + (17/9)*x + (220/27)

def derive_metabolic_upkeep(mass):
    # https://en.wikipedia.org/wiki/Kleiber%27s_law
    return .15 * (mass ** (3./4))

def move_cost(mass, dist):
    # all moves happen in 1 turn, so distance is speed
    return .03 * mass * dist