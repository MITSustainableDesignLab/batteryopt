# from csv import reader
import gurobipy as gb
import pandas as pd
from path import Path


def create_model(
    price_of_el=0.0002624,
    feed_in_t=0.0000791,
    P_ch_min=100,
    P_ch_max=32000,
    P_dis_min=100,
    P_dis_max=32000,
    eff=1,
    eff_dis=1,
    E_batt_min=20000,
    E_batt_max=100000,
):
    """
    Args:
        price_of_el (float or PathLike): CHF/Wh
        feed_in_t: CHF/Wh
        P_ch_min: minimum battery charging power (W)
        P_ch_max: maximum battery charging power (W)
        P_dis_min: minimum battery discharging power (W)
        P_dis_max: maximum battery discharging power (W)
        eff: charging efficiency
        eff_dis: discharging efficiency
        E_batt_min: battery minimum energy state of charge (Wh)
        E_batt_max: battery maximum energy state of charge (Wh)
    """
    model = gb.Model()  # Initialize the model

    if isinstance(price_of_el, (str, Path)):
        # Use file as electricity price
        price = pd.read_csv(
            "../data/pricesignal.csv"
        )  # read hourly electricity price from csv file
        price_of_el = price.PRICE.to_dict()
    else:
        price_of_el = {k: price_of_el for k in range(0, 8760)}
    P_pvv = pd.read_csv(
        "../data/pvgen.csv"
    )  # Generation from installed PV at each hour
    P_pv = P_pvv.SUM_GENERATION.to_dict()  # Generation from installed PV at each hour
    P_pv_export = {}  # PV power sold to the grid at each time step (W)
    P_grid = {}  # grid electricity imported/bought at each time step (W)
    P_charge = {}  # power used to charge the battery from excess PV (W)
    P_discharge = {}  # power discharged by the battery to meet unmet demand (W)
    P_dmd_unmet = {}  # unmet electricity demand at each time step (W)
    P_pv_excess = {}  # excess electricity from PV at each time step (W)
    for t in range(0, 8760):
        P_pv_export[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_pv_export")
        P_grid[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_grid")
        P_charge[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_charge")
        P_discharge[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_discharge")
        P_dmd_unmet[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_dmd_unmet")
        P_pv_excess[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="P_pv_excess")
    demand = pd.read_csv("../data/demand.csv")  # read electricity demand from csv file
    P_dmd = demand.SUM_DEMAND.to_dict()  # Electricity demand at each time step
    E_s = {}  # battery energy state of charge at each time step (Wh)
    X = {}  # a binary variable preventing buying and selling of electricity
    Y = {}  # a binary variable that constraints charging power to prevent charging and
    # discharging simultaneously at each time step
    Z = {}  # a binary variable that constraints discharging power to prevent
    # charging and
    # discharging simultaneously at each time step
    for t in range(0, 8760):
        E_s[t] = model.addVar(vtype=gb.GRB.CONTINUOUS, name="E_s")
        X[t] = model.addVar(
            vtype=gb.GRB.BINARY, name="X"
        )  # simultaneously at each time step
        Y[t] = model.addVar(vtype=gb.GRB.BINARY, name="Y")
        Z[t] = model.addVar(vtype=gb.GRB.BINARY, name="Z")
    model.update()
    # objective function
    model.setObjective(
        gb.quicksum(
            P_pv_export[t] * feed_in_t - P_grid[t] * price_of_el[t] for t in range(0, 8760)
        ),
        gb.GRB.MAXIMIZE,
    )
    # constraints
    c1 = {}
    for t in range(0, 8760):
        c1 = model.addConstr(P_grid[t], gb.GRB.GREATER_EQUAL, 0)
    c2 = {}
    for t in range(0, 8760):
        c2 = model.addConstr(P_grid[t], gb.GRB.LESS_EQUAL, P_dmd_unmet[t])
    c3 = {}
    for t in range(0, 8760):
        if P_dmd[t] > P_pv[t]:
            c3 = model.addConstr(P_dmd_unmet[t], gb.GRB.EQUAL, P_dmd[t] - P_pv[t])
    c4 = {}
    for t in range(0, 8760):
        if P_dmd[t] <= P_pv[t]:
            c4 = model.addConstr(P_dmd_unmet[t], gb.GRB.EQUAL, 0)
    c5 = {}
    for t in range(0, 8760):
        c5 = model.addConstr(P_pv_export[t], gb.GRB.GREATER_EQUAL, 0)
    c6 = {}
    for t in range(0, 8760):
        c6 = model.addConstr(E_s[0], gb.GRB.EQUAL, E_batt_min)
    c7 = {}
    for t in range(0, 8760):
        c7 = model.addConstr(P_pv_export[t], gb.GRB.LESS_EQUAL, P_pv_excess[t])
    c8 = {}
    for t in range(0, 8760):
        if P_pv[t] > P_dmd[t]:
            c8 = model.addConstr(P_pv_excess[t], gb.GRB.EQUAL, P_pv[t] - P_dmd[t])
    c9 = {}
    for t in range(0, 8760):
        if P_pv[t] <= P_dmd[t]:
            c9 = model.addConstr(P_pv_excess[t], gb.GRB.EQUAL, 0)
    c10 = {}
    for t in range(0, 8760):
        c10 = model.addConstr(P_charge[t], gb.GRB.GREATER_EQUAL, Y[t] * P_ch_min)
    c11 = {}
    for t in range(0, 8760):
        c11 = model.addConstr(P_charge[t], gb.GRB.LESS_EQUAL, Y[t] * P_ch_max)
    c12 = {}
    for t in range(0, 8760):
        c12 = model.addConstr(P_discharge[t], gb.GRB.GREATER_EQUAL, Z[t] * P_dis_min)
    c13 = {}
    for t in range(0, 8760):
        c13 = model.addConstr(P_discharge[t], gb.GRB.LESS_EQUAL, Z[t] * P_dis_max)
    c14 = {}
    for t in range(0, 8760):
        c14 = model.addConstr((Y[t] + Z[t]), gb.GRB.LESS_EQUAL, 1)
    c15 = model.addConstr(
        gb.quicksum(P_discharge[t] for t in range(0, 8760)),
        gb.GRB.LESS_EQUAL,
        gb.quicksum(P_charge[t] for t in range(0, 8760)),
    )
    c16 = {}
    for t in range(1, 8760):
        c16 = model.addConstr(
            E_s[t],
            gb.GRB.EQUAL,
            E_s[t - 1] + (eff * P_charge[t] - (P_discharge[t] / eff_dis)),
        )
    c17 = {}
    for t in range(0, 8760):
        c17 = model.addConstr(
            E_s[0],
            gb.GRB.EQUAL,
            E_s[8759] + (eff * P_charge[0] - (P_discharge[0] / eff_dis)),
        )
    c18 = {}
    for t in range(0, 8760):
        c18 = model.addConstr(P_pv_export[t], gb.GRB.LESS_EQUAL, 50000000 * (1 - X[t]))
    c19 = {}
    for t in range(0, 8760):
        c19 = model.addConstr(E_s[t], gb.GRB.GREATER_EQUAL, E_batt_min)
    c20 = {}
    for t in range(0, 8760):
        c20 = model.addConstr(E_s[t], gb.GRB.LESS_EQUAL, E_batt_max)
    c21 = {}
    for t in range(0, 8760):
        c21 = model.addConstr(E_s[0], gb.GRB.EQUAL, E_s[8759])
    c22 = {}
    for t in range(0, 8760):
        c22 = model.addConstr(P_grid[t], gb.GRB.LESS_EQUAL, 50000000 * X[t])
    c23 = {}
    for t in range(0, 8760):
        c23 = model.addConstr(
            P_dmd[t],
            gb.GRB.EQUAL,
            P_grid[t] + P_pv[t] - P_pv_export[t] - P_charge[t] + P_discharge[t],
        )
    c24 = {}
    for t in range(0, 8760):
        c24 = model.addConstr(P_pv[t], gb.GRB.GREATER_EQUAL, P_pv_export[t])
    # c26 = {}
    # for t in range(0, 8760):
    #   c26 = a.addConstr(P_dmd_unmet[t], gb.GRB.GREATER_EQUAL, P_grid[t])
    c25 = {}
    for t in range(0, 8760):
        c25 = model.addConstr(P_discharge[t] + P_grid[t], gb.GRB.EQUAL, P_dmd_unmet[t])
    model.update()
    return model


if __name__ == "__main__":
    # First, create the model
    a = create_model()

    # Optimize
    a.optimize()

    # saving results to file
    var = pd.Series(
        [str(v.X) for v in a.getVars() if v.varName == "P_grid"], name="P_grid"
    )
    var.to_csv("Pbought_aggregated.csv", index_label="Time Step")
