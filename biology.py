import util

from math import log

class BioAssumptions:

    @classmethod
    def derive_reach(cls, simon):
        # mass ~ length^3, reach is about half of length
        return 0.5 * util.cbrt(simon.mass)

    @classmethod
    def derive_max_energy(cls, simon):
        return 3 * simon.mass

    @classmethod
    def derive_max_speed(cls, simon):
        # https://www.sciencemag.org/news/2017/07/why-midsized-animals-are-fastest-earth
        # https://www.wolframalpha.com/input/?i=plot+%28-2%2F27%29x%5E3+-+%281%2F3%29x%5E2+%2B+%2817%2F9%29x+%2B+%28220%2F27%29
        # 1kg = 35 mass, 50km/hr = 10 speed
        x = log(simon.mass/35)/log(10)
        return (-2/27)*x**3 - (1/3)*x**2 + (17/9)*x + (220/27)

    @classmethod
    def derive_metabolic_upkeep(cls, simon):
        # https://en.wikipedia.org/wiki/Kleiber%27s_law
        return .07 * (simon.mass ** (3./4))

    @classmethod
    def move_cost(cls, simon, dist):
        # all moves happen in 1 turn, so distance is speed
        return .02 * simon.mass * dist

    @classmethod
    def repro_cost(cls, simon):
        # currently a flat proportion of max energy
        return 0.1 * simon.max_energy