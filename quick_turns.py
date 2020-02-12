import util

from random import sample, gauss

class MySpecies(Simon):
    def __init__(self, world, *args, **kwargs):
        super().__init__(world, *args, bio=MyBioAssumptions, **kwargs)

    # overwriting the default initial traits of my species
    TRAITS = {
        'per_simon': 10,                    # perception range of other simons, currently does nothing
        'per_food': 8,                      # perception range of food drops
        'wander_effort': 0.9,               # proportion of max speed Simon moves at when no goal in sight

        'mass': 20,                         # determines a lot of derived stats
        'reproduction_threshold': 0.4,      # proportion of max energy at which Simon will reproduce
        'energy_inheritance': 0.15,         # proportion of max energy passed on to each child
    }

    def act(self):
        food_options = []
        mate_options = []
        visible_simons = self._visible_simons()
        predators = [rho,p for rho,p in visible_simons if self._is_predator(p)]

        nearby_predators = [rho,p for rho,p in predators if rho<self.pred_range]
        if nearby_predators:
            self.flee()
        else:
            # compare food vs mate in reach
            limit = self.reach+util.epsilon
            nearby_food = [rho,f,v for rho,f,v in self._visible_food() if rho<=limit]
            nearby_mates = [rho, m, self._mate_eval(m) for rho,m in visible_simons if self._valid_mate(m) and rho<=limit]
            if nearby_food or nearby_mates:
                best_food = max(nearby_food, key=lambda e:e[2])
                best_mate = max(nearby_mates, key=lambda e:e[2])
                if best_food[2] > best_mate[2]:
                    self.reproduce_sex(best_mate[1])
                else:
                    self.eat(best_food[1])
            elif desire := self._find_desired() is not None:
                rho, phi, _, _ = desire
                self._move(min(rho-self.reach+util.epsilon, self.max_speed), phi)
            else:
                self.flee()

    def flee(self):
        self.flee_1()

    def flee_1(self):
        predators = [p for p in self.visible_simons if self._is_predator(p)]
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

    def flee_2(self):
        #normalize sum of interval sizes to ~80% of 2pi
        danger_arcs = []
        biggest_arc = 0
        for rho, pred in predators:
            phi = util.rel_phi(self.loc, pred.loc)
            arc = self._threat_eval(pred) / (rho ** (3.0/2))
            danger_arcs.append(phi, arc)
            biggest_arc = max(biggest_arc, arc)

        scale = 0.9*pi / sum([arc for _,arc in danger_arcs])    # scale so sum of arcs is 90% of circle
        intervals = [(phi-desperation*arc, phi+desperation*arc) for phi,arc in danger_arcs]
        safe_intervals = util.subtract_intervals(intervals)
        right, left = max(safe_intervals, key=lambda i: i[1]-i[0])
        return right + util.angle(right, left)/2

    def reproduce_sex(self, mate):
        energy_donation = min(self.energy, self.energy_inheritance * self.max_energy)
        self.energy -= energy_donation
        new_traits = self._combine_chromosomes(mate)
        Subspecies = type(Self)     # so that child is of the same subclass
        child = Subspecies(self.world, loc=self.loc, traits=new_traits, energy=energy_donation)
        self.children.add(child)
        mate.children.add(child)
        self.world.add_simon(child)



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

    def _find_desired(self):
        if self.energy >= self.reproduction_threshold:
            mate_options = [r, util.rel_phi(m.loc), m, self._mate_eval(m) for r,m in self.visible_simons if self._valid_mate(m)]
        else:
            mate_options = []
        food_options = [r, util.rel_phi(f.loc), f, self._food_eval(f) for r,f in self.visible_food]
        predators = [r, util.rel_phi(p.loc), p, self._threat_eval(p) for r,p in self.visible_simons if self._is_predator(p)]
        desire = {}

        for rho, heading, target, value in mate_options + food_options:
            desire[(rho, heading, target, value)] = 0

            # summing food
            for rho, phi, _, value in food_options:
                ang = util.angle(heading, phi)
                desire[(rho, heading, target, value)] += value/( (ang/self.nav_angleoffset_food) + (rho/self.nav_distance_food) )

            # adding value of best mate option
            best_mate_value = 0
            for rho, phi, _, value in mate_options:
                ang = util.angle(heading, phi)
                adj_val = value/( (ang/self.nav_angleoffset_mate) + (rho/self.nav_distance_mate) )
                best_mate_value = max(best_mate_value, adj_val)
            desire[(rho, heading, target, value)] += best_mate_value

            # subtracting predator influence
            for rho, phi, _, threat in predators:
                ang = util.angle(heading, phi)
                desire[(rho, heading, target, value)] -= threat/( (ang/self.nav_angleoffset_pred) + (rho/self.nav_distance_pred) )

        # if every mate and food item is covered by a predator and we're not feeling brave
        if all([val<0 for val in desire.values()]):
            return None
        else:
            return max(desire, key=lambda k: desire[k])

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
