from normalizers import *

WEIGHTS = {
    "Resistance": 50,
    "Capacitance": 50,
    "Voltage": 15,
    "Tolerance": 15,
    "Power": 10,
    "Package": 20,
    "Current": 30,
    "Dielectric": 15,
    "Inductance": 50,
    "MPN": 100
}


# ==========================================================
# Helper Functions
# ==========================================================

def add_match(score, matched, weight, name):
    score += weight
    matched.append(name)
    return score


def add_mismatch(mismatched, name):
    mismatched.append(name)


# ----------------------------------------------------------
# Exact comparison
# ----------------------------------------------------------

def compare_equal(
    required,
    found,
    normalize,
    field,
    weight,
    score,
    max_score,
    matched,
    mismatched,
    optional=False
):

    required = normalize(required)

    if optional and (required is None or required == ""):
        return score, max_score

    found = normalize(found)

    max_score += weight

    if required == found:
        score = add_match(score, matched, weight, field)
    else:
        add_mismatch(mismatched, field)

    return score, max_score



def compare_contains(
    required,
    found,
    field,
    weight,
    score,
    max_score,
    matched,
    mismatched,
    optional=True
):

    required = str(required).strip().upper()

    if optional and required in ("", "NONE"):
        return score, max_score

    found = str(found).strip().upper()

    max_score += weight

    if required in found:

        score = add_match(score, matched, weight, field)

    else:

        add_mismatch(mismatched, field)

    return score, max_score
# ----------------------------------------------------------
# Minimum comparison
# ----------------------------------------------------------

def compare_min(
    required,
    found,
    normalize,
    field,
    weight,
    score,
    max_score,
    matched,
    mismatched,
    optional=True
):

    required = normalize(required)

    if optional and required is None:
        return score, max_score

    found = normalize(found)

    max_score += weight

    if (
        required is not None
        and found is not None
        and found >= required
    ):

        score = add_match(score, matched, weight, field)

    else:

        add_mismatch(mismatched, field)

    return score, max_score

def compare_close(
    required,
    found,
    normalize,
    tolerance,
    field,
    weight,
    score,
    max_score,
    matched,
    mismatched,
    optional=True
):

    required = normalize(required)

    if optional and required is None:
        return score, max_score

    found = normalize(found)

    max_score += weight

    if (
        required is not None
        and found is not None
        and abs(found - required) <= tolerance
    ):

        score = add_match(score, matched, weight, field)

    else:

        add_mismatch(mismatched, field)

    return score, max_score




# ----------------------------------------------------------
# Package comparison
# ----------------------------------------------------------

def compare_package(
    required,
    found,
    score,
    max_score,
    matched,
    mismatched
):

    required = normalize_package(required)

    if required == "":
        return score, max_score

    found = normalize_package(found)

    max_score += WEIGHTS["Package"]

    if required == found:

        score = add_match(
            score,
            matched,
            WEIGHTS["Package"],
            "Package"
        )

    else:

        add_mismatch(
            mismatched,
            "Package"
        )

    return score, max_score


# ----------------------------------------------------------
# MPN comparison
# ----------------------------------------------------------

def compare_mpn(
    required,
    found,
    score,
    max_score,
    matched,
    mismatched
):

    required = (
        str(required)
        .upper()
        .replace("-", "")
        .replace("/", "")
        .replace(" ", "")
    )

    found = (
        str(found)
        .upper()
        .replace("-", "")
        .replace("/", "")
        .replace(" ", "")
    )

    max_score += WEIGHTS["MPN"]

    if required == "":
        add_mismatch(mismatched, "MPN")
        return score, max_score

    if found.startswith(required):

        score = add_match(
            score,
            matched,
            WEIGHTS["MPN"],
            "MPN"
        )

    else:

        add_mismatch(
            mismatched,
            "MPN"
        )

    return score, max_score


# ==========================================================
# Main Validator
# ==========================================================

def score_candidate(engineering_row, product):

    params = product.get("Parameters", {})

    score = 0
    max_score = 0

    matched = []
    mismatched = []

    part_type = engineering_row["Part Type"]


    # ==========================================================
    # RESISTOR
    # ==========================================================

    if part_type == "Resistor":

        score, max_score = compare_equal(
            engineering_row["Value"],
            params.get("Resistance", ""),
            normalize_resistance,
            "Resistance",
            WEIGHTS["Resistance"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get("Package / Case", ""),
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_equal(
            engineering_row["Tolerance"],
            params.get("Tolerance", ""),
            normalize_tolerance,
            "Tolerance",
            WEIGHTS["Tolerance"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_min(
            engineering_row["Power Rating"],
            params.get("Power (Watts)", ""),
            normalize_power,
            "Power",
            WEIGHTS["Power"],
            score,
            max_score,
            matched,
            mismatched
        )

    # ==========================================================
    # CERAMIC CAPACITOR
    # ==========================================================

    elif part_type == "Ceramic Capacitor":

    # ---------- Capacitance ----------

        score, max_score = compare_equal(
            engineering_row["Value"],
            params.get("Capacitance", ""),
            normalize_capacitance,
            "Capacitance",
            WEIGHTS["Capacitance"],
            score,
            max_score,
            matched,
            mismatched
        )

        # ---------- Voltage ----------

        score, max_score = compare_min(
            engineering_row["Voltage Rating"],
            params.get("Voltage - Rated", ""),
            normalize_voltage,
            "Voltage",
            WEIGHTS["Voltage"],
            score,
            max_score,
            matched,
            mismatched
        )

        # ---------- Package ----------

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get("Package / Case", ""),
            score,
            max_score,
            matched,
            mismatched
        )

        # ---------- Dielectric ----------

        score, max_score = compare_contains(
            engineering_row["Dielectric"],
            params.get("Temperature Coefficient", ""),
            "Dielectric",
            WEIGHTS["Dielectric"],
            score,
            max_score,
            matched,
            mismatched
        )

    # ==========================================================
    # ELECTROLYTIC CAPACITOR
    # ==========================================================

    elif part_type == "Electrolytic Capacitor":

        score, max_score = compare_equal(
            engineering_row["Value"],
            params.get("Capacitance", ""),
            normalize_capacitance,
            "Capacitance",
            WEIGHTS["Capacitance"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_min(
            engineering_row["Voltage Rating"],
            params.get("Voltage - Rated", ""),
            normalize_voltage,
            "Voltage",
            WEIGHTS["Voltage"],
            score,
            max_score,
            matched,
            mismatched
        )


    # ==========================================================
    # INDUCTOR
    # ==========================================================

    elif part_type == "Inductor":

        score, max_score = compare_min(
            engineering_row["Current Rating"],
            params.get("Current Rating (Amps)", ""),
            normalize_current,
            "Current",
            WEIGHTS["Current"],
            score,
            max_score,
            matched,
            mismatched
        )


    # ==========================================================
    # DIODE
    # ==========================================================

    elif part_type == "Diode":

        # --------------------------------------------------
        # Case 1 : BOM specifies only MPN
        # --------------------------------------------------

        if (
            engineering_row["Voltage Rating"] == ""
            and engineering_row["Current Rating"] == ""
            and engineering_row["Package"] == ""
        ):

            score, max_score = compare_mpn(
                engineering_row["Value"],
                product.get("Manufacturer Part Number", ""),
                score,
                max_score,
                matched,
                mismatched
            )

        # --------------------------------------------------
        # Case 2 : BOM specifies electrical parameters
        # --------------------------------------------------

        else:

            score, max_score = compare_min(
                engineering_row["Current Rating"],
                params.get("Current - Average Rectified (Io)", ""),
                normalize_current,
                "Current",
                WEIGHTS["Current"],
                score,
                max_score,
                matched,
                mismatched
            )

            score, max_score = compare_min(
                engineering_row["Voltage Rating"],
                params.get("Voltage - DC Reverse (Vr) (Max)", ""),
                normalize_voltage,
                "Voltage",
                WEIGHTS["Voltage"],
                score,
                max_score,
                matched,
                mismatched
            )

            score, max_score = compare_package(
                engineering_row["Package"],
                params.get("Package / Case", ""),
                score,
                max_score,
                matched,
                mismatched
            )


    # ==========================================================
    # ZENER
    # ==========================================================

    elif part_type == "Zener":

        score, max_score = compare_close(
            engineering_row["Voltage Rating"],
            params.get("Voltage - Zener (Nom) (Vz)", ""),
            normalize_voltage,
            0.5,
            "Voltage",
            WEIGHTS["Voltage"],
            score,
            max_score,
            matched,
            mismatched,
            optional=False
        )

        score, max_score = compare_min(
            engineering_row["Power Rating"],
            params.get("Power - Max", ""),
            normalize_power,
            "Power",
            WEIGHTS["Power"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get("Package / Case", ""),
            score,
            max_score,
            matched,
            mismatched
        )


    # ==========================================================
    # TVS
    # ==========================================================

    elif part_type == "TVS":

        score, max_score = compare_min(
            engineering_row["Voltage Rating"],
            params.get("Voltage - Reverse Standoff (Typ)", ""),
            normalize_voltage,
            "Voltage",
            WEIGHTS["Voltage"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get(
                "Supplier Device Package",
                params.get("Package / Case", "")
            ),
            score,
            max_score,
            matched,
            mismatched
        )


    # ==========================================================
    # BRIDGE RECTIFIER
    # ==========================================================

    elif part_type == "Bridge Rectifier":

        score, max_score = compare_min(
            engineering_row["Current Rating"],
            params.get("Current - Average Rectified (Io)", ""),
            normalize_current,
            "Current",
            WEIGHTS["Current"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_min(
            engineering_row["Voltage Rating"],
            params.get("Voltage - Peak Reverse (Max)", ""),
            normalize_voltage,
            "Voltage",
            WEIGHTS["Voltage"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get("Package / Case", ""),
            score,
            max_score,
            matched,
            mismatched
        )

    # ==========================================================
    # NTC
    # ==========================================================

    elif part_type == "NTC":

        score, max_score = compare_equal(
            engineering_row["Value"],
            params.get("Resistance @ 25°C", ""),
            normalize_resistance,
            "Resistance",
            WEIGHTS["Resistance"],
            score,
            max_score,
            matched,
            mismatched
        )

        score, max_score = compare_equal(
            engineering_row["Tolerance"],
            params.get("Resistance Tolerance", ""),
            normalize_tolerance,
            "Tolerance",
            WEIGHTS["Tolerance"],
            score,
            max_score,
            matched,
            mismatched,
            optional=True
        )

        score, max_score = compare_package(
            engineering_row["Package"],
            params.get(
                "Supplier Device Package",
                params.get("Package / Case", "")
            ),
            score,
            max_score,
            matched,
            mismatched
        )


    # ==========================================================
    # IC
    # ==========================================================

    elif part_type == "IC":

        score, max_score = compare_mpn(
            engineering_row["Value"],
            product.get("Manufacturer Part Number", ""),
            score,
            max_score,
            matched,
            mismatched
        )

    # ==========================================================
    # UNKNOWN
    # ==========================================================

    else:

        max_score = 1

        add_mismatch(
            mismatched,
            "Unknown"
        )


    percentage = (
        round(score / max_score * 100, 1)
        if max_score
        else 0
    )

    if percentage == 100:

        status = "Found"

    elif percentage >= 20:

        status = "Partially Matched"

    elif percentage > 0:

        status = "Few Parameters Matched"

    else:

        status = "Not Found"

    return {

        "Score": percentage,
        "Status": status,
        "Matched": matched,
        "Mismatched": mismatched,
        "Max Score": max_score

    }

