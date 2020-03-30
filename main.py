# from csv import reader
import pandas as pd
import numpy as np
import csv
import gurobipy as gb

a = gb.Model()  # Initialize the mode

# Define used values

# price_of_el = 0.0002624 #CHF/Wh
FiT = 0.0000791  # CHF/Wh
P_ch_min = 100  # minimum battery charging power (W)
P_ch_max = 32000  # maximum battery charging power (W)
P_dis_min = 100  # minimum batery discharging power (W)
P_dis_max = 32000  # maximum battery discharging power (W)
eff = 1  # charging efficiency
eff_dis = 1  # discharging efficiency
E_batt_min = 20000  # battry minimum energy state of charge (Wh)
E_batt_max = 100000  # battery maximum energy state of charge (Wh)

price = pd.read_csv("price.csv")  # read hourly electricity price from csv file
price = price.PRICE

price_of_el = {}  # Electeicity price at each time step
for t in range(0, 8760):
    price_of_el[t] = price[t]

P_pvv = pd.read_csv(
    "PV_generation_aggregated.csv"
)  # Generation from installed PV at each hour
P_pvv = P_pvv.SUM_GENERATION

P_pv = {}  # Generation from installed PV at each hour
for t in range(0, 8760):
    P_pv[t] = P_pvv[t]

P_pv_export = {}  # PV power sold to the grid at each time step (W)
for t in range(0, 8760):
    P_pv_export[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

P_grid = {}  # grid electricity imported/bought at each time step (W)
for t in range(0, 8760):
    P_grid[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

P_charge = {}  # power used to charge the battery from excess PV (W)
for t in range(0, 8760):
    P_charge[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

P_discharge = {}  # power discharged by the battery to meet unmet demand (W)
for t in range(0, 8760):
    P_discharge[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

P_dmd_unmet = {}  # unmet electricity demand at each time step (W)
for t in range(0, 8760):
    P_dmd_unmet[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

P_pv_excess = {}  # excess electricity from PV at each time step (W)
for t in range(0, 8760):
    P_pv_excess[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

demand = pd.read_csv("demand_aggregated.csv")  # read electricity demand from csv file
demand = demand.SUM_DEMAND

P_dmd = {}  # Electeicity demand at each time step
for t in range(0, 8760):
    P_dmd[t] = demand[t]

E_s = {}  # battery energy state of charge at each time step (Wh)
for t in range(0, 8760):
    E_s[t] = a.addVar(vtype=gb.GRB.CONTINUOUS)

X = {}  # a binary variable preventing buying and selling of electricity
# simultaneously at each time step
for t in range(0, 8760):
    X[t] = a.addVar(vtype=gb.GRB.BINARY)

Y = {}  # a binary variable that constraints charging power to prevent charging and
# discharging simpultaneously at each time step
for t in range(0, 8760):
    Y[t] = a.addVar(vtype=gb.GRB.BINARY)

Z = (
    {}
)  # a binary variable that constraints discharging power to prevent charging and discharging simultaneously at each time step
for t in range(0, 8760):
    Z[t] = a.addVar(vtype=gb.GRB.BINARY)

a.update()

# objective function

a.setObjective(
    gb.quicksum(
        P_pv_export[t] * FiT - P_grid[t] * price_of_el[t] for t in range(0, 8760)
    ),
    gb.GRB.MAXIMIZE,
)

# constraints
c1 = {}
for t in range(0, 8760):
    c1 = a.addConstr(P_grid[t], gb.GRB.GREATER_EQUAL, 0)

c2 = {}
for t in range(0, 8760):
    c2 = a.addConstr(P_grid[t], gb.GRB.LESS_EQUAL, P_dmd_unmet[t])

c3 = {}
for t in range(0, 8760):
    if P_dmd[t] > P_pv[t]:
        c3 = a.addConstr(P_dmd_unmet[t], gb.GRB.EQUAL, P_dmd[t] - P_pv[t])
c4 = {}
for t in range(0, 8760):
    if P_dmd[t] <= P_pv[t]:
        c4 = a.addConstr(P_dmd_unmet[t], gb.GRB.EQUAL, 0)

c5 = {}
for t in range(0, 8760):
    c5 = a.addConstr(P_pv_export[t], gb.GRB.GREATER_EQUAL, 0)
c6 = {}
for t in range(0, 8760):
    c6 = a.addConstr(E_s[0], gb.GRB.EQUAL, E_batt_min)

c7 = {}
for t in range(0, 8760):
    c7 = a.addConstr(P_pv_export[t], gb.GRB.LESS_EQUAL, P_pv_excess[t])

c8 = {}
for t in range(0, 8760):
    if P_pv[t] > P_dmd[t]:
        c8 = a.addConstr(P_pv_excess[t], gb.GRB.EQUAL, P_pv[t] - P_dmd[t])
c9 = {}
for t in range(0, 8760):
    if P_pv[t] <= P_dmd[t]:
        c9 = a.addConstr(P_pv_excess[t], gb.GRB.EQUAL, 0)

c10 = {}
for t in range(0, 8760):
    c10 = a.addConstr(P_charge[t], gb.GRB.GREATER_EQUAL, Y[t] * P_ch_min)

c11 = {}
for t in range(0, 8760):
    c11 = a.addConstr(P_charge[t], gb.GRB.LESS_EQUAL, Y[t] * P_ch_max)

c12 = {}
for t in range(0, 8760):
    c12 = a.addConstr(P_discharge[t], gb.GRB.GREATER_EQUAL, Z[t] * P_dis_min)

c13 = {}
for t in range(0, 8760):
    c13 = a.addConstr(P_discharge[t], gb.GRB.LESS_EQUAL, Z[t] * P_dis_max)

c14 = {}
for t in range(0, 8760):
    c14 = a.addConstr((Y[t] + Z[t]), gb.GRB.LESS_EQUAL, 1)

c15 = a.addConstr(
    gb.quicksum(P_discharge[t] for t in range(0, 8760)),
    gb.GRB.LESS_EQUAL,
    gb.quicksum(P_charge[t] for t in range(0, 8760)),
)

c16 = {}
for t in range(1, 8760):
    c16 = a.addConstr(
        E_s[t],
        gb.GRB.EQUAL,
        E_s[t - 1] + (eff * P_charge[t] - (P_discharge[t] / eff_dis)),
    )

c17 = {}
for t in range(0, 8760):
    c17 = a.addConstr(
        E_s[0],
        gb.GRB.EQUAL,
        E_s[8759] + (eff * P_charge[0] - (P_discharge[0] / eff_dis)),
    )

c18 = {}
for t in range(0, 8760):
    c18 = a.addConstr(P_pv_export[t], gb.GRB.LESS_EQUAL, 50000000 * (1 - X[t]))

c19 = {}
for t in range(0, 8760):
    c19 = a.addConstr(E_s[t], gb.GRB.GREATER_EQUAL, E_batt_min)

c20 = {}
for t in range(0, 8760):
    c20 = a.addConstr(E_s[t], gb.GRB.LESS_EQUAL, E_batt_max)

c21 = {}
for t in range(0, 8760):
    c21 = a.addConstr(E_s[0], gb.GRB.EQUAL, E_s[8759])

c22 = {}
for t in range(0, 8760):
    c22 = a.addConstr(P_grid[t], gb.GRB.LESS_EQUAL, 50000000 * X[t])

c23 = {}
for t in range(0, 8760):
    c23 = a.addConstr(
        P_dmd[t],
        gb.GRB.EQUAL,
        P_grid[t] + P_pv[t] - P_pv_export[t] - P_charge[t] + P_discharge[t],
    )

c24 = {}
for t in range(0, 8760):
    c24 = a.addConstr(P_pv[t], gb.GRB.GREATER_EQUAL, P_pv_export[t])

# c26 = {}
# for t in range(0, 8760):
#   c26 = a.addConstr(P_dmd_unmet[t], gb.GRB.GREATER_EQUAL, P_grid[t])

c25 = {}
for t in range(0, 8760):
    c25 = a.addConstr(P_discharge[t] + P_grid[t], gb.GRB.EQUAL, P_dmd_unmet[t])

a.update()

a.optimize()

# functions below used for printing results

# lst = []
# for t in range(0, 8760):
#   lst.append(t)

# with open('Pbought_aggregated.csv', 'w', newline='', encoding='utf8') as output_file:

#   for t in range (0, 8760):
#      lst[t] = P_grid[t]

# writer = csv.writer(output_file, lineterminator='\n')
# writer.writerows(map(lambda x: [x], lst))
