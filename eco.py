from biology import BioAssumptions
from critter import Critter, Decisions, Results
from world import World
from food import Food
import util

class Predator(Critter):
    def __init__(self, world, *args, **kwargs):
        super().__init__(world, *args, **kwargs)
    
    DESCRIPTION = "A predator species"

    # overwriting the default initial traits of my species
    START_TRAITS = {
        'per_critter': 60,                  # perception range of other critters
        'per_food': 60,                     # perception range of food drops
        'wander_effort': 0.9,               # proportion of max speed Critter moves at when no goal in sight
        'wander_faith': 40,                 # how close they adhere to their previous heading when wandering

        'mass': 15,                         # determines a lot of derived stats
        'reproduction_threshold': 0.8,      # proportion of max energy at which Critter will reproduce
        'energy_inheritance': 0.5,          # proportion of max energy passed on to each child

        'flee_range': 5,

        'behav_weight_wander': .75,
        'behav_weight_flee': 0.8,
        'behav_weight_food': 2,
        'behav_weight_mate': 2,
        'behav_weight_predator': 3,
        'behav_weight_competitor': 30,

        'nav_angleoffset_food': 1,
        'nav_angleoffset_mate': 2,
        'nav_angleoffset_predator': 3,
        'nav_angleoffset_competitor': 3,

        'nav_distance_food': 1,
        'nav_distance_mate': 2,
        'nav_distance_pred': 3,
        'nav_distance_competitor': 1,
    }
    
    @property
    def visible_food(self):
        return [c in self.visible_critters if self._is_prey(c)]

    def seek_food(self):
        # should probably rewrite default seek_food to service full carnivore-herbivore spectrum
        decision, target = super().seek_food()
        if decision is Decisions.EAT:
            decision = Decisions.PREDATE
        return decision, target
       
    def predate(self, prey):
        # prey is actually killed in World.step
        self.energy += prey.energy     # something has to be done about structural energy and carcasses etc
        return Results.SUCCESS
        
    def _food_eval(self, prey):
        return self.behav_weight_food * prey.energy * (self.max_energy/self.energy) * 1
        
    def _is_prey(self, other):
        return type(other) is Prey
    
Class Prey(Critter):
    
    DESCRIPTION = "A prey species"
    
    def _is_predator(self, other):
        return type(other) is Predator
    
