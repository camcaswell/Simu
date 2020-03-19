from critter import Critter
from world import World
import datavis

class LabRat(Critter):
    def __init__(self, world, *args, **kwargs):
        super().__init__(world, *args, **kwargs)

    def flee(self):
            self.flee_1()

    def flee_1(self):
        predators = [p for p in self.visible_critters if self._is_predator(p)]
        danger_arcs = []
        biggest_arc = 0
        for rho, pred in predators:
            phi = util.rel_phi(self.loc, pred.loc)
            arc = self._threat_eval(pred) / (rho ** (3.0/2))
            danger_arcs.append(phi, arc)
            biggest_arc = max(biggest_arc, arc)
        if biggest_arc >= pi:
            scale = pi/biggest_arc - util.epsilon    # scale down largest interval to at most 2pi-2ep
        else:
            scale = 1
        safe_intervals = []
        while not safe_intervals:
            intervals = [(phi-desperation*arc, phi+desperation*arc) for phi,arc in danger_arcs]
            safe_intervals = util.subtract_intervals(intervals)
            scale *= 0.8
        right, left = max(safe_intervals, key=lambda i: i[1]-i[0])
        return right + util.angle(right, left)/2

    def flee_2(self):
        #normalize sum of interval sizes to ~80% of 2pi
        danger_arcs = []
        biggest_arc = 0
        for rho, pred in predators:
            phi = util.rel_phi(self.loc, pred.loc)
            arc = self._threat_eval(pred) / (rho ** (3.0/2))
            danger_arcs.append(phi, arc)
            biggest_arc = max(biggest_arc, arc)

        scale = 0.9*pi / sum([arc for _,arc in danger_arcs])    # scale so sum of arcs is 90% of circle
        intervals = [(phi-desperation*arc, phi+desperation*arc) for phi,arc in danger_arcs]
        safe_intervals = util.subtract_intervals(intervals)
        right, left = max(safe_intervals, key=lambda i: i[1]-i[0])
        return right + util.angle(right, left)/2

def run():
    world = World()
    world.set_up()

    world.add_critters([LabRat(world) for _ in range(40)])

    pop_data = []

    while world.turn < 500 and 0 < (turn_pop := world.pop_count):
        print(f"{world.turn}: {turn_pop}")
        pop_data.append(turn_pop)
        world.step()

    world.report()
    datavis.plot_pop(pop_data)

if __name__=='__main__':
    run()
