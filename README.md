[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

batteryopt is a battery operation optimization tool developed by Jakub Szcześniak and implemented by Samuel Letellier-Duchesne. The objective is to minimize the annual electricity costs of a battery-integrated PV system using a Mixed-Integer Linear Program (MILP). The algorithm is implemented using the [pyomo](http://www.pyomo.org/) library opening up the model to a large array of solvers (e.g.: Gurobi, GLPK, etc.).

# Installation

`git clone https://github.com/MITSustainableDesignLab/batteryopt.git`
`cd batteryopt`
`python setup.py install`

# Usage

Type `batteryopt --help` to acces the command line options
