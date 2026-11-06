"""Receives a table input (from a scripted caller) and returns its row count and a derived table."""

PARAMS = {
    "column": {"type": "str", "default": "area"},
}


def run(ctx, inputs, params):
    table = inputs["table"]
    col = params["column"]
    if isinstance(table, list):  # no pandas in this env: csv.DictReader rows (strings)
        rows = [{**r, "double": 2 * float(r[col])} for r in table]
        return {"n_rows": len(table), "kind": "rows", "doubled": rows}
    out = table.copy()
    out["double"] = 2 * out[col]
    return {"n_rows": int(len(table)), "kind": type(table).__name__, "doubled": out}
