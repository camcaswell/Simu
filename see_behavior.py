from world import World, Food
from critter import Critter, CustomCritterMeta
from datavis import Data
from animate import animate_world
import util

from numpy.random import vonmises   # approx. of normal distribution wrapped around the circle
from math import inf as INF

def main():

    turns = 1000
    size = 600
    world = World(size=size)

    lr = LabRat(world, loc=(size/2,size/2))
    world.add_critter(lr)

    animate_world(world, turns)



class LabRat(Critter):

    START_TRAITS = {
        'wander_effort': 1,
        'wander_faith': 40,
    }

    LIMITS = {
        'wander_faith': (0, INF)
    }

    def __init__(self, world, **kwargs):
        self.last_heading = 0
        super().__init__(world, **kwargs)


    def act(self):
        self.energy = INF
        self.age = 0
        self.wander()

    def wander(self):
        phi = util.wrap_angle(self.last_heading + vonmises(0, self.wander_faith))
        rho = self.wander_effort * self.max_speed
        self._move(rho, phi)

    def _move(self, rho, phi):
        super()._move(rho, phi)
        self.last_heading = phi







if __name__ == '__main__':
    main()