[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

batteryopt is a battery operation optimization tool developed by Jakub Szcześniak and
implemented by Samuel Letellier-Duchesne. The objective is to minimize the annual
electricity costs of a battery-integrated PV system using a Mixed-Integer Linear Program
(MILP). The algorithm is implemented using the [pyomo](http://www.pyomo.org/) library
opening up the model to a large array of solvers (e.g.: Gurobi, GLPK, etc.).

# Installation

```cmd
conda create --name batteryopt python=3.7  # tested with 3.7, 3.8 and 3.9
conda activate batteryopt
```

```
git clone https://github.com/MITSustainableDesignLab/batteryopt.git
cd batteryopt
python setup.py install
```

# Usage

Type `batteryopt --help` to access the command line options

# Output

batteryopt outputs an Excel file with the model Variables for each time step of the year:

|    |  t |  tf |   M |   P_dmd |    P_elec | P_pv | Buying | Charging | Discharging |   E_s | P_charge | P_discharge | P_dmd_unmet |  P_grid | P_pv_excess | P_pv_export |
|---:|---:|----:|----:|--------:|----------:|-----:|-------:|---------:|------------:|------:|---------:|------------:|------------:|--------:|------------:|------------:|
|  0 |  1 | nan | nan | 60536.5 | 0.0002624 |    0 |      1 |        0 |           0 | 20000 |       -0 |          -0 |     60536.5 | 60536.5 |           0 |           0 |
|  1 |  1 |   1 | nan | 60536.5 | 0.0002624 |    0 |      1 |        0 |           0 | 20000 |       -0 |           0 |     60536.5 | 60536.5 |           0 |           0 |
|  2 |  1 |   1 | nan | 60536.5 | 0.0002624 |    0 |      1 |        0 |           0 | 20000 |       -0 |           0 |     60536.5 | 60536.5 |           0 |           0 |
|  3 |  1 |   1 | nan | 60536.5 | 0.0002624 |    0 |      1 |        0 |           0 | 20000 |       -0 |           0 |     60536.5 | 60536.5 |           0 |           0 |
|  4 |  1 |   1 | nan | 60536.5 | 0.0002624 |    0 |      1 |        0 |           0 | 20000 |       -0 |           0 |     60536.5 | 60536.5 |           0 |           0 |

The column names are:
