from critter import Critter

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
        if critters is None:
            critters = set()
        self.size = size
        self.abundance = 1              # multiplier for mean food per area (useful for modifying food scarcity over time)
        self.food_drops = food_drops    # list of triplets: (constructor, mean drops/turn/100 area, coefficient of variation)
        self.turn = 0
        self.critter_total = 0
        
        self.critters = {}      # critters that exist in the world, by chunk
        self.avail_food = {}    # food that actually exists in the world, by chunk
        
        for x in range(int(self.SIZE/self.CHUNK_SIZE)):
            for y in range(int(self.SIZE/self.CHUNK_SIZE)):
                self.critters[(x,y)] = []
                self.avail_food[(x,y)] = []
                
    @property
    def pop_count(self):
        return sum([len(chunk_list) for chunk_list in self.critters.values()])

    def add_critters(self, critters):
        for critter in critters:
            self.add_critter(critter)

    def add_critter(self, critter):
        self.critters[self.chunk_idx(critter.loc)].append(critter)
        self.critter_total += 1

    def add_critters(self, critters):
        for critter in critters:
            self.add_critter(critter)

    def untrack(self, critter):
        self.critters[self.chunk_dx(critter.loc)].remove(critter)
        critter.wipe_caches()

    def register_food_drop(self, food=None, mu=15, cv=0.2):
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

    def step(self):
        self.turn += 1
        self.remove_expired()
        self.drop_food()
        all_critters = [critter for chunk_list in self.critters for critter in chunk_list]
        for critter in sample(all_critters, len(all_critters)):   # random action order to make it fair
            critter.act()
            critter.age += 1
            if critter.age > critter.max_age or critter.energy <= 0:
                critter._die()

    def report(self, trait=None):
        if not self.critters:
            print("No survivors")
            return
        if trait is None:
            for t in self.critters.pop().traits:
                self.report(t)
        else:
            vals = [s.traits[trait] for s in self.critters]
            print(f"\n{trait}: {sum(vals)/len(vals):.2f}")
            #print(' '.join([f'{v:.2f}' for v in vals]))
            
    def chunk_idx(self, loc):
        x,y = loc
        return int(x/self.CHUNK_SIZE), int(y/self.CHUNK_SIZE)
    
    def search_critters(self, loc, search_range):
        x,y = loc
        up_idx =    int((y+search_range)/self.SIZE)
        down_idx =  int((y-search_range)/self.SIZE)
        right_idx = int((x+search_range)/self.SIZE)
        left_idx =  int((x-search_range)/self.SIZE)
        return [c for i in range(left_idx, right_idx+1) for j in range(down_idx, up_idx+1) for c in self.critters[(i,j)]]
    
    def search_food(self, loc, search_range):
        x,y = loc
        up_idx = int((y+search_range)/self.SIZE)
        down_idx = int((y-search_range)/self.SIZE)
        right_idx = int((x+search_range)/self.SIZE)
        down_idx = int((x-search_range)/self.SIZE)
        return [f for i in range(left_idx, right_idx+1) for j in range(down_idx, up_idx+1) for f in self.avail_food[(i,j)]]

def run():
    world = World()
    world.register_food_drop()

    # spreading food
    for _ in range(10):
        world.step()
    world.turn = 0

    world.add_critters([Critter(world) for _ in range(40)])

    while world.turn < 1000 and world.pop_count > 0:
        world.step()
        print(f"{world.turn}: {world.pop_count}")

    world.report()

if __name__=='__main__':
    run()
