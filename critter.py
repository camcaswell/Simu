import util
from biology import BioAssumptions

from random import random, gauss, sample
from numpy.random import vonmises
from math import inf as INF, pi

class CustomCritterMeta(type):

    def __init__(cls, clsname, bases, attrdict):
        super().__init__(clsname, bases, attrdict)
        for SuperSpecies in bases:
            if hasattr(SuperSpecies, 'START_TRAITS'):
                cls.START_TRAITS = {**SuperSpecies.START_TRAITS, **cls.START_TRAITS}
            if hasattr(SuperSpecies, 'MUTABILITY'):
                cls.MUTABILITY = {**SuperSpecies.MUTABILITY, **cls.MUTABILITY}
            if hasattr(SuperSpecies, 'LIMITS'):
                cls.LIMITS = {**SuperSpecies.LIMITS, **cls.LIMITS}

class Critter(metaclass=CustomCritterMeta):

    # default starting values
    START_TRAITS = {
        'per_critter': 60,                  # perception range of other critters
        'per_food': 30,                     # perception range of food drops
        'wander_effort': 0.9,               # proportion of max speed Critter moves at when no goal in sight
        'wander_faith': 40,                 # how close they adhere to their previous heading when wandering

        'mass': 15,                         # determines a lot of derived stats
        'reproduction_threshold': 0.8,      # proportion of max energy at which Critter will reproduce
        'energy_inheritance': 0.5,         # proportion of max energy passed on to each child

        'flee_range': 5,

        'behav_weight_wander': .75,
        'behav_weight_flee': 0.8,
        'behav_weight_food': 2,
        'behav_weight_mate': 2,
        'behav_weight_predator': 3,
        'behav_weight_competitor': 30,

        'nav_angleoffset_food': 1,
        'nav_angleoffset_mate': 2,
        'nav_angleoffset_predator': 3,
        'nav_angleoffset_competitor': 3,

        'nav_distance_food': 1,
        'nav_distance_mate': 2,
        'nav_distance_pred': 3,
        'nav_distance_competitor': 1,
    }


    # coefficients of variation (SD/MEAN)
    MUTABILITY = {
        'per_critter': .015,
        'per_food': .015,
        'wander_effort': .015,
        'mass': .015,
        'reproduction_threshold': .015,
        'energy_inheritance': .015,
    }

    # upper and lower bounds past which values for the trait wouldn't make sense
    LIMITS = {
        'per_critter': (0,INF),
        'per_food': (0,INF),
        'wander_effort': (0,1),
        'wander_faith': (0, INF),
        'mass': (util.epsilon,INF),
        'reproduction_threshold': (util.epsilon,1),
        'energy_inheritance': (0,1),
    }

    # used for any traits w/o defined CV in MUTABILITY
    DEFAULT_CV = .015
    # number of turns before the Critter dies
    MAX_AGE = 300


    #NITTY-GRITTY

    def __init__(self, world, energy=None, loc=None, age=0, max_age=None, traits=None, bio=BioAssumptions, generation=0):

        self.world = world

        if loc is None:
            loc = (random()*world.size, random()*world.size)
        if max_age is None:
            max_age = self.MAX_AGE
        if traits is None:
            traits = self.START_TRAITS

        # facts
        self.bio = bio
        self.max_age = max_age
        self.traits = traits
        self.birth = world.turn
        self.generation = generation

        # state info
        self.loc = loc
        self.age = age
        self.offspring_traits = []     # holds traits of children during gestation
        self.gestation_timer = None    # countdown to giving birth
        self.last_heading = util.rand_phi()

        # derived traits
        self.reach = self.bio.derive_reach(self)
        self.max_speed = self.bio.derive_max_speed(self)
        self.max_energy = self.bio.derive_max_energy(self)
        self.metabolic_upkeep = self.bio.derive_metabolic_upkeep(self)

        if energy is None:
            energy = .5 * self.max_energy
        self._energy = energy

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
                if critter is self:
                    continue
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

    def take_turn(self):
        self.age += 1
        if self.gestation_timer is not None:
            self.gestation_timer -= 1
        self.act()

    def act(self):

        if self.gestation_timer is not None and self.gestation_timer <= 0:
            self.give_birth()
            return

        near_predators = [p for rho,p in self.visible_critters
                            if self._is_predator(p)
                            and rho < self.flee_range]
        if near_predators:
            self.flee()
            return

        food_desire = ((self.max_energy-self.energy)/self.max_energy) * self.behav_weight_food
        wander_desire = self.behav_weight_wander
        flee_desire = self.behav_weight_flee

        priorities = [(self.seek_food, food_desire), (self.wander, wander_desire), (self.flee, flee_desire)]

        if self._is_adult() and self.gestation_timer is None:
            mate_desire = (self.age/self.MAX_AGE) *  self.behav_weight_mate
            priorities.append((self.seek_mate, mate_desire))

        priorities.sort(key=lambda p:p[1], reverse=True)

        for action in [p for p,_ in priorities]:
            if decision := action() is not None:
                break
                #send action enum to world

    def seek_food(self):
        food_in_reach = [f for rho,f in self.visible_food if rho <= self.reach + util.epsilon]
        if food_in_reach:
            best_option = max(food_in_reach, key=lambda f: self._food_eval(f))
            self.eat(best_option)
            return 1
        else:
            food_options = [(r, self._rel_phi(f), self._food_eval(f))
                            for r,f in self.visible_food]
            predators =    [(r, self._rel_phi(p), self._threat_eval(p))
                            for r,p in self.visible_critters if self._is_predator(p)]
            competitors =  [(util.dist2(self.loc, c.loc), self._rel_phi(c), self._food_competition_eval(c))
                            for _,c in self.visible_critters if self._food_competitor(c)]
            desire = {}
            for dist, heading, _ in food_options:
                desire[(dist, heading)] = 0

                # summing value of food in this direction
                for rho, phi, value in food_options:
                    ang = util.angle(heading, phi)
                    desire[(dist, heading)] += value/( (ang/self.nav_angleoffset_food) + (rho/self.nav_distance_food) )

                # subtracting value of competitors in this direction
                for comp_dist, phi, competition in competitors:
                    ang = util.angle(heading, phi)
                    desire[(dist, heading)] -= competition/( (ang/self.nav_angleoffset_competitor) + (comp_dist/self.nav_distance_competitor) )

                # subtracting value of predators in this direction
                for rho, phi, threat in predators:
                    ang = util.angle(heading, phi)
                    desire[(dist, heading)] -= threat/( (ang/self.nav_angleoffset_predator) + (rho/self.nav_distance_pred) )

            if any(value > 0 for value in desire.values()):
                dist, heading = max(desire, key=lambda k: desire[k])
                self._move(min(dist-self.reach, self.max_speed), heading)
                return 1
            else:
                return None

    def seek_mate(self):
        mate_in_reach = [m for rho,m in self.visible_critters if self._valid_mate(m) and rho <= self.reach + util.epsilon]
        if mate_in_reach:
            best_option = max(mate_in_reach, key=lambda m: self._mate_eval(m))
            self.reproduce_sex(best_option)
            return 1
        else:
            predators =    [(r, self._rel_phi(p), self._threat_eval(p))
                            for r,p in self.visible_critters if self._is_predator(p)]
            desire = {}
            for dist, mate_option in [(r,m) for r,m in self.visible_critters if self._valid_mate(m)]:
                heading = self._rel_phi(mate_option)
                desire[(dist, heading)] = self._mate_eval(mate_option)/(dist/self.nav_distance_mate)

                # subtracting value of predators in this direction
                for rho, phi, threat in predators:
                    ang = util.angle(heading, phi)
                    desire[(dist, heading)] -= threat/( (ang/self.nav_angleoffset_predator) + (rho/self.nav_distance_pred) )

            if any(value > 0 for value in desire.values()):
                dist, heading = max(desire, key=lambda k: desire[k])
                self._move(min(dist-self.reach, self.max_speed), heading)
                return 1
            else:
                return None

    def flee(self):
        predators = [p for p in self.visible_critters if self._is_predator(p)]
        if not predators:
            return None
        danger_arcs = []
        biggest_arc = 0
        for rho, pred in predators:
            phi = self._rel_phi(pred)
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
        heading = right + util.angle(right, left)/2
        self._move(self.max_speed, heading)
        return 1

    def wander(self):
        phi = vonmises(self.last_heading, self.wander_faith)
        rho = self.wander_effort * self.max_speed
        self._move(rho, phi)
        return 1


    def eat(self, food):
        bite = min(food.amount, self.max_energy-self.energy)
        self.energy += bite
        food.deplete(bite)


    def reproduce_asex(self):
        self.energy -= self.bio.repro_cost(self)
        self.offspring_traits.append(self._clone())
        self.gestation_timer = self.bio.gestation_period(self)


    def reproduce_sex(self, mate):
        self.energy -= self.bio.repro_cost(self)
        self.offspring_traits.append(self._combine_chromosomes(mate))
        self.gestation_timer = self.bio.gestation_period(self)

    def give_birth(self):
        Subspecies = type(self)     # so that children are of the same subclass
        for new_traits in self.offspring_traits:
            energy_donation = min(self.energy, self.energy_inheritance * self.max_energy)
            self.energy -= energy_donation
            child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_donation, generation=self.generation+1)
            self.world.add_critter(child)
        self.offspring_traits = []
        self.gestation_timer = None


    #HELPERS

    def _move(self, rho, phi):
        rho = min(rho, self.max_speed)
        self.energy -= self.bio.move_cost(self, rho)
        dx,dy = util.p2c((rho, phi))
        x,y = self.loc
        new_loc = (x+dx, y+dy)
        self.world.relocate(self, new_loc)
        self.loc = new_loc
        self.last_heading = phi
        

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
        return self.behav_weight_food * food.amount * (self.max_energy/self.energy) * 1  # something about the kind of food and own digestive system

    def _mate_eval(self, mate):
        return self.behav_weight_mate * 1   # something about sexual fitness of mate

    def _threat_eval(self, predator):
        return self.behav_weight_predator * 1   # maybe something about predator species/size

    def _food_competition_eval(self, other):
        return self.behav_weight_competitor * 1

    def _is_predator(self, other):
        return False       # base on species of other

    def _food_competitor(self, other):
        return not self._is_predator(other)

    def _valid_mate(self, mate):
        return self._same_species(mate) and mate._is_adult() and (mate.gestation_timer is None)

    def _is_adult(self):
        return self.age > self.bio.adult_age(self)

    def _same_species(self, other):
        return type(self) is type(other)

    def _rel_phi(self, other):
        return util.rel_phi(self.loc, other.loc)