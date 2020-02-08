import util
from biology import BioAssumptions

from random import random, gauss
from math import inf as INF

class Simon:

    # default starting values
    TRAITS = {
        'per_simon': 10,                    # need constraint (complexity?)
        'per_fruit': 10,
        'wander_effort': 0.5,               # percent of max speed Simon moves at when no goal in sight

        'mass': 35,
        'reproduction_threshold': 0.1,      # percent of max energy at which Simon will reproduce
        'energy_inheritance': 0.15,         # percent of max energy passed on to each child
    }

    # coefficients of variation (SD/MEAN)
    MUTABILITY = {
        'per_simon': .008,
        'per_fruit': .008,

        'mass': .008,
        'reproduction_threshold': .008,
    }

    LIMITS = {
        'per_simon': (0,INF),
        'per_fruit': (0,INF),
        'wander_effort': (0,1),
        'mass': (0,INF),
        'reproduction_threshold': (0,1),
        'energy_inheritance': (0,1),
    }

    # used for any traits w/o defined CV in MUTABILITY
    DEFAULT_CV = .008
    # number of turns before the Simon dies
    MAX_AGE = 20


    #NITTY-GRITTY

    def __init__(self, world, energy=0, loc=None, age=0, max_age=None, traits=None, bio=BioAssumptions):

        self.world = world

        if loc is None:
            loc = (random()*world.size, random()*world.size)
        if max_age is None:
            max_age = self.MAX_AGE
        if traits is None:
            traits = self.TRAITS

        self.loc = loc
        self._energy = energy
        self.age = age
        self.max_age = max_age
        self.traits = traits
        self.children = set()
        self.birth = world.turn
        self.bio = bio

        # derived traits
        self.reach = self.bio.derive_reach(self)
        self.max_speed = self.bio.derive_max_speed(self)
        self.max_energy = self.bio.derive_max_energy(self)
        self.metabolic_upkeep = self.bio.derive_metabolic_upkeep(self)




    def __getattr__(self, name):
        # only called if *self* has no attribute *name*
        # allows traits to be referred to like properties w/o manually defining each
        if name in self.traits:
            return self.traits[name]
        else:
            raise AttributeError

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, e):
        self._energy = min(e, self.max_energy)




    #ACTIONS

    def act(self):
        self.energy -= self.metabolic_upkeep
        if self.energy >= self.reproduction_threshold:
            self.reproduce()
        else:
            food_options = self._visible_food()
            if food_options:
                rho,nearest = food_options[0]
                phi = util.rel_phi(self.loc, nearest.loc)
                if rho <= self.max_speed:
                    self._move(rho, phi)
                    self.eat(nearest)
                else:
                    self._move(self.max_speed, phi)
            else:
                self.wander()


    def wander(self):
        phi = util.rand_phi()
        rho = self.wander_effort * self.max_speed
        self._move(rho, phi)


    def eat(self, food):
        assert util.dist2(self.loc, food.loc) <= self.reach
        self.energy += food.amount
        self.world.avail_food.remove(food)


    def reproduce(self):
        energy_passed_on = min(self.energy, self.energy_inheritance * self.max_energy)
        self.energy -= energy_passed_on
        new_traits = self._clone()
        Subspecies = type(self)     # so that child is of the same subclass
        child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_passed_on)
        self.children.add(child)
        self.world.add_simon(child)


    #HELPERS

    def _move(self, rho, phi):
        assert rho <= self.max_speed
        dx,dy = util.p2c((rho, phi))
        x,y = self.loc
        self.loc = (x+dx, y+dy)
        self.energy -= self.bio.move_cost(self, rho)

    def _clone(self):
        new_traits = {}
        for trait, val in self.traits.items():
            cv = self.MUTABILITY.get(trait, self.DEFAULT_CV)
            mu = self.traits[trait]
            new_val = gauss(mu, mu*cv)
            if trait in self.LIMITS:
                lower,upper = self.LIMITS[trait]
                new_val = max(min(upper, new_val), lower)
            new_traits[trait] = new_val
        return new_traits

    def _die(self):
        self.world.untrack(self)

    def _visible_simons(self):
        #returns other simons within this simon's perception range and it's distance
        found = []
        for simon in self.world.simons:
            rho,phi = util.rel_pol(self.loc, simon.loc)
            if rho <= self.per_simon:
                found.append(((rho,phi), simon))
        found.sort(key = lambda e: e[0][0])
        return found

    def _visible_food(self):
        # returns food within this simon's perception range and it's distance
        found = []
        for food in self.world.avail_food:
            rho,phi = util.rel_pol(self.loc, fruit.loc)
            if rho <= self.per_fruit:
                found.append(((rho,phi), fruit))
        found.sort(key = lambda e: e[0][0])
        return found

