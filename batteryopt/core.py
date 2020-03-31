# from csv import reader
import pandas as pd
from pandas import DataFrame
from path import Path
from pyomo.environ import *
from pyomo.opt import SolverFactory

from batteryopt import list_entities, get_entity


def create_model(
    demand_csv,
    pvgen_csv,
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
    M=50000000,
):
    """
    Args:
        demand_csv (PathLike): file containing the electricity demand (W).
        pvgen_csv (PathLike): file containing the PV generation (W).
        price_of_el (float or PathLike): If float, a single price is used for
            all time steps. If a .csv is passed, the column named "PRICE" is
            used. Units are $/Wh.
        feed_in_t (float): $/Wh
        P_ch_min (float): minimum battery charging power (W).
        P_ch_max (float): maximum battery charging power (W).
        P_dis_min (float): minimum battery discharging power (W).
        P_dis_max (float): maximum battery discharging power (W).
        eff (float): charging efficiency (-).
        eff_dis (float): discharging efficiency (-).
        E_batt_min (float): battery minimum energy state of charge (Wh).
        E_batt_max (float): battery maximum energy state of charge (Wh).
        M (float): an arbitrarily chosen number that is big enough to ensure a
         feasible solution.
    """
    m = ConcreteModel()

    if isinstance(price_of_el, (str, Path)):
        # Use file as electricity price
        price = pd.read_csv(price_of_el)  # read hourly electricity price from csv file
        price_of_el = price.PRICE.to_dict()
    else:
        price_of_el = {k: price_of_el for k in range(0, 8760)}

    # Sets
    m.t = Set(initialize=list(range(0, 8760)), ordered=True, doc="Set of timesteps")
    m.tf = Set(
        within=m.t,
        initialize=list(range(0, 8760))[1:],
        ordered=True,
        doc="Set of modelled time steps",
    )

    # Parameters
    generation = pd.read_csv(pvgen_csv).SUM_GENERATION
    m.P_pv = Param(
        m.t,
        initialize=generation.to_dict(),
        doc="Generation from installed PV at each hour",
    )
    demand = pd.read_csv(demand_csv).SUM_DEMAND
    m.P_dmd = Param(
        m.t, initialize=demand.to_dict(), doc="Electricity demand at each time step",
    )
    m.P_elec = Param(
        m.t, initialize=price_of_el, doc="Price of electricity at each time step",
    )
    m.M = Param(initialize=M, doc="Arbitrary number used to ensure feasible solutions")

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
        m.t, domain=Reals, doc="battery energy state of charge at each time step (Wh)",
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
        expr=sum(
            [m.P_pv_export[t] * feed_in_t - m.P_grid[t] * m.P_elec[t] for t in m.t]
        ),
        sense=maximize,
        doc="",  # todo: document this method
    )

    # constraints
    m.c1 = Constraint(
        m.t,
        rule=lambda m, t: m.P_grid[t] >= 0,
        doc="Energy imported from the grid at each hour is always bigger or equal "
        "to zero at each hour",
    )
    m.c2 = Constraint(
        m.t,
        rule=lambda m, t: m.P_grid[t] <= m.P_dmd_unmet[t],
        doc="Energy imported from the grid at each hour is always smaller or equal "
        "to the unmet electricity demand at each hour",
    )
    m.c3 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd_unmet[t] == m.P_dmd[t] - m.P_pv[t]
        if m.P_dmd[t] > m.P_pv[t]
        else Constraint.Skip,
        doc="If the total demand is bigger than the power supplied by PV, the unmet "
        "demand is equal to the difference of total demand and the power supplied "
        "by PV",
    )
    m.c4 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd_unmet[t] == 0
        if m.P_dmd[t] <= m.P_pv[t]
        else Constraint.Skip,
        doc="If the total demand is smaller or equal to the power supplied by PV, "
        "the unmet demand is equal zero â€“ the demand is met by the electricity "
        "produced by PV",
    )
    m.c5 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_export[t] >= 0,
        doc="Energy sold to grid is always equal or bigger than zero",
    )
    m.c6 = Constraint(expr=m.E_s[0] == E_batt_min, doc="")  # todo: document this method
    m.c7 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_export[t] <= m.P_pv_excess[t],
        doc="Energy sold to grid is always smaller or equal to the excess energy",
    )
    m.c8 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_excess[t] == m.P_pv[t] - m.P_dmd[t]
        if m.P_pv[t] > m.P_dmd[t]
        else Constraint.Skip,
        doc="If the energy produced by PV is bigger than the total demand, the "
        "excess energy is defined as a difference between the energy produced "
        "by PV and the total demand",
    )
    m.c9 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_excess[t] == 0
        if m.P_pv[t] <= m.P_dmd[t]
        else Constraint.Skip,
        doc="If the energy produced by PV is smaller or equal to the total demand, "
        "the excess energy is zero",
    )
    m.c10 = Constraint(
        m.t,
        rule=lambda m, t: m.P_charge[t] >= m.Charging[t] * P_ch_min,
        doc="When the battery is charging, the charging power must be bigger or equal "
        "to the minimum charging power",
    )
    m.c11 = Constraint(
        m.t,
        rule=lambda m, t: m.P_charge[t] <= m.Charging[t] * P_ch_max,
        doc="When the battery is charging, the charging power must be smaller or equal"
        " the maximum charging power",
    )
    m.c12 = Constraint(
        m.t,
        rule=lambda m, t: m.P_discharge[t] >= m.Discharging[t] * P_dis_min,
        doc="When the battery is discharging, the discharging power must be bigger or "
        "equal to the minimum discharging power",
    )
    m.c13 = Constraint(
        m.t,
        rule=lambda m, t: m.P_discharge[t] <= m.Discharging[t] * P_dis_max,
        doc="When the battery is discharging, the discharging power smaller or equal "
        "the maximum discharging power",
    )
    m.c14 = Constraint(
        m.t,
        rule=lambda m, t: m.Charging[t] + m.Discharging[t] <= 1,
        doc="The battery cannot charge and discharge simultaneously",
    )
    m.c15 = Constraint(
        expr=sum(m.P_discharge[t] for t in m.t) <= sum(m.P_charge[t] for t in m.t),
        doc="Over time the total discharge from the battery will be smaller or equal "
        "to its total charge",
    )
    m.c16 = Constraint(
        m.tf,
        rule=lambda m, t: m.E_s[t]
        == m.E_s[t - 1] + (eff * m.P_charge[t] - (m.P_discharge[t] / eff_dis)),
        doc="At each next time step (hour) the battery SoC is equal to the SoC at "
        "the previous step plus/minus the charge/discharge of the battery",
    )
    m.c17 = Constraint(
        expr=m.E_s[0]
        == m.E_s[8759] + (eff * m.P_charge[0] - (m.P_discharge[0] / eff_dis)),
        doc="Constraint c16 applied to the end and beginning of the year",
    )
    m.c18 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv_export[t] <= m.M * (1 - m.Buying[t]),
        doc="",  # todo: document this method
    )
    m.c19 = Constraint(
        m.t,
        rule=lambda m, t: (E_batt_min, m.E_s[t], E_batt_max),
        doc="The state of charge of the battery is between its minimum and maximum "
        "values at each time",
    )

    m.c21 = Constraint(
        m.t,
        rule=lambda m, t: m.E_s[0] == m.E_s[8759],
        doc="Battery SoC at the end of the year is equal to the battery SoC in the "
        "beginning of the year",
    )
    m.c22 = Constraint(
        m.t,
        rule=lambda m, t: m.P_grid[t] <= m.M * m.Buying[t],
        doc="Assures that the electricity is not sold and bought at the same time. M "
        "is an arbitrarily chosen number that is big enough to ensure a feasible "
        "solution",
    )
    m.c23 = Constraint(
        m.t,
        rule=lambda m, t: m.P_dmd[t]
        == m.P_grid[t]
        + m.P_pv[t]
        - m.P_pv_export[t]
        - m.P_charge[t]
        + m.P_discharge[t],
        doc="Total demand is equal to the electricity bought from grid plus "
        "electricity produced by the PV plus electricity discharged from the "
        "battery minus electricity from PV used to charge the battery and "
        "electricity sold to the grid at each time step",
    )
    m.c24 = Constraint(
        m.t,
        rule=lambda m, t: m.P_pv[t] >= m.P_pv_export[t],
        doc="",  # todo: document this method
    )
    # m.c26 = Constraint(m.t, rule=lambda m, t: m.P_dmd_unmet[t] >= m.P_grid[t],
    # doc="") todo: document this method
    m.c25 = Constraint(
        m.t,
        rule=lambda m, t: m.P_discharge[t] + m.P_grid[t] == m.P_dmd_unmet[t],
        doc="The unmet demand is equal to the amount of energy discharged from the "
        "battery and bought from the grid at each time step",
    )
    return m


def setup_solver(optim, logfile="solver.log"):
    """
    Args:
        optim:
        logfile:
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
    optim = SolverFactory(solver)  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile="log_filename.txt")
    result = optim.solve(model, tee=True)
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
