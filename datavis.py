import matplotlib.pyplot as plt
from collections import defaultdict as dd

COLORS = ['r', 'g', 'b', 'c', 'm', 'y']

class Data():
    def __init__(self, turns):

        self.turns = turns

        self.pop =     dd(int)
        self.avg_age = dd(float)
        self.born =    dd(int)
        self.avg_generation = dd(float)
        self.max_generation = dd(int)

        self.starved = dd(int)
        self.old_age = dd(int)
        self.prey =    dd(int)

        self.avg_energy =  dd(float)
        self.food_energy = dd(float)
        self.food_expired = dd(float)

    def compile_plots(self):
        self.plot_thermo()
        self.plot_demo()

    def plot_pop(self):
        plt.plot(self.list_data(self.pop))
        plt.ylabel("Population")
        plt.xlabel("Turn")
        plt.show()

    def plot_thermo(self):
        plots = {
            "Population": self.list_data(self.pop),
            "Average Energy Level": self.list_data(self.avg_energy),
            "Total Available Food": self.list_data(self.food_energy),
            #"Food Expired": self.list_data(self.food_expired),
        }
        self.multi_plot(**plots)

    def plot_demo(self):
        plots = {
            "Population": self.list_data(self.pop),
            "Average Age": self.list_data(self.avg_age),
            "Dead of Old Age (cum.)": self.accumulate(self.list_data(self.old_age)),
            "Dead of Starvation (cum.)": self.accumulate(self.list_data(self.starved)),
            "Critters Born": self.list_data(self.born),
            "Max Generation": self.list_data(self.max_generation),
        }
        self.multi_plot(**plots)

    def multi_plot(self, xlabel="Turn", **kwargs):
        # https://matplotlib.org/3.2.0/gallery/ticks_and_spines/multiple_yaxis_with_spines.html

        fig, host = plt.subplots()
        #fig.subplots_adjust(right=.8)
        fig.set_tight_layout(True)

        (main_label, main_data), *parasites = kwargs.items()

        xpoints = list(range(self.turns))

        line, = host.plot(xpoints, main_data, 'k-', label=main_label)
        host.yaxis.label.set_color(line.get_color())

        host.set_xlim(0, xpoints[-1])
        host.set_ylim(0, 1.15*max(main_data))

        host.set_xlabel(xlabel)
        host.set_ylabel(main_label)

        tkw = dict(size=4, width=1.5)
        host.tick_params(axis='x', **tkw)
        host.tick_params(axis='y', colors=line.get_color(), **tkw)

        lines = [line]

        for count, (label, data) in enumerate(parasites):

            parasite = host.twinx()

            # Offset the right spine of parasite.  The ticks and label have already been
            # placed on the right by twinx above.
            parasite.spines["right"].set_position(("axes", 1+(0.05*count)))
            # Having been created by twinx, parasite has its frame off, so the line of its
            # detached spine is invisible.  First, activate the frame but make the patch
            # and spines invisible.
            parasite.set_frame_on(True)
            parasite.patch.set_visible(False)
            for sp in parasite.spines.values():
                sp.set_visible(False)
            # Second, show the right spine.
            parasite.spines["right"].set_visible(True)

            line, = parasite.plot(xpoints, data, COLORS[count]+'-', label=label)

            parasite.set_ylim(0, max(1, 1.15*max(data)))
            parasite.set_ylabel(label)

            parasite.yaxis.label.set_color(line.get_color())

            parasite.tick_params(axis='y', colors=line.get_color(), **tkw)

            lines.append(line)

        #host.legend(lines, [l.get_label() for l in lines])

    def accumulate(self, count_list):
        ret_list = [count_list[0]]
        for t in range(1, self.turns):
            ret_list.append(ret_list[t-1] + count_list[t])
        return ret_list

    def list_data(self, ddict):
        retlist = [0] * self.turns
        for t, d in ddict.items():
            retlist[t] = d
        return retlist
