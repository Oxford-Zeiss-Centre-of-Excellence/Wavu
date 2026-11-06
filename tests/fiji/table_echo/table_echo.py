"""Returns the input table's row count and the table itself, with a derived column."""

PARAMS = {}


def run(ctx, inputs, params):
    table = inputs["table"]
    out = table.copy()
    out["area_x2"] = 2 * out["area"]
    return {"n_rows": int(len(table)), "columns": ",".join(str(c) for c in table.columns), "table": out}
