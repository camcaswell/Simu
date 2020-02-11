import util

from math import log

class BioAssumptions:

    @classmethod
    def derive_reach(cls, critter):
        # mass ~ length^3, reach is about half of length
        return 0.5 * util.cbrt(critter.mass)

    @classmethod
    def derive_max_energy(cls, critter):
        return 3 * critter.mass

    @classmethod
    def derive_max_speed(cls, critter):
        # https://www.sciencemag.org/news/2017/07/why-midsized-animals-are-fastest-earth
        # https://www.wolframalpha.com/input/?i=plot+%28-2%2F27%29x%5E3+-+%281%2F3%29x%5E2+%2B+%2817%2F9%29x+%2B+%28220%2F27%29
        # 1kg = 35 mass, 50km/hr = 10 speed
        x = log(critter.mass/35)/log(10)
        return (-2/27)*x**3 - (1/3)*x**2 + (17/9)*x + (220/27)

    @classmethod
    def derive_metabolic_upkeep(cls, critter):
        # https://en.wikipedia.org/wiki/Kleiber%27s_law
        return .07 * (critter.mass ** (3./4))

    @classmethod
    def move_cost(cls, critter, dist):
        # all moves happen in 1 turn, so distance is speed
        return .02 * critter.mass * dist

    @classmethod
    def repro_cost(cls, critter):
        # currently a flat proportion of max energy
        return 0.1 * critter.max_energy