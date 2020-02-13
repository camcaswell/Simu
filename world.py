from critter import Critter

from random import random, randint, sample, gauss
from math import inf as INF

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

    def __init__(self, size=SIZE, food_drops=[], critters=[]):
        if critters is None:
            critters = set()
        self.size = size
        self.abundance = 1              # multiplier for mean food per area (useful for modifying food scarcity over time)
        self.food_drops = food_drops    # list of triplets: (constructor, mean drops/turn/100 area, coefficient of variation)
        self.avail_food = []            # food that actually exists in the world
        self.critters = critters
        self.turn = 0
        self.critter_total = 0

    def add_critter(self, critter):
        self.critters.append(critter)
        #self.all_critters.add(critter)

    def add_critters(self, critters):
        for critter in critters:
            self.add_critter(critter)

    def untrack(self, critter):
        self.critters.remove(critter)
        critter.wipe_caches()

    def register_food_drop(self, food=None, mu=15, cv=0.2):
        if food is None:
            food = Food
        self.food_drops.append((food, mu, cv))

    def drop_food(self):
        for food, mu, cv in self.food_drops:
            adjusted_mean = self.abundance * mu * self.TURN_DURATION / 100      # div100 just to avoid making the other numbers awkwardly small
            drop_count = round(gauss(adjusted_mean, adjusted_mean*cv))
            new_drops = [food(self) for _ in range(drop_count)]
            self.avail_food += new_drops

    def remove_expired(self):
        self.avail_food = [f for f in self.avail_food if f.expiration > self.turn]


    def step(self):
        self.turn += 1
        self.remove_expired()
        self.drop_food()    
        for critter in sample(self.critters, len(self.critters)):   # random action order to make it fair
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

def run():
    world = World()
    world.register_food_drop()

    # spreading food
    for _ in range(10):
        world.step()
    world.turn = 0

    world.add_critters([Critter(world) for _ in range(40)])
    print(world.critters)

    while world.turn < 1000 and len(world.critters) > 0:
        world.step()
        print(f"{world.turn}: {len(world.critters)}")

    world.report()

if __name__=='__main__':
    run()