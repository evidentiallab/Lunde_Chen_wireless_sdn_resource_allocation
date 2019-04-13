from deap import tools


def myVarAnd(population, toolbox):
    # offspring = [toolbox.clone(ind) for ind in population]
    offspring = population

    pairs = [(offspring[i-1], offspring[i]) for i in range(1, len(offspring), 2)]
    _result = toolbox.map(toolbox.mate, pairs)
    for i in range(1, len(offspring), 2):
        (offspring[i -1], offspring[i]) = _result[(i - 1) / 2]

    offspring = [list(elem)[0] for elem in toolbox.map(toolbox.mutate, offspring)]
    return offspring

def myEaSimple(population, toolbox, cxpb, mutpb, ngen, stats=None,
             halloffame=None, verbose=__debug__):
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    # invalid_ind = [ind for ind in population]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    for gen in range(1, ngen + 1):
        offspring = toolbox.select(population, len(population))

        offspring = myVarAnd(offspring, toolbox)

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        # invalid_ind = [ind for ind in offspring]

        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        if halloffame is not None:
            halloffame.update(offspring)

        # population[:] = offspring

        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

    return population, logbook
