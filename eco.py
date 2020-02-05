from simon import Simon
from world import World, Fruit

class MyWorld(World):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def step(self):
        # Example for how to overwrite the method of the base class to modify it
        if self.turn < 1000 and self.turn%50 == 0:
            self.abundance -= 1
        super().step()





def main():
    world = MyWorld()
    world.create_simons()
    while world.turn < 1000:
        world.step()
        print(f"{world.turn}: {len(world.simons)}")
        if len(world.simons) == 0:
            break
    world.report()