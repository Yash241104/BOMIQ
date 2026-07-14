import re


# ==========================================================
# Generic Engineering Number Parser
# ==========================================================

def parse_engineering_number(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    value = value.upper()

    # Remove symbols
    value = (
        value.replace("OHMS", "")
        .replace("OHM", "")
        .replace("Ω", "")
        .replace("±", "")
        .replace("µ", "U")
        .replace("μ", "U")
        .replace("Μ", "U")
        .replace(" ", "")
    )

    # Invalid values
    if value in ["-", "N/A", "NA"]:
        return None

    # ------------------------------------------------------
    # Fractions (1/4W, 1/8W ...)
    # ------------------------------------------------------

    value = value.replace("W", "")

    if "/" in value:

        try:

            num, den = value.split("/")

            return float(num) / float(den)

        except:

            pass

    # ------------------------------------------------------
    # Scientific prefixes inside number
    # 4K7
    # 2R2
    # 1M5
    # ------------------------------------------------------

    m = re.match(r'^(\d+)([RKMGUNP])(\d+)$', value)

    if m:

        left = m.group(1)

        prefix = m.group(2)

        right = m.group(3)

        value = left + "." + right + prefix

    # ------------------------------------------------------
    # Extract numeric + suffix
    # ------------------------------------------------------

    m = re.match(r'^([0-9]*\.?[0-9]+)([RKMGUNPMA]?)([FAHV]?)$', value)

    if not m:
        return None

    number = float(m.group(1))

    prefix = m.group(2)

    multipliers = {

        "P": 1e-12,
        "N": 1e-9,
        "U": 1e-6,
        "M": 1e6,
        "K": 1e3,
        "G": 1e9,
        "R": 1,
        "": 1

    }

    return number * multipliers.get(prefix, 1)


# ==========================================================
# Resistance
# ==========================================================

def normalize_resistance(value):

    x = parse_engineering_number(value)

    if x is None:
        return None

    return round(x, 6)


# ==========================================================
# Capacitance
# Return in pF
# ==========================================================

def normalize_capacitance(value):

    x = parse_engineering_number(value)

    if x is None:
        return None

    return round(x * 1e12, 3)


# ==========================================================
# Voltage
# ==========================================================

def normalize_voltage(value):

    if value is None:
        return None

    value = str(value).upper().strip()

    value = value.replace(" ", "")

    try:

        if "KV" in value:
            return float(value.replace("KV", "")) * 1000

        if "MV" in value:
            return float(value.replace("MV", "")) * 0.001

        if "VDC" in value:
            return float(value.replace("VDC", ""))

        if "VAC" in value:
            return float(value.replace("VAC", ""))

        if value.endswith("V"):
            return float(value[:-1])

        return float(value)

    except:

        return None

# ==========================================================
# Current
# ==========================================================

def normalize_current(value):

    if value is None:
        return None

    value = (
        str(value)
        .upper()
        .replace(" ", "")
    )

    if value.endswith("MA"):

        try:
            return float(value[:-2]) / 1000
        except:
            return None

    if value.endswith("A"):

        try:
            return float(value[:-1])
        except:
            return None

    try:
        return float(value)
    except:
        return None


# ==========================================================
# Power
# ==========================================================

def normalize_power(value):

    if value is None:
        return None

    value = (
        str(value)
        .upper()
        .replace(" ", "")
    )

    if value in ["", "-", "N/A"]:
        return None

    # DigiKey:
    # 0.25W,1/4W

    if "," in value:
        value = value.split(",")[0]

    value = value.strip()

    return parse_engineering_number(value)


# ==========================================================
# Tolerance
# ==========================================================

def normalize_tolerance(value):

    if value is None:
        return None

    value = (
        str(value)
        .replace("%", "")
        .replace("±", "")
        .strip()
    )

    try:
        return float(value)
    except:
        return None


# ==========================================================
# Package
# ==========================================================

def normalize_package(value):

    if value is None:
        return ""

    value = str(value).upper().strip()

    # -----------------------------
    # SMD resistor/capacitor packages
    # -----------------------------
    m = re.search(r'(0201|0402|0603|0805|1206|1210|1812|2010|2512)', value)

    if m:
        return m.group(1)

    # -----------------------------
    # TVS / Diode aliases
    # -----------------------------

    if (
        "DO-214AA" in value
        or "SMB" in value
    ):
        return "SMB"

    if "DO-214AB" in value or "SMC" in value or value == "SMC":
        return "SMC"

    if "DO-214AC" in value or "SMA" in value or value == "SMA":
        return "SMA"

    if "SOD-123" in value:
        return "SOD123"

    if "SOD-323" in value:
        return "SOD323"

    if "SOD-523" in value:
        return "SOD523"

    if "DO-41" in value:
        return "DO41"

    if "DO-15" in value:
        return "DO15"

    if "DO-201" in value:
        return "DO201"

    if "TO-220" in value:
        return "TO220"

    if "TO-247" in value:
        return "TO247"

    if "TO-252" in value:
        return "TO252"

    if "TO-263" in value:
        return "TO263"

    if "SOIC" in value:
        return "SOIC"

    if "SOP" in value:
        return "SOP"

    if "SSOP" in value:
        return "SSOP"

    if "TSSOP" in value:
        return "TSSOP"

    if "QFN" in value:
        return "QFN"

    if "QFP" in value:
        return "QFP"

    if "DIP" in value:
        return "DIP"

    return value