from util import *
from simon import *

#import networkx as nx
from random import random, randint, shuffle, gauss
from math import inf as INF

class Fruit:
    def __init__(self, world, loc=None, kind=None, amount=10, good_for=10):
        self.world = world
        if not loc:
            loc = (random()*world.size, random()*world.size)
        self.loc = loc
        self.kind = kind
        self.amount = amount
        self.expiration = world.turn + good_for


class World:

    ABUNDANCE = 50      # max fruit per 100^2 area
    SIGMA = 0.7         # standard deviation of fruit drops
    SIZE = 100          # side length of square in which fruit can drop


    def __init__(self, size=SIZE, abundance=ABUNDANCE, sigma=SIGMA, simons=None):
        if not simons:
            simons = set()
        self.size = size
        self.abundance = abundance
        self.sigma = sigma
        self.simons = simons
        self.all_simons = set()
        self.fruits = set()
        self.turn = 0

    def create_simons(self, count=10):
        for _ in range(count):
            Simon(self, energy=10)

    def track(self, simon):
        self.simons.add(simon)
        #self.all_simons.add(simon)

    def untrack(self, simon):
        self.simons.remove(simon)

    def fruit_drops(self):
        mu = self.abundance * (100**2/self.size**2)
        return int(gauss(mu, self.sigma))

    def step(self):

        self.turn += 1

        if self.turn < 1000 and self.turn%40 == 0:
            self.abundance -= 1

        for _ in range(self.fruit_drops()):
            self.fruits.add(Fruit(self))

        self.fruits = {f for f in self.fruits if f.expiration > self.turn}

        simons = list(self.simons)
        shuffle(simons)                 # random action order to make it fair
        for simon in simons:
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
    world.create_simons()
    while world.turn < 50000:
        world.step()
        print(f"{world.turn}: {len(world.simons)}")
        if len(world.simons) == 0:
            break

    world.report()

if __name__=='__main__':
    run()