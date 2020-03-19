import util
from biology import BioAssumptions

from random import random, gauss, sample
from math import inf as INF, pi

class CustomCritterMeta(type):

    def __init__(cls, clsname, bases, attrdict):
        super().__init__(clsname, bases, attrdict)
        for SuperSpecies in bases:
            if hasattr(SuperSpecies, 'TRAITS'):
                cls.START_TRAITS = {**SuperSpecies.START_TRAITS, **cls.START_TRAITS}
            if hasattr(SuperSpecies, 'MUTABILITY'):
                cls.MUTABILITY = {**SuperSpecies.MUTABILITY, **cls.MUTABILITY}
            if hasattr(SuperSpecies, 'LIMITS'):
                cls.LIMITS = {**SuperSpecies.LIMITS, **cls.LIMITS}

class Critter(metaclass=CustomCritterMeta):

    # default starting values
    START_TRAITS = {
        'per_critter': 30,                  # perception range of other critters
        'per_food': 25,                     # perception range of food drops
        'wander_effort': 0.9,               # proportion of max speed Critter moves at when no goal in sight

        'mass': 20,                         # determines a lot of derived stats
        'reproduction_threshold': 0.4,      # proportion of max energy at which Critter will reproduce
        'energy_inheritance': 0.15,         # proportion of max energy passed on to each child

        'flee_range': 5,

        'behav_weight_food': 1,
        'behav_weight_mate': 2,
        'behav_weight_predator': 3,

        'nav_angleoffset_food': 1,
        'nav_angleoffset_mate': 2,
        'nav_angleoffset_predator': 3,

        'nav_distance_food': 1,
        'nav_distance_mate': 2,
        'nav_distance_pred': 3,
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

    # used for any traits w/o defined CV in MUTABILITY
    DEFAULT_CV = .008
    # number of turns before the Critter dies
    MAX_AGE = 500


    #NITTY-GRITTY

    def __init__(self, world, energy=40, loc=None, age=0, max_age=None, traits=None, bio=BioAssumptions):

        self.world = world

        if loc is None:
            loc = (random()*world.size, random()*world.size)
        if max_age is None:
            max_age = self.MAX_AGE
        if traits is None:
            traits = self.START_TRAITS

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
            for critter in self.world.search_critters(self.loc, self.per_critter):
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
            for food in self.world.search_food(self.loc, self.per_food):
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
        if name == 'traits':
            raise AttributeError('traits')
            
        if name in self.traits:
            return self.traits[name]
        else:
            raise AttributeError(name)



    #ACTIONS

    def act(self):
        food_options = []
        mate_options = []
        visible_critters = self.visible_critters
        predators = [(rho,p) for rho,p in visible_critters if self._is_predator(p)]

        nearby_predators = [(rho,p) for rho,p in predators if rho<self.flee_range]
        if nearby_predators:
            self.flee()
        else:
            # compare food vs mate in reach
            limit = self.reach+util.epsilon
            nearby_food = [(rho, f, self._food_eval(f)) for rho,f in self.visible_food if rho<=limit]
            nearby_mates = [(rho, m, self._mate_eval(m)) for rho,m in visible_critters if self._valid_mate(m) and rho<=limit]
            best_food = max(nearby_food, key=lambda e:e[2], default=(0,0,0))
            best_mate = max(nearby_mates, key=lambda e:e[2], default=(0,0,0))
            if best_food[2] > 0 or best_mate[2] > 0:
                if best_food[2] > best_mate[2]:
                    self.eat(best_food[1])
                else:
                    self.reproduce_sex(best_mate[1])
            elif (desire := self.find_desired()) is not None:
                (rho, phi, _), score = desire
                if score > 0:
                    self._move(min(rho-self.reach+util.epsilon, self.max_speed), phi)
                else:
                    self.flee()
            else:
                if predators:
                    self.flee()
                else:
                    self.wander()

    def find_desired(self):
        if self.energy >= self.reproduction_threshold:
            mate_options = [(r, util.rel_phi(self.loc, m.loc), m, self._mate_eval(m)) for r,m in self.visible_critters if self._valid_mate(m)]
        else:
            mate_options = []
        food_options = [(r, util.rel_phi(self.loc, f.loc), f, self._food_eval(f)) for r,f in self.visible_food]
        predators = [(r, util.rel_phi(self.loc, p.loc), p, self._threat_eval(p)) for r,p in self.visible_critters if self._is_predator(p)]
        desire = {}

        for dist, heading, target, _ in mate_options + food_options:
            desire[(dist, heading, target)] = 0

            # summing food
            for rho, phi, _, value in food_options:
                ang = util.angle(heading, phi)
                desire[(dist, heading, target)] += value/( (ang/self.nav_angleoffset_food) + (rho/self.nav_distance_food) )

            # adding value of best mate option
            best_mate_value = 0
            for rho, phi, _, value in mate_options:
                ang = util.angle(heading, phi)
                adj_val = value/( (ang/self.nav_angleoffset_mate) + (rho/self.nav_distance_mate) )
                best_mate_value = max(best_mate_value, adj_val)
            desire[(dist, heading, target)] += best_mate_value

            # subtracting predator influence
            for rho, phi, _, threat in predators:
                ang = util.angle(heading, phi)
                desire[(dist, heading, target)] -= threat/( (ang/self.nav_angleoffset_predator) + (rho/self.nav_distance_pred) )

        # if every mate and food item is covered by a predator and we're not feeling brave
        if desire:
            best_option = max(desire, key=lambda k: desire[k])
            return best_option, desire[best_option]
        else:
            return None

    def flee(self):
        predators = [p for p in self.visible_critters if self._is_predator(p)]
        danger_arcs = []
        biggest_arc = 0
        for rho, pred in predators:
            phi = util.rel_phi(self.loc, pred.loc)
            arc = self._threat_eval(pred) / (rho ** (3.0/2))
            danger_arcs.append(phi, arc)
            biggest_arc = max(biggest_arc, arc)
        if biggest_arc >= pi:
            scale = pi/biggest_arc - util.epsilon    # scale down largest interval to at most 2pi-2ep
        else:
            scale = 1
        safe_intervals = []
        while not safe_intervals:
            intervals = [(phi-desperation*arc, phi+desperation*arc) for phi,arc in danger_arcs]
            safe_intervals = util.subtract_intervals(intervals)
            scale *= 0.8
        right, left = max(safe_intervals, key=lambda i: i[1]-i[0])
        return right + util.angle(right, left)/2

    def wander(self):
        phi = util.rand_phi()
        rho = self.wander_effort * self.max_speed
        self._move(rho, phi)


    def eat(self, food):
        assert util.dist2(self.loc, food.loc) <= self.reach
        self.energy += food.amount
        self.world.untrack_food(food)


    def reproduce_asex(self):
        energy_donation = min(self.energy, self.energy_inheritance * self.max_energy)
        self.energy -= energy_donation
        new_traits = self._clone()
        Subspecies = type(self)     # so that child is of the same subclass
        child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_donation)
        self.children.add(child)
        self.world.add_critter(child)

    def reproduce_sex(self, mate):
        energy_donation = min(self.energy, self.energy_inheritance * self.max_energy)
        self.energy -= energy_donation
        new_traits = self._combine_chromosomes(mate)
        Subspecies = type(self)     # so that child is of the same subclass
        child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_donation)
        self.children.add(child)
        mate.children.add(child)
        self.world.add_critter(child)


    #HELPERS

    def _move(self, rho, phi):
        assert rho <= self.max_speed
        self.energy -= self.bio.move_cost(self, rho)
        dx,dy = util.p2c((rho, phi))
        x,y = self.loc
        new_loc = (x+dx, y+dy)
        self.world.relocate(self, new_loc)
        self.loc = new_loc
        

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

    def _combine_chromosomes(self, mate):
        new_traits = {}
        num_traits = len(self.traits)
        self_chromosome = sample(range(num_traits), num_traits//2)
        for idx, trait in enumerate(self.traits):
            cv = self.MUTABILITY.get(trait, self.DEFAULT_CV)
            if idx in self_chromosome:
                mu = self.traits[trait]
            else:
                mu = mate.traits[trait]
            new_val = gauss(mu, mu*cv)
            if trait in self.LIMITS:
                lower,upper = self.LIMITS[trait]
                new_val = min(upper, max(lower, new_val))
            new_traits[trait] = new_val
        return new_traits

    def _die(self):
        self.world.untrack_critter(self)

    def _food_eval(self, food):
        return self.behav_weight_food * food.amount * 1  # something about the kind of food and own digestive system

    def _mate_eval(self, mate):
        return self.behav_weight_mate * 1   # something about sexual fitness of mate

    def _threat_eval(self, predator):
        return self.behav_weight_predator * 1   # maybe something about predator species/size

    def _is_predator(self, other):
        return False       # base on species of other

    def _valid_mate(self, mate):
        return (type(mate) is type(self)) and mate._is_adult()    # and other sex

    def _is_adult(self):
        return self.age > .2 * self.max_age