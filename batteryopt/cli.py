import click


@click.command()
@click.option("--p", default=0.0002624,
              type=click.FLOAT, help="Price of electricity $/Wh")
@click.option("--f", default=0.0000791,
              type=click.FLOAT, help="Feed in tariff $/Wh")
@click.option("--cmin", default=100,
              type=click.FLOAT, help="minimum battery charging power (W)")
@click.option("--cmax", default=32000,
              type=click.FLOAT, help='maximum battery charging power (W)')
@click.option("--dmin", default=100,
              type=click.FLOAT, help="minimum battery discharging power (W)")
@click.option("--dmax", default=32000,
              type=click.FLOAT, help="maximum battery discharging power (W)")
@click.option("--ceff", default=1,
              type=click.FLOAT, help="charging efficiency")
@click.option("--deff", default=1,
              type=click.FLOAT, help="discharging efficiency")
@click.option("--smin", default=20000,
              type=click.FLOAT,help="battery minimum energy state of charge (Wh)")
@click.option("--smax", default=100000,
              type=click.FLOAT, help="battery maximum energy state of charge (Wh)")
@click.argument("out", type=click.File("w"), default="Pbought_aggregated.csv")
def batteryopt(p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax, out):
    """Example script."""
    from batteryopt import create_model
    from pandas import Series

    model = create_model(p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax)
    model.optimize()
    # saving results to file
    var = Series(
        [str(v.X) for v in model.getVars() if v.varName == "P_grid"], name="P_grid"
    )
    var.to_csv(out, index_label="Time Step", line_terminator='\n')
