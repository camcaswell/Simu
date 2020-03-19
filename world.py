from critter import Critter
import datavis

from random import random, randint, sample, gauss
from math import inf as INF, ceil

class Food:
    def __init__(self, world, loc=None, kind=None, amount=10, good_for=100):
        self.world = world
        if not loc:
            loc = (random()*world.size, random()*world.size)
        self.loc = loc
        self.kind = kind
        self.amount = amount
        self.expiration = world.turn + good_for


class World:

    SIZE = 100                  # side length of square in which food can drop
    TURN_DURATION = 10          # unitless; affects the "resolution" of the sim; lower numbers mean fewer things happening per turn
    CHUNK_SIZE = 10

    def __init__(self, size=SIZE, food_drops=[]):
        self.size = size
        self.abundance = 1              # multiplier for mean food per area (useful for modifying food scarcity over time)
        self.food_drops = food_drops    # list of triplets: (constructor, mean drops/turn/100 area, coefficient of variation)
        self.turn = 0
        self.critter_total = 0          # count of all critters over the existence of the world
        self.species = set()
        
        self.critters = {}      # critters that exist in the world, by chunk
        self.avail_food = {}    # food that actually exists in the world, by chunk
        
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
        self.critter_total += 1
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
    def register_food_drop(self, food=None, mu=7, cv=0.2):
        if food is None:
            food = Food
        self.food_drops.append((food, mu, cv))

    def drop_food(self):
        for food, mu, cv in self.food_drops:
            adjusted_mean = self.abundance * mu * self.TURN_DURATION / 100      # div100 just to avoid making the other numbers awkwardly small
            drop_count = round(gauss(adjusted_mean, adjusted_mean*cv))
            for _ in range(drop_count):
                new_food = food(self)
                self.avail_food[self.chunk_idx(new_food.loc)].append(new_food)

    def remove_expired(self):
        for chunk_list in self.avail_food.values():
            chunk_list = [f for f in chunk_list if f.expiration > self.turn]

    # ADMIN
    def step(self):
        self.turn += 1
        self.remove_expired()
        self.drop_food()
        for critter in sample(self.all_critters, self.pop_count):   # random action order to make it fair
            critter.act()
            critter.age += 1
            if critter.age > critter.max_age or critter.energy <= 0:
                critter._die()

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

    def set_up(self):
        self.register_food_drop()
        temp = self.abundance
        self.abundance /= 2
        for _ in range(10):     # spreading food with variety of ages before adding critters
            self.step()
        self.abundance = temp
        self.turn = 0
        print(self.food_count)

def run():
    world = World()
    world.set_up()

    world.add_critters([Critter(world) for _ in range(10)])

    pop_data = []

    while world.turn < 1000 and 0 < (turn_pop := world.pop_count):
        print(f"{world.turn}: {turn_pop}")
        pop_data.append(turn_pop)
        world.step()

    world.report()
    datavis.plot_pop(pop_data)

if __name__=='__main__':
    run()
