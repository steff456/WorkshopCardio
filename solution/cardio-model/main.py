"""This is a module."""
#!/usr/bin/env python
# coding: utf-8
import argparse
from sympy import Symbol
from sympy.tensor.array import derive_by_array
from sympy.utilities.lambdify import lambdify
import numpy as np


parser = argparse.ArgumentParser(description='Compliance calculation')

parser.add_argument('--mode', default='healthy',
                    help='Case for changing the parameters value.')

parser.add_argument('--vol', default=5, help='Total volume of blood')

parser.add_argument('--numit', default=10000,
                    help='Number of iterations of the simulation')

args = parser.parse_args()


if args.mode == 'healthy':
    RS = 17.5
    RP = 1.79
    KR = 2.8
    KL = 1.12
elif args.mode == 'heart-failure':
    RS = 6.82
    RP = 1.36
    KR = 4.72
    KL = 9.5
elif args.mode == 'hypertension':
    RS = 40.5
    RP = 3.21
    KR = 3
    KL = 1.7
else:
    raise RuntimeError("The mode is not valid.")


V = float(args.vol)
NUMIT = int(args.numit)


def create_def():
    """Define variables, equations and objective function."""
    # Definition of variables
    Csa = Symbol('Csa')
    Csv = Symbol('Csv')
    Cpa = Symbol('Cpa')
    Cpv = Symbol('Cpv')

    # Definition of equations
    Tsa = Csa / KR + Csa * RS
    Tsv = Csv / KR
    Tpa = Cpa / KL + Cpa * RP
    Tpv = Cpv / KL

    Tsum = Tsa + Tsv + Tpa + Tpv

    # Volumes
    Vsa = Tsa * V / Tsum
    Vsv = Tsv * V / Tsum
    Vpa = Tpa * V / Tsum
    Vpv = Tpv * V / Tsum
    Vsum = Vsa + Vsv + Vpa + Vpv
    Vtot = lambdify((Csa, Csv, Cpa, Cpv), Vsum)

    # Objective Function
    f_obj = V / Tsum
    f = lambdify((Csa, Csv, Cpa, Cpv), f_obj)

    # Partial derivatives of objective function
    partial = derive_by_array(f_obj, (Csa, Csv, Cpa, Cpv))
    grad = lambdify((Csa, Csv, Cpa, Cpv), partial)

    return grad, Vtot, f


def run_simulation(grad, Vtot, f):
    """Minimize the objective function to get the compliance values."""
    n = NUMIT

    # Generate random values for init Cpa, Cpv, Csa, Csv
    x = np.random.rand(4)

    min_val = 5000000
    min_x = x

    while n > 0:
        # Check all x are positive
        for val in x:
            if val < 0:
                val = abs(val)

        # Check the volume restriction
        act_v = Vtot(x[0], x[1], x[2], x[3])

        if act_v != V:
            y = V*np.ones(4)
            diff = np.abs(np.subtract(x, y))
            val, idx = min((val, idx) for (idx, val) in enumerate(diff))
            x[idx] = val

        # Calculate gradient given the points
        g = grad(x[0], x[1], x[2], x[3])

        # Calculate the value of the objective function
        act = f(x[0], x[1], x[2], x[3])

        if act < min_val:
            min_val = act
            min_x = x

        # Modify the actual value depending the gradient
        val, idx = max((val, idx) for (idx, val) in enumerate(g))
        x[idx] = abs(x[idx]+val)
        n = n - 1

    return min_x


def main():
    """Run the program."""
    grad, Vtot, f = create_def()
    min_x = run_simulation(grad, Vtot, f)
    print(' Csa: {} \n Csv: {} \n Cpa: {} \n Cpv: {} \n'.format(
              min_x[0], min_x[1], min_x[2], min_x[3]))


if __name__ == '__main__':
    main()
