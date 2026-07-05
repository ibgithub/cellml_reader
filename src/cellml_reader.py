import os
import libcellml

ALLOWED_UNITS = {"microA_per_cm2", "uA_per_mm2", "uA_per_mmsq", "nanoA"}

def read_cellml(cellml_file):
    variables = []

    if not os.path.isfile(cellml_file):
        raise FileNotFoundError(f"{cellml_file} not found")

    with open(cellml_file, "r") as f:
        cellml_content = f.read()

    parser = libcellml.Parser()
    parser.setStrict(False)

    model = parser.parseModel(cellml_content)

    if parser.issueCount() > 0:
        print("Issues found:")
        for i in range(parser.issueCount()):
            print("-", parser.issue(i).description())

    print("")

    for i in range(model.componentCount()):
        component = model.component(i)

        if component.name() == "membrane":
            continue

        for j in range(component.variableCount()):
            variable = component.variable(j)

            unit_name = variable.units().name() if variable.units() else "N/A"

            if unit_name in ALLOWED_UNITS:

                variables.append({
                    "component": component.name(),
                    "variable": variable.name(),
                    "unit": unit_name
                })

    return variables