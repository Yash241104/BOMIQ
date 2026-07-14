import pandas as pd


def get_part_type(libref):

    libref = str(libref).strip().lower()

    if libref == "resistor":
        return "Resistor"

    elif libref == "capacitor":
        return "Ceramic Capacitor"

    elif libref == "ecapacitor":
        return "Electrolytic Capacitor"

    elif libref == "inductor":
        return "Inductor"

    elif libref == "diode":
        return "Diode"

    elif libref == "mov":
        return "MOV"

    else:
        return "IC"


def parse_resistor(comment):

    tokens = str(comment).split()

    value = ""
    tolerance = "5%"
    power = "0.25W"
    package = ""

    autofilled = []

    if len(tokens) >= 1:
        value = tokens[0]

    if len(tokens) == 2:
        package = tokens[1]
        autofilled.extend(["Tolerance", "Power Rating"])

    elif len(tokens) == 3:
        tolerance = tokens[1]
        package = tokens[2]
        autofilled.append("Power Rating")

    elif len(tokens) >= 4:
        tolerance = tokens[1]
        power = tokens[2]
        package = tokens[3]

    remarks = (
        "User Provided All Fields"
        if not autofilled
        else f"Auto-filled: {', '.join(autofilled)}"
    )

    return {
        "Value": value,
        "Package": package,
        "Voltage Rating": "",
        "Current Rating": "",
        "Power Rating": power,
        "Tolerance": tolerance,
        "Dielectric": "",
        "Remarks": remarks
    }


def parse_ceramic_capacitor(comment):

    tokens = str(comment).split()

    value = ""
    voltage = "50V"
    dielectric = "X7R"
    package = ""

    autofilled = []

    if len(tokens) >= 1:
        value = tokens[0]

    if len(tokens) == 2:
        package = tokens[1]
        autofilled.extend(
            ["Voltage Rating", "Dielectric"]
        )

    elif len(tokens) == 3:
        voltage = tokens[1]
        package = tokens[2]
        autofilled.append("Dielectric")

    elif len(tokens) >= 4:
        voltage = tokens[1]
        dielectric = tokens[2]
        package = tokens[3]

    remarks = (
        "User Provided All Fields"
        if not autofilled
        else f"Auto-filled: {', '.join(autofilled)}"
    )

    return {
        "Value": value,
        "Package": package,
        "Voltage Rating": voltage,
        "Current Rating": "",
        "Power Rating": "",
        "Tolerance": "10%",
        "Dielectric": dielectric,
        "Remarks": remarks
    }


def parse_electrolytic_capacitor(comment):

    tokens = str(comment).split()

    value = ""
    voltage = "50V"

    autofilled = []

    if len(tokens) >= 1:
        value = tokens[0]

    if len(tokens) >= 2:
        voltage = tokens[1]
    else:
        autofilled.append("Voltage Rating")

    remarks = (
        "User Provided All Fields"
        if not autofilled
        else f"Auto-filled: {', '.join(autofilled)}"
    )

    return {
        "Value": value,
        "Package": "",
        "Voltage Rating": voltage,
        "Current Rating": "",
        "Power Rating": "",
        "Tolerance": "20%",
        "Dielectric": "",
        "Remarks": remarks
    }


def parse_inductor(comment):

    tokens = str(comment).split()

    value = ""
    current = ""

    if len(tokens) >= 1:
        value = tokens[0]

    if len(tokens) >= 2:
        current = tokens[1]

    return {
        "Value": value,
        "Package": "",
        "Voltage Rating": "",
        "Current Rating": current,
        "Power Rating": "",
        "Tolerance": "",
        "Dielectric": "",
        "Remarks": "User Provided All Fields"
    }


def parse_diode(comment):

    return {
        "Value": str(comment),
        "Package": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Power Rating": "",
        "Tolerance": "",
        "Dielectric": "",
        "Remarks": "Exact Part"
    }


def parse_mov(comment):

    return {
        "Value": str(comment),
        "Package": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Power Rating": "",
        "Tolerance": "",
        "Dielectric": "",
        "Remarks": "Exact Part"
    }


def parse_ic(comment):

    return {
        "Value": str(comment),
        "Package": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Power Rating": "",
        "Tolerance": "",
        "Dielectric": "",
        "Remarks": "Exact Part"
    }


def generate_intermediate_bom(df):

    intermediate_rows = []

    for _, row in df.iterrows():

        comment = str(row.get("Comment", ""))
        libref = str(row.get("LibRef", ""))

        designator = row.get("Designator", "")
        quantity = row.get("Quantity", "")

        part_type = get_part_type(libref)

        if part_type == "Resistor":
            parsed = parse_resistor(comment)

        elif part_type == "Ceramic Capacitor":
            parsed = parse_ceramic_capacitor(comment)

        elif part_type == "Electrolytic Capacitor":
            parsed = parse_electrolytic_capacitor(comment)

        elif part_type == "Inductor":
            parsed = parse_inductor(comment)

        elif part_type == "Diode":
            parsed = parse_diode(comment)

        elif part_type == "MOV":
            parsed = parse_mov(comment)

        else:
            parsed = parse_ic(comment)

        intermediate_rows.append({

            "Designator": designator,
            "Quantity": quantity,
            "Part Type": part_type,

            "Value": parsed["Value"],
            "Package": parsed["Package"],
            "Voltage Rating": parsed["Voltage Rating"],
            "Current Rating": parsed["Current Rating"],
            "Power Rating": parsed["Power Rating"],
            "Tolerance": parsed["Tolerance"],
            "Dielectric": parsed["Dielectric"],
            "Remarks": parsed["Remarks"]
        })

    return pd.DataFrame(intermediate_rows)