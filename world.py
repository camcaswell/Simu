from simon import Simon

from random import random, randint, sample, gauss
from math import inf as INF

class Food:
    def __init__(self, world, loc=None, kind=None, amount=10, good_for=10):
        self.world = world
        if not loc:
            loc = (random()*world.size, random()*world.size)
        self.loc = loc
        self.kind = kind
        self.amount = amount
        self.expiration = world.turn + good_for


class World:

    SIZE = 100                      # side length of square in which food can drop

    def __init__(self, size=SIZE, food_drops=[], simons=[]):
        if simons is None:
            simons = set()
        self.size = size
        self.abundance = 1              # multiplier for mean food per area (useful for modifying food scarcity over time)
        self.food_drops = food_drops    # list of triplets: (constructor, mean drops/turn/100 area, coefficient of variation)
        self.avail_food = []            # food that actually exists in the world
        self.simons = simons
        self.turn = 0

    def add_simons(self, simons):
        self.simons += simons

    def add_simon(self, simon):
        self.simons.append(simon)
        #self.all_simons.add(simon)

    def untrack(self, simon):
        self.simons.remove(simon)

    def register_food_drop(self, food=None, mu=15, cv=0.2):
        if food is None:
            food = Food
        self.food_drops.append((food, mu, cv))

    def drop_food(self):
        for food, mu, cv in self.food_drops:
            adjusted_mean = self.abundance * mu
            drop_count = int(gauss(adjusted_mean, adjusted_mean*cv))
            new_drops = [food(self) for _ in range(drop_count)]
            self.avail_food += new_drops

    def remove_expired(self):
        self.avail_food = [f for f in self.avail_food if f.expiration > self.turn]


    def step(self):
        self.turn += 1
        self.remove_expired()
        self.drop_food()    
        for simon in sample(self.simons, len(self.simons)):   # random action order to make it fair
            simon.act()
            simon.age += 1
            if simon.age > simon.max_age or simon.energy <= 0:
                simon._die()

    def report(self, trait=None):
        if not self.simons:
            print("No survivors")
            return
        if trait is None:
            for t in self.simons.pop().traits:
                self.report(t)
        else:
            vals = [s.traits[trait] for s in self.simons]
            print(f"\n{trait}: {sum(vals)/len(vals):.2f}")
            #print(' '.join([f'{v:.2f}' for v in vals]))

def run():
    world = World()
    world.register_food_drop()

    # spreading food
    for _ in range(10):
        world.step()
    world.turn = 0

    world.add_simons([Simon(world) for _ in range(40)])
    print(world.simons)

    while world.turn < 1000 and len(world.simons) > 0:
        world.step()
        print(f"{world.turn}: {len(world.simons)}")

    world.report()

if __name__=='__main__':
    run()