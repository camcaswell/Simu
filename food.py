from random import random

class Food:

    DESCRIPTION = "The default food"

    DEFAULT_AMOUNT = 60

    def __init__(self, world, amount=DEFAULT_AMOUNT, loc=None):
        self.world = world
        if loc is None:
            loc = (random()*world.size, random()*world.size)
        self.loc = loc
        self.amount_left = amount
        self.original_amount = amount

    def take_turn(self):
        self.deteriorate()

    def deteriorate(self):
        self.deplete(0.0005*self.original_amount + 0.01*self.amount_left)

    def bite(self, size):
        size = min(size, self.amount_left)
        self.deplete(size)
        return size

    def deplete(self, size):
        self.amount_left -= size
        if self.amount_left <= 0:
            self.world.untrack_food(self)