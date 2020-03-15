import util
from biology import BioAssumptions

from random import random, gauss
from math import inf as INF

class Critter:

    # default starting values
    TRAITS = {
        'per_critter': 10,                    # need constraint (complexity?)
        'per_food': 10,
        'wander_effort': 0.9,               # percent of max speed Critter moves at when no goal in sight

        'mass': 10,
        'reproduction_threshold': 0.1,      # percent of max energy at which Critter will reproduce
        'energy_inheritance': 0.15,         # percent of max energy passed on to each child
    }


    # coefficients of variation (SD/MEAN)
    MUTABILITY = {
        'per_critter': .008,
        'per_food': .008,
        'wander_effort': .008,
        'mass': .008,
        'reproduction_threshold': .008,
        'energy_inheritance': .008,
    }

    # upper and lower bounds past which values for the trait wouldn't make sense
    LIMITS = {
        'per_critter': (0,INF),
        'per_food': (0,INF),
        'wander_effort': (0,1),
        'mass': (util.epsilon,INF),
        'reproduction_threshold': (util.epsilon,1),
        'energy_inheritance': (0,1),
    }
    
    @classmethod
    def _get_default_traits():
        if hasattr(super(), "TRAITS"):
            return {**super()._get_default_traits(), **TRAITS}
        else:
            return TRAITS
    
    # Assemble default traits by pulling from each superclass up to Critter, with later definitions overriding
    TRAITS = __class__._get_default_traits()

    # used for any traits w/o defined CV in MUTABILITY
    DEFAULT_CV = .008
    # number of turns before the Critter dies
    MAX_AGE = 500


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

        # caches
        self._visible_critters_cache = (-1, [])
        self._visible_food_cache = (-1, [])

    def wipe_caches(self):
        del self._visible_critters_cache
        del self._visible_food_cache

    @property
    def visible_critters(self):
        turn, cached = self._visible_critters_cache
        if turn == self.world.turn:
            return cached
        else:
            found = []
            for critter in self.world.critters:
                rho = util.dist2(self.loc, critter.loc)
                if rho <= self.per_critter:
                    found.append( (rho, critter) )
            self._visible_critters_cache = (self.world.turn, found)
            return found

    @property
    def visible_food(self):
        turn, cached = self._visible_food_cache
        if turn == self.world.turn:
            return cached
        else:
            found = []
            for food in self.world.avail_food:
                rho = util.dist2(self.loc, food.loc)
                if rho <= self.per_food:
                    found.append( (rho, food) )
            self._visible_food_cache = (self.world.turn, found)
            return found

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, e):
        self._energy = min(e, self.max_energy)


    def __getattr__(self, name):
        # only called if *self* has no attribute *name*
        # allows traits to be referred to like properties w/o manually defining each
        if name in self.traits:
            return self.traits[name]
        else:
            raise AttributeError(name)


    #ACTIONS

    def act(self):
        self.energy -= self.metabolic_upkeep
        if self.energy >= self.reproduction_threshold:
            self.reproduce_asex()
        else:
            food_options = self.visible_food
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


    def reproduce_asex(self):
        energy_donation = min(self.energy, self.energy_inheritance * self.max_energy)
        self.energy -= energy_donation
        new_traits = self._clone()
        Subspecies = type(self)     # so that child is of the same subclass
        child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_donation)
        self.children.add(child)
        self.world.add_critter(child)


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

    def _visible_critters(self):
        # returns other critters within this critter's perception range and it's distance
        found = []
        for critter in self.world.search_critters(self.loc, self.per_critter):
            rho = util.dist2(self.loc, critter.loc)
            if rho <= self.per_critter:
                found.append((rho, critter))
        found.sort(key = lambda e: e[0])
        return found

    def _visible_food(self):
        # returns food within this critter's perception range and it's distance
        found = []
        for food in self.world.search_food(self.loc, self.per_food):
            rho = util.dist2(self.loc, food.loc)
            if rho <= self.per_food:
                found.append((rho, food))
        found.sort(key = lambda e: e[0])
        return found
