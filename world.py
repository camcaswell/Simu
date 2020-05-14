from critter import Critter, Decisions, Results
from food import Food
from datavis import Data

from random import random, randint, sample, gauss
from math import inf as INF, ceil

class World:

    DESCRIPTION = "The default world"

    SIZE = 200                  # side length of square in which food can drop
    TURN_DURATION = 10          # affects the "resolution" of the sim; lower numbers mean fewer things happening per turn
    CHUNK_SIZE = 30             # quick n dirty testing suggests this is ~optimal

    def __init__(self, size=SIZE, food_drops=[]):
        self.size = size
        self.abundance = 1              # multiplier for mean food per area (useful for modifying food scarcity over time)
        self.food_drops = food_drops    # list of triplets: (constructor, mean drops/area/time, coefficient of variation)
        self.turn = 0
        self.species = set()
        
        self.critters = {}      # critters that exist in the world, by chunk
        self.avail_food = {}    # food that actually exists in the world, by chunk

        self.decisions = {}     # registers each critter's decision each turn
        self.results = {}       # registers results during and after resolving turn
        
        for x in range(int(self.SIZE/self.CHUNK_SIZE) + 1):
            for y in range(int(self.SIZE/self.CHUNK_SIZE) + 1):
                self.critters[(x,y)] = []
                self.avail_food[(x,y)] = []

    @property
    def all_critters(self):
        return [critter for chunk in self.critters.values() for critter in chunk]
                
    @property
    def pop_count(self):
        return sum([len(chunk) for chunk in self.critters.values()])

    @property
    def all_food(self):
        return [food for chunk in self.avail_food.values() for food in chunk]

    @property
    def food_count(self):
        return sum([len(chunk) for chunk in self.avail_food.values()])

    def add_critters(self, critters):
        for critter in critters:
            self.add_critter(critter)

    def add_critter(self, critter):
        self.critters[self.chunk_idx(critter.loc)].append(critter)
        self.species.add(critter.__class__)

    def add_critters(self, critters):
        for critter in critters:
            self.add_critter(critter)

    # CHUNKS
    def relocate(self, critter, new_loc):
        self.critters[self.chunk_idx(critter.loc)].remove(critter)
        self.critters[self.chunk_idx(new_loc)].append(critter)

    def untrack_critter(self, critter):
        self.critters[self.chunk_idx(critter.loc)].remove(critter)
        critter.wipe_caches()

    def untrack_food(self, food):
        self.avail_food[self.chunk_idx(food.loc)].remove(food)

    def chunk_normalize(self, coord):
        coord = max(0, min(self.SIZE, coord))
        return int(coord/self.CHUNK_SIZE)
            
    def chunk_idx(self, loc):
        x,y = loc
        return self.chunk_normalize(x), self.chunk_normalize(y)
    
    def search_critters(self, loc, search_range):
        x,y = loc
        up_idx =    self.chunk_normalize(y+search_range)
        down_idx =  self.chunk_normalize(y-search_range)
        right_idx = self.chunk_normalize(x+search_range)
        left_idx =  self.chunk_normalize(x-search_range)
        return [c for i in range(left_idx, right_idx+1) for j in range(down_idx, up_idx+1) for c in self.critters[(i,j)]]
    
    def search_food(self, loc, search_range):
        x,y = loc
        up_idx =    self.chunk_normalize(y+search_range)
        down_idx =  self.chunk_normalize(y-search_range)
        right_idx = self.chunk_normalize(x+search_range)
        left_idx =  self.chunk_normalize(x-search_range)
        return [f for i in range(left_idx, right_idx+1) for j in range(down_idx, up_idx+1) for f in self.avail_food[(i,j)]]

    # FOOD
    def register_food_drop(self, food=None, mu=5, cv=0.2):
        if food is None:
            food = Food
        self.food_drops.append((food, mu, cv))

    def drop_food(self):
        for food, mu, cv in self.food_drops:
            size_modifier = self.SIZE**2 / 1000000  # div1000000 to avoid making the other numbers awkwardly small
            adjusted_mean = size_modifier * self.abundance * mu * self.TURN_DURATION
            drop_count = round(gauss(adjusted_mean, adjusted_mean*cv))
            for _ in range(drop_count):
                new_food = food(self)
                self.avail_food[self.chunk_idx(new_food.loc)].append(new_food)

    # ADMIN
    def step(self):

        self.turn += 1

        for food in self.all_food:
            food.take_turn()
        self.drop_food()

        self.decisions = {}
        self.results = {}
        turn_order = sample(self.all_critters, self.pop_count)  # random action order to make it fair
        for critter in turn_order:
            decision, target = critter.take_turn()
            self.decisions[critter] = (decision, target)
            critter.last_decision = decision
            critter.last_target = target

        for critter in turn_order:
            decision, target = self.decisions[critter]
            if decision is Decisions.PREDATE:
                result = critter.resolve_turn(decision, target)
                self.results[critter] = result
                critter.last_result = result
                if result is Results.SUCCESS:
                    self.results[target] = Results.KILLED

        for critter in turn_order:
            decision, target = self.decisions[critter]
            if critter not in self.results:     # if not hunting or already killed
                result = critter.resolve_turn(decision, target)
                self.results[critter] = result
                critter.last_result = result

    def report(self):
        for Species in self.species:
            print(f"\n{Species.__name__}")
            extant_group = [c for c in self.all_critters if isinstance(c, Species)]
            if extant_group:
                for trait in Species.START_TRAITS:
                    vals = [c.traits[trait] for c in extant_group]
                    print(f"\t{trait}: {sum(vals)/len(vals):.2f}")
                    #print(' '.join([f'{v:.2f}' for v in vals]))
            else:
                print("No surviving critters")

    def set_up_food(self):
        if not self.food_drops:
            self.register_food_drop()
        temp = self.abundance
        self.abundance *= 50
        self.drop_food()
        self.abundance = temp
        for food in self.all_food:
            food.amount_left = random() * food.DEFAULT_AMOUNT

    def get_generator(self, turn_limit = INF):
        while self.turn < turn_limit:
            yield self
            self.step()

def run():
    world = World()

    turns = 1000
    world.abundance = .6
    start_pop = 50

    world.set_up_food()
    world.add_critters([Critter(world, age=randint(0,Critter.MAX_AGE)) for _ in range(start_pop)])

    data = Data(turns)

    while world.turn < turns and 0 < (turn_pop := world.pop_count):
        print(f"{world.turn}: {turn_pop}")

        turn_pop = world.pop_count
        all_critters = world.all_critters
        all_food = world.all_food
        turn = world.turn

        data.pop[turn] = turn_pop
        data.avg_age[turn] = sum([c.age for c in all_critters]) / turn_pop
        #data.avg_generation[turn] = sum([c.generation for c in all_critters]) / turn_pop
        data.max_generation[turn] = max([c.generation for c in all_critters])

        data.avg_energy[turn] = sum([c.energy for c in all_critters]) / turn_pop
        data.food_energy[turn] = sum([f.amount_left for f in all_food])

        world.step()

    world.report()

if __name__=='__main__':
    run()
