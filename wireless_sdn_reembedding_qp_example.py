from __future__ import print_function

import cplex


def setproblemdata(p):
    p.objective.set_sense(p.objective.sense.maximize)

    p.linear_constraints.add(rhs=[20.0, 30.0], senses="LL")

    obj = [1.0, 2.0, 3.0]
    ub = [40.0, cplex.infinity, cplex.infinity]
    cols = [[[0, 1], [-1.0, 1.0]],
            [[0, 1], [1.0, -3.0]],
            [[0, 1], [1.0, 1.0]]]

    p.variables.add(obj=obj, ub=ub, columns=cols,
                    names=["one", "two", "three"])

    qmat = [[[0, 1, 2], [-33.0, 6.0, 0]],
            [[0, 1, 2], [6.0, -22.0, 11.5]],
            [[0, 1, 2], [0, 11.5, -11.0]]]

    p.objective.set_quadratic(qmat)


def qpex1():
    p = cplex.Cplex()
    setproblemdata(p)
    p.write("cplex_file_generated.lp")

    p.solve()

    # solution.get_status() returns an integer code
    print("Solution status = ", p.solution.get_status(), ":", end=' ')
    # the following line prints the corresponding string
    print(p.solution.status[p.solution.get_status()])
    print("Solution value  = ", p.solution.get_objective_value())

    numrows = p.linear_constraints.get_num()

    for i in range(numrows):
        print("Row ", i, ":  ", end=' ')
        print("Slack = %10f " % p.solution.get_linear_slacks(i), end=' ')
        print("Pi = %10f" % p.solution.get_dual_values(i))

    numcols = p.variables.get_num()

    for j in range(numcols):
        print("Column ", j, ":  ", end=' ')
        print("Value = %10f " % p.solution.get_values(j), end=' ')
        print("Reduced Cost = %10f" % p.solution.get_reduced_costs(j))

if __name__ == "__main__":
    qpex1()


'''

Maximize
 obj: one + 2 two + 3 three + [ - 33 one ^2 + 12 one * two - 22 two ^2
      + 23 two * three - 11 three ^2 ] / 2
Subject To
 c1: - one + two + three <= 20
 c2: one - 3 two + three <= 30
Bounds
 0 <= one <= 40
End

'''