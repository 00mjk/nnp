"""
Use ASE to Simulate Planetary Motion
====================================

This tutorial shows how to use `ASE`_ to simulate planetary motion.
Although both ASE and NNP are designed for molecular dynamics (MD),
implementing a force field to do MD is not at a reasonable abount of
work to use as a tutorial. So we simulate something different here.
Assume we have two atoms, one hydrogen and one carbon. They are all
moving under the gravity centered at the origin. There is no interaction
between these two atoms.

.. _ASE:
    https://wiki.fysik.dtu.dk/ase
"""

###############################################################################
# Let's first import all the packages we will use:
import ase
from ase.data import atomic_masses
from ase.units import fs
from ase.md.verlet import VelocityVerlet
import nnp.md as md
import pytest
import sys
import math
import matplotlib.pyplot as plt


###############################################################################
# The module `nnp.md` provide tools to run molecular dynamics with a potential
# defined by PyTorch. To define the potential we need to provide a function that
# takes the chemical symbols, atom coordinates, unit cell, and PBC flag as an input
# and returns the molecular energy as an output. The output and input coordinates
# and cell must be in the a differentiable graph so that PyTorch could automatically
# compute the force and stress tensor using the `autograd` engine. In this example,
# we don't care about the periodic boundary condition and unit cell because we
# are actually not simulating molecular system.
#
# From basic physics, we know that the equation for gravitational potential has
# the equation :math:`E(r)=-\frac{GMm}{r}`. For simplicity, we choose :math:`GM=1`
# when :math:`E` is in :math:`\mathrm{eV}`, :math:`m` in :math:`\mathrm{amu}`,
# and :math:`r` in Angstrom.
def gravity(chemical_symbols, coordinates, _cell, _pbc):
    assert len(chemical_symbols) == coordinates.shape[0]
    atomic_numbers = {'H': 0, 'C': 6}
    mass = coordinates.new_tensor(
        [atomic_masses[atomic_numbers[s]] for s in chemical_symbols])
    inv_r = 1 / coordinates.norm(dim=1)
    potential_energies = - mass * inv_r
    return potential_energies.sum()


###############################################################################
# with this potential, we could define an ASE calculator:
calculator = md.Calculator(gravity)

###############################################################################
# Now let's create two atoms, initially at (1, 0, 0) and (2, 0, 0)
planets = ase.Atoms('CH', [[1, 0, 0], [2, 0, 0]])

###############################################################################
# For the purpose of demonstration, we make these two atoms's trajector a perfect
# circle at the XY plane. To do so, we need to carefully set the initial velocity.
# It is not hard to get that, the velocity is :math:`v = \sqrt{\frac{GM}{r}}`.
planets.set_velocities([[0, 1, 0], [0, 1 / math.sqrt(2), 0]])
planets.set_calculator(calculator)

###############################################################################
# Now we can start the dynamics:
X1 = []
Y1 = []
Z1 = []
X2 = []
Y2 = []
Z2 = []


def dump_positions():
    (x1, y1, z1), (x2, y2, z2) = planets.get_positions()
    X1.append(x1)
    Y1.append(y1)
    Z1.append(z1)
    X2.append(x2)
    Y2.append(y2)
    Z2.append(z2)


dyn = VelocityVerlet(planets, timestep=0.01 * fs)
dyn.attach(dump_positions)
dyn.run(20000)

###############################################################################
# Now let's plot the trajectory to see what we get:
if __name__ == '__main__':
    plt.clf()
    plt.plot(X1, Y1, label='C')
    plt.plot(X2, Y2, label='H')
    plt.legend()
    plt.axes().set_aspect('equal')
    plt.show()


###############################################################################
# To check the correctness of this dynamics, we use pytest to test if it is on
# the XY plane and if the trajectory is circle:
def test_is_on_xy_plan():
    for z in Z1 + Z2:
        assert abs(z) < 1e-4


def test_is_circle():
    for x, y in zip(X1, Y1):
        assert abs(math.sqrt(x * x + y * y) - 1) < 0.1
    for x, y in zip(X2, Y2):
        assert abs(math.sqrt(x * x + y * y) - 2) < 0.1


if __name__ == '__main__':
    pytest.main([sys.argv[0], '-v'])
