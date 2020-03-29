class Food:

    def __init__(self, world, amount, loc=None):
        self.world = world
        if loc is None:
            loc = (random()*world.size, random()*world.size)
        self.loc = loc
        self.amount_left = amount

    def take_turn(self):
        self.deteriorate()

    def deteriorate(self):
        self.deplete(max(0.02 * self.amount_left, 0.01))

    def bite(self, size):
        size = min(size, self.amount_left)
        self.deplete(size)
        return size

    def deplete(self, size):
        self.amount_left -= size
        if self.amount_left <= 0:
            self.world.untrack_food(self)