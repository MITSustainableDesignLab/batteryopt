# from csv import reader
import pandas as pd
from pandas import DataFrame
from path import Path
from pyomo.environ import *
from pyomo.opt import SolverFactory

from batteryopt import list_entities, get_entity


def create_model(
    demand,
    generation,
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
        demand (pd.Series): Series with the electricity demand (W).
        generation (pd.Series): Series with the PV generation (W).
        price_of_el (float or PathLike): If float, a single price is used for all
            time steps. If a .csv is passed, the column named "PRICE" is used. Units
            are $/Wh.
        feed_in_t: $/Wh
        P_ch_min: minimum battery charging power (W).
        P_ch_max: maximum battery charging power (W).
        P_dis_min: minimum battery discharging power (W).
        P_dis_max: maximum battery discharging power (W).
        eff: charging efficiency (-).
        eff_dis: discharging efficiency (-).
        E_batt_min: battery minimum energy state of charge (Wh).
        E_batt_max: battery maximum energy state of charge (Wh).
    """
    m = ConcreteModel()
    period = len(demand)  # period lenght in storage_hours

    # Sets
    m.t = Set(initialize=list(range(0, period)), ordered=True, doc="Set of timesteps")
    m.tf = Set(
        within=m.t,
        initialize=list(range(0, period))[1:],
        ordered=True,
        doc="Set of modelled time steps",
    )

    if isinstance(price_of_el, (str, Path)):
        # Use file as electricity price
        price = pd.read_csv(price_of_el)  # read hourly electricity price from csv file
        price_of_el = price.PRICE.to_dict()
    else:
        price_of_el = {k: price_of_el for k in range(0, period)}

    # Parameters
    m.P_dmd = Param(
        m.t,
        initialize=demand.reset_index(drop=True).to_dict(),  # reset_index to remove
        # datetime index
        doc="Electricity demand at each time step",
    )
    m.P_elec = Param(
        m.t,
        initialize=price_of_el,
        doc="Price of electricity at each time step",
    )

    m.P_pv = Param(
        m.t,
        initialize=generation.reset_index(drop=True).to_dict(),  # reset_index to remove
        # datetime index
        doc="Generation from installed PV at each hour",
    )

    # Variables
    m.P_pv_export = Var(
        m.t, domain=Reals, doc="PV power sold to the grid at each time step (W)"
    )
    m.P_grid = Var(
        m.t, domain=Reals, doc="grid electricity imported/bought at each time step (W)"
    )
    m.P_charge = Var(
        m.t, domain=Reals, doc="power used to charge the battery from excess PV (W)"
    )
    m.P_discharge = Var(
        m.t,
        domain=Reals,
        doc="power discharged by the battery to meet unmet demand (W)",
    )
    m.P_dmd_unmet = Var(
        m.t, domain=Reals, doc="unmet electricity demand at each time step (W)"
    )
    m.P_pv_excess = Var(
        m.t, domain=Reals, doc="excess electricity from PV at each time step (W)"
    )
    m.E_s = Var(
        m.t,
        domain=Reals,
        doc="battery energy state of charge at each time step (Wh)",
    )
    m.Buying = Var(
        m.t,
        domain=Binary,
        doc="a binary variable preventing buying and selling of electricity",
    )
    m.Charging = Var(
        m.t,
        domain=Binary,
        doc="a binary variable that constraints charging power to prevent "
        "charging and discharging simultaneously at each time step",
    )
    m.Discharging = Var(
        m.t,
        domain=Binary,
        doc="a binary variable that constraints discharging power to prevent "
        "charging and discharging simultaneously at each time step",
    )

    # objective function
    m.obj = Objective(
        expr=sum(m.P_grid[t] * m.P_elec[t] - m.P_pv_export[t] * feed_in_t for t in m.t),
        sense=minimize,
    )

    # constraints
    m.c1 = Constraint(m.t, rule=lambda m, t: m.P_grid[t] >= 0)
    m.c2 = Constraint(m.t, rule=lambda m, t: m.P_grid[t] <= m.P_dmd_unmet[t])
    m.c3 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd_unmet[t] == m.P_dmd[t] - m.P_pv[t]
        if m.P_dmd[t] > m.P_pv[t]
        else Constraint.Skip,
    )
    m.c4 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd_unmet[t] == 0
        if m.P_dmd[t] <= m.P_pv[t]
        else Constraint.Skip,
    )
    m.c5 = Constraint(m.t, rule=lambda m, t: m.P_pv_export[t] >= 0)
    m.c6 = Constraint(expr=m.E_s[0] == E_batt_min)
    m.c7 = Constraint(m.t, rule=lambda m, t: m.P_pv_export[t] <= m.P_pv_excess[t])
    m.c8 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_excess[t] == m.P_pv[t] - m.P_dmd[t]
        if m.P_pv[t] > m.P_dmd[t]
        else Constraint.Skip,
    )
    m.c9 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_excess[t] == 0
        if m.P_pv[t] <= m.P_dmd[t]
        else Constraint.Skip,
    )
    m.c10 = Constraint(m.t, rule=lambda m, t: m.P_charge[t] >= m.Charging[t] * P_ch_min)
    m.c11 = Constraint(m.t, rule=lambda m, t: m.P_charge[t] <= m.Charging[t] * P_ch_max)
    m.c12 = Constraint(
        m.t, rule=lambda m, t: m.P_discharge[t] >= m.Discharging[t] * P_dis_min
    )
    m.c13 = Constraint(
        m.t, rule=lambda m, t: m.P_discharge[t] <= m.Discharging[t] * P_dis_max
    )
    m.c14 = Constraint(m.t, rule=lambda m, t: m.Charging[t] + m.Discharging[t] <= 1)
    m.c15 = Constraint(
        expr=sum(m.P_discharge[t] for t in m.t) <= sum(m.P_charge[t] for t in m.t),
    )
    m.c16 = Constraint(
        m.tf,
        rule=lambda m, t: m.E_s[t]
        == m.E_s[t - 1] + (eff * m.P_charge[t] - (m.P_discharge[t] / eff_dis)),
    )
    m.c17 = Constraint(
        m.t,
        rule=lambda m, t: m.E_s[0]
        == m.E_s[period - 1] + (eff * m.P_charge[0] - (m.P_discharge[0] / eff_dis)),
    )
    m.c18 = Constraint(
        m.t, rule=lambda m, t: m.P_pv_export[t] <= 50000000 * (1 - m.Buying[t])
    )
    m.c19 = Constraint(m.t, rule=lambda m, t: m.E_s[t] >= E_batt_min)
    m.c20 = Constraint(m.t, rule=lambda m, t: m.E_s[t] <= E_batt_max)
    m.c21 = Constraint(m.t, rule=lambda m, t: m.E_s[0] == m.E_s[period - 1])
    m.c22 = Constraint(m.t, rule=lambda m, t: m.P_grid[t] <= 50000000 * m.Buying[t])
    m.c23 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd[t]
        == m.P_grid[t]
        + m.P_pv[t]
        - m.P_pv_export[t]
        - m.P_charge[t]
        + m.P_discharge[t],
    )
    m.c24 = Constraint(m.t, rule=lambda m, t: m.P_pv[t] >= m.P_pv_export[t])
    # m.c26 = Constraint(m.t, rule=lambda m, t: m.P_dmd_unmet[t] >= m.P_grid[t])
    m.c25 = Constraint(
        m.t, rule=lambda m, t: m.P_discharge[t] + m.P_grid[t] == m.P_dmd_unmet[t]
    )
    return m


def setup_solver(optim, logfile="solver.log"):
    """
    Args:
        optim (SolverFactoryClass): The SolverFactoryClass object.
        logfile (str): the path/name of the log file.
    """
    if optim.name == "gurobi":
        # reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
        optim.set_options("logfile={}".format(logfile))
        # optim.set_options("timelimit=7200")  # seconds
        # optim.set_options("mipgap=5e-4")  # default = 1e-4
    elif optim.name == "glpk":
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    elif optim.name == "cplex":
        optim.set_options("log={}".format(logfile))
    else:
        print(
            "Warning from setup_solver: no options set for solver "
            "'{}'!".format(optim.name)
        )
    return optim


def run_model(model, solver="gurobi"):
    # solve model and read results
    model.optim = SolverFactory(solver)  # cplex, glpk, gurobi, ...
    model.optim = setup_solver(model.optim, logfile=f"{solver}_run.txt")
    result = model.optim.solve(model, tee=True)
    assert str(result.solver.termination_condition) == "optimal"
    return model


def read_model_results(model):
    # saving results to file
    entity_types = ["set", "par", "var"]
    if hasattr(model, "dual"):
        entity_types.append("con")
    entities = []
    for entity_type in entity_types:
        entities.extend(list_entities(model, entity_type).index.tolist())
    result_cache = {}
    for entity in entities:
        result_cache[entity] = get_entity(model, entity)
    df = DataFrame(result_cache)

    return df
