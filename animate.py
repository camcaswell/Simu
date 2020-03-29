from world import World
from critter import Critter
from datavis import Data

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from random import randint



def main():

    turns = 5000
    start_pop = 50

    world = World(size=400)

    world.abundance = 0.3


    world.set_up_food()
    world.add_critters([Critter(world, age=randint(0,Critter.MAX_AGE)) for _ in range(start_pop)])

    animate_world(world, turns)



def animate_world(world, turns):
    data = Data(turns)
    fig, ax = plt.subplots()
    ax.set_xlim(-0.1*world.size, 1.1*world.size)
    ax.set_ylim(-0.1*world.size, 1.1*world.size)

    critter_line, = ax.plot([], [], color='red', marker='D', linestyle='')
    food_line, = ax.plot([], [], color='green', marker='x', linestyle='')

    def draw(world_state):
        turn_pop = world_state.pop_count
        all_critters = world_state.all_critters
        all_food = world_state.all_food
        turn = world_state.turn

        data.pop[turn] = turn_pop
        data.avg_age[turn] = sum([c.age for c in all_critters]) / turn_pop
        #data.avg_generation[turn] = sum([c.generation for c in all_critters]) / turn_pop
        data.max_generation[turn] = max([c.generation for c in all_critters])

        data.starved[turn] = world.starved
        data.old_age[turn] = world.old_age
        data.prey[turn] = world.prey
        data.born[turn] = world.born

        data.avg_energy[turn] = sum([c.energy for c in all_critters]) / turn_pop
        data.food_energy[turn] = sum([f.amount for f in all_food])

        critter_xs = []
        critter_ys = []
        for critter in all_critters:
            x,y = critter.loc
            critter_xs.append(x)
            critter_ys.append(y)

        food_xs = []
        food_ys = []
        for food in all_food:
            x,y = food.loc
            food_xs.append(x)
            food_ys.append(y)

        critter_line.set_xdata(critter_xs)
        critter_line.set_ydata(critter_ys)
        food_line.set_xdata(food_xs)
        food_line.set_ydata(food_ys)

        ax.set_title(f"Turn: {turn}  Pop: {turn_pop}")


    ani = animation.FuncAnimation(fig, draw, world.get_generator(turns), 
            blit=False, interval=1, repeat=True, repeat_delay=0, save_count=turns)

    #data.compile_plots()

    plt.show()



if __name__ == '__main__':
    main()