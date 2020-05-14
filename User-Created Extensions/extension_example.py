from grizzled.os import working_directory
with working_directory('..'):
    from critter import Critter
    from food import Food
    from world import World
    from biology import BioAssumptions

class ScaryPredator(Critter):
    DESCRIPTION = "A critter than can eat other critters"
    pass
