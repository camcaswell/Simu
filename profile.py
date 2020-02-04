from cProfile import Profile
from pstats import Stats
from io import StringIO

import world

def profile():
    profiler = Profile()
    profiler.enable()
    world.run()
    profiler.disable()

    s = StringIO()
    stats = Stats(profiler, stream=s)
    stats.sort_stats('cumtime')
    stats.print_stats()

    results = 'ncalls'+s.getvalue().split('ncalls')[1]       # cutting of some non-column text at beginning
    lines = results.split('\n')
    rows = [','.join(line.rstrip().split(None, 5)) for line in lines]

    with open('profile_results.csv', 'w') as statfile:
        statfile.write('\n'.join(rows))

profile()