from biology import BioAssumptions
from simon import Simon
from world import World, Food
import util

class MyBioAssumptions(BioAssumptions):
    # this class is just a container for methods encoding assumptions about how biology works

    # overwrite methods to change how biology works in your sim
    @classmethod
    def move_cost(cls, simon, dist):
        return 0.1 * simon.mass * dist

    @classmethod
    def derive_metabolic_upkeep(cls, simon):
        return .5 * super().derive_metabolic_upkeep(simon)


class MySpecies(Simon):
    def __init__(self, world, *args, **kwargs):
        super().__init__(world, *args, bio=MyBioAssumptions, **kwargs)

    # overwriting the default initial traits of my species
    TRAITS = {
        'per_simon': 10,                    # perception range of other simons, currently does nothing
        'per_food': 8,                      # perception range of food drops
        'wander_effort': 0.9,               # proportion of max speed Simon moves at when no goal in sight

        'mass': 20,                         # determines a lot of derived stats
        'reproduction_threshold': 0.4,      # proportion of max energy at which Simon will reproduce
        'energy_inheritance': 0.15,         # proportion of max energy passed on to each child
    }

    def act(self):
        if self.age < .2 * self.max_age:
            self._act_juv()
        else:
            super().act()

    def _act_juv(self):
        # same as super().act except the option to reproduce is removed
        food_options = self._visible_food()
        if food_options:
            rho,nearest = food_options[0]
            phi = util.rel_phi(self.loc, nearest.loc)
            if rho <= self.max_speed:
                self._move(rho, phi)
                self.eat(nearest)
            else:
                self._move(self.max_speed, phi)
        else:
            self.wander()

    def reproduce(self):
        # will be called by Simon.act
        self.energy -= self.bio.repro_cost(self)    # currently there is no flat cost by default
        super().reproduce()


class MyWorld(World):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def step(self):
        # Overwrite the step method to change how each turn is handled
        if self.turn < 500 and self.turn % 50 == 0:
            self.abundance -= .001
        super().step()

class MyFood(Food):
    def __init__(self, world, *args, **kwargs):
        super().__init__(world, *args, kind="grass_or_some_shit", amount=25, good_for=30)






def run():
    world = MyWorld()
    my_simons = {MySpecies(world) for _ in range(40)}
    world.register_food_drop(MyFood, mu=10, cv=.1)

    # spreading food with variety of ages before adding simons
    for _ in range(10):
        world.step()
    world.turn = 0
    world.add_simons(my_simons)

    while world.turn < 1000 and len(world.simons) > 0:
        world.step()
        print(f"{world.turn}: {len(world.simons)}")

    world.report()

if __name__ == '__main__':
    run()