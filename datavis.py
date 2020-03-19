import matplotlib.pyplot as plt

def plot_pop(pop_data):
    plt.plot(pop_data)
    plt.ylabel("Population")
    plt.xlabel("Turn")
    plt.show()