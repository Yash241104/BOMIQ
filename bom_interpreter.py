import re
import pandas as pd

# =====================================================
# Standard Packages
# =====================================================

PACKAGES = [

    # Chip
    "0201",
    "0402",
    "0603",
    "0805",
    "1206",
    "1210",
    "1812",
    "2010",
    "2512",

    # Diodes
    "SOD123",
    "SOD323",
    "SOD523",
    "SMA",
    "SMB",
    "SMC",
    "DO-214AA",
    "DO-214AB",
    "DO-214AC",

    # Bridge
    "GBI-4",
    "GBJ",
    "GBU",
    "KBP",
    "KBJ",
    "KBL",
    "KBU",

    # IC
    "SOIC",
    "SOP",
    "SSOP",
    "TSSOP",
    "MSOP",
    "QFN",
    "QFP",
    "LQFP",
    "TQFP",
    "DIP",
    "SOT23",
    "TO220",
    "TO247"

]

# =====================================================
# Ceramic Dielectrics
# =====================================================

DIELECTRICS = [

    "X7R",
    "X5R",
    "C0G",
    "NP0",
    "Y5V"

]

# =====================================================
# Prefixes
# =====================================================

IC_PREFIXES = [

    "STM",
    "VIPER",
    "TL",
    "LM",
    "UC",
    "ICE",
    "ATMEGA",
    "PIC",
    "ESP",
    "TPS",
    "MC",
    "IR"

]

DIODE_PREFIXES = [

    "UF",
    "US",
    "FR",
    "ES",
    "HER",
    "MUR",
    "RS",
    "1N",
    "BAV",
    "BAT",
    "MBR",
    "SS"

]

MOV_PREFIXES = [

    "MOV",
    "07D",
    "10D",
    "14D",
    "20D",
    "S07",
    "S10",
    "S14",
    "S20"

]

# =====================================================
# Part Type Detection
# =====================================================

def detect_part_type(row):

    description = str(row.get("Description", "")).upper()
    comment = str(row.get("Comment", "")).upper()
    footprint = str(row.get("Footprint", "")).upper()
    libref = str(row.get("LibRef", "")).upper()

    text = " ".join([
        description,
        comment,
        footprint,
        libref
    ])

    # -------------------------------------------------
    # Bridge Rectifier
    # -------------------------------------------------

    if (
        "BRIDGE RECTIFIER" in text
        or "RECTIFIER BRIDGE" in text
    ):
        return "Bridge Rectifier"

    # -------------------------------------------------
    # TVS
    # -------------------------------------------------

    if (
        "TVS" in text
        or "TRANSIENT VOLTAGE SUPPRESSOR" in text
    ):
        return "TVS"

    # -------------------------------------------------
    # Zener
    # -------------------------------------------------

    if "ZENER" in text:
        return "Zener"

    # -------------------------------------------------
    # MOV
    # -------------------------------------------------

    if (
        any(prefix in text for prefix in MOV_PREFIXES)
        or "METAL OXIDE VARISTOR" in text
    ):
        return "MOV"

    # -------------------------------------------------
    # NTC
    # -------------------------------------------------

    if (
        "NTC" in text
        or "THERMISTOR" in text
    ):
        return "NTC"

    # -------------------------------------------------
    # IC
    # -------------------------------------------------

    if any(prefix in text for prefix in IC_PREFIXES):
        return "IC"

    # -------------------------------------------------
    # Inductor
    # -------------------------------------------------

    if (
        "INDUCTOR" in text
        or re.search(r"\d+(\.\d+)?(NH|UH|MH)\b", text)
    ):
        return "Inductor"

    # -------------------------------------------------
    # Capacitors
    # -------------------------------------------------

    if re.search(r"\d+(\.\d+)?(PF|NF|UF)\b", text):

        if any(pkg in text for pkg in PACKAGES):
            return "Ceramic Capacitor"

        return "Electrolytic Capacitor"

    # -------------------------------------------------
    # Standard Diode
    # -------------------------------------------------

    if (
        any(prefix in text for prefix in DIODE_PREFIXES)
        or (
            "DIODE" in text
            and "TVS" not in text
            and "ZENER" not in text
        )
    ):
        return "Diode"

    # -------------------------------------------------
    # Resistor
    # -------------------------------------------------

    if re.search(

        r'(\d+(\.\d+)?[RKM]|[RKM]\d+|\d+\s*OHM|\d+\s*Ω)',

        text

    ):
        return "Resistor"

    return "Unknown"


def extract_resistor(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    # Resistance
    match = re.search(
        r'(\d+(?:\.\d+)?(?:R|K|M)|\d+\.\d+[KM]|[RKM]\d+|\d+\s*OHM|\d+\s*Ω)',
        text
    )

    if match:
        attributes["Value"] = (
            match.group(1)
            .replace("OHM", "")
            .replace("Ω", "")
            .strip()
        )

    # Package
    for pkg in PACKAGES:
        if pkg in text:
            attributes["Package"] = pkg
            break

    # Tolerance
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if match:
        attributes["Tolerance"] = match.group(1) + "%"

    # Power
    match = re.search(r'(\d+(?:\.\d+)?)\s*W', text)
    if match:
        attributes["Power Rating"] = match.group(1) + "W"

    return attributes


def extract_ceramic_capacitor(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    # Capacitance
    match = re.search(r'(\d+(?:\.\d+)?(?:PF|NF|UF))', text)
    if match:
        attributes["Value"] = match.group(1)

    # Voltage
    match = re.search(r'(\d+(?:\.\d+)?)V', text)
    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    # Dielectric
    for dielectric in DIELECTRICS:
        if dielectric in text:
            attributes["Dielectric"] = dielectric
            break

    # Package
    for pkg in PACKAGES:
        if pkg in text:
            attributes["Package"] = pkg
            break

    return attributes



def extract_electrolytic_capacitor(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    match = re.search(r'(\d+(?:\.\d+)?UF)', text)
    if match:
        attributes["Value"] = match.group(1)

    match = re.search(r'(\d+(?:\.\d+)?)V', text)
    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    return attributes



def extract_inductor(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    # Inductance
    match = re.search(r'(\d+(?:\.\d+)?(?:NH|UH|MH))', text)
    if match:
        attributes["Value"] = match.group(1)

    # Current
    match = re.search(r'(\d+(?:\.\d+)?)A', text)
    if match:
        attributes["Current Rating"] = match.group(1) + "A"

    # Tolerance
    match = re.search(r'(\d+(?:\.\d+)?)%', text)
    if match:
        attributes["Tolerance"] = match.group(1) + "%"

    return attributes


def extract_diode(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    # Part Number
    match = re.search(
        r'\b(UF\d+\w*|US\d+\w*|FR\d+\w*|HER\d+\w*|MUR\d+\w*|RS\d+\w*|1N\d+\w*|SS\d+\w*|MBR\d+\w*)\b',
        text
    )

    if match:
        attributes["Value"] = match.group(1)

    # Voltage
    match = re.search(r'(\d+(?:\.\d+)?)V', text)

    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    # Current
    match = re.search(r'(\d+(?:\.\d+)?)A', text)

    if match:
        attributes["Current Rating"] = match.group(1) + "A"

    # Package
    for pkg in PACKAGES:

        if pkg in text:
            attributes["Package"] = pkg
            break

    return attributes



def extract_zener(text):

    attributes = {
        "Value":"",
        "Package":"",
        "Tolerance":"",
        "Power Rating":"",
        "Voltage Rating":"",
        "Current Rating":"",
        "Dielectric":""
    }

    text = str(text).upper()

    match = re.search(r'(\d+(?:\.\d+)?)V', text)
    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    match = re.search(r'(\d+(?:\.\d+)?)W', text)
    if match:
        attributes["Power Rating"] = match.group(1) + "W"

    match = re.search(r'(\d+(?:\.\d+)?)%', text)
    if match:
        attributes["Tolerance"] = match.group(1) + "%"

    for pkg in PACKAGES:

        if pkg in text:
            attributes["Package"] = pkg
            break

    return attributes


def extract_tvs(text):

    attributes = {
        "Value":"",
        "Package":"",
        "Tolerance":"",
        "Power Rating":"",
        "Voltage Rating":"",
        "Current Rating":"",
        "Dielectric":""
    }

    text = str(text).upper()

    match = re.search(r'(\d+)VR', text)

    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    else:

        match = re.search(r'(\d+)V', text)

        if match:
            attributes["Voltage Rating"] = match.group(1) + "V"

    for pkg in PACKAGES:

        if pkg in text:
            attributes["Package"] = pkg
            break

    return attributes

def extract_bridge_rectifier(text):

    attributes = {
        "Value":"",
        "Package":"",
        "Tolerance":"",
        "Power Rating":"",
        "Voltage Rating":"",
        "Current Rating":"",
        "Dielectric":""
    }

    text = str(text).upper()

    match = re.search(r'(\d+)V', text)

    if match:
        attributes["Voltage Rating"] = match.group(1) + "V"

    match = re.search(r'(\d+)A', text)

    if match:
        attributes["Current Rating"] = match.group(1) + "A"

    for pkg in PACKAGES:

        if pkg in text:
            attributes["Package"] = pkg
            break

    return attributes


def extract_mov(text):

    attributes = {
        "Value": "",
        "Package": "",
        "Tolerance": "",
        "Power Rating": "",
        "Voltage Rating": "",
        "Current Rating": "",
        "Dielectric": ""
    }

    text = str(text).upper()

    # AC Voltage
    match = re.search(r'(\d+)VAC', text)
    if match:
        attributes["Voltage Rating"] = match.group(1) + "VAC"
        attributes["Value"] = match.group(1) + "VAC"

    # DC Voltage
    match = re.search(r'(\d+)VDC', text)
    if match:
        attributes["Power Rating"] = match.group(1) + "VDC"

    # Disc Diameter (optional)
    match = re.search(r'D[- ]?(\d+)', text)
    if match:
        attributes["Package"] = "D-" + match.group(1)

    return attributes


def extract_ntc(text):

    attributes = {
        "Value":"",
        "Package":"",
        "Tolerance":"",
        "Power Rating":"",
        "Voltage Rating":"",
        "Current Rating":"",
        "Dielectric":""
    }

    text = str(text).upper()

    match = re.search(r'(\d+)(KOHM|OHM)', text)

    if match:

        if match.group(2) == "KOHM":

            attributes["Value"] = match.group(1) + "K"

        else:

            attributes["Value"] = match.group(1)

    match = re.search(r'(\d+)%', text)

    if match:

        attributes["Tolerance"] = match.group(1) + "%"

    for pkg in PACKAGES:

        if pkg in text:

            attributes["Package"] = pkg
            break

    return attributes



def extract_ic(text):

    attributes = {
        "Value":"",
        "Package":"",
        "Tolerance":"",
        "Power Rating":"",
        "Voltage Rating":"",
        "Current Rating":"",
        "Dielectric":""
    }

    text = str(text).upper()

    tokens = text.split()

    if tokens:

        attributes["Value"] = tokens[0]

    for pkg in PACKAGES:

        if pkg in text:

            attributes["Package"] = pkg
            break

    return attributes


def extract_attributes(row):

    part_type = detect_part_type(row)

    search_text = " ".join([
        str(row.get("Description", "")),
        str(row.get("Comment", "")),
        str(row.get("Footprint", "")),
        str(row.get("LibRef", ""))
    ])

    extractor_map = {
        "Resistor": extract_resistor,
        "Ceramic Capacitor": extract_ceramic_capacitor,
        "Electrolytic Capacitor": extract_electrolytic_capacitor,
        "Inductor": extract_inductor,
        "Diode": extract_diode,
        "Zener": extract_zener,
        "TVS": extract_tvs,
        "Bridge Rectifier": extract_bridge_rectifier,
        "MOV": extract_mov,
        "NTC": extract_ntc,
        "IC": extract_ic,
    }

    if part_type in extractor_map:
        attributes = extractor_map[part_type](search_text)

    else:
        attributes = {
            "Value": "",
            "Package": "",
            "Tolerance": "",
            "Power Rating": "",
            "Voltage Rating": "",
            "Current Rating": "",
            "Dielectric": ""
        }

    attributes["Part Type"] = part_type

    return attributes


def fill_defaults(attributes):

    part = attributes["Part Type"]

    defaults = {

        "Resistor": {
            "Tolerance": "5%",
            "Power Rating": "0.25W"
        },

        "Ceramic Capacitor": {
            "Voltage Rating": "50V",
            "Dielectric": "X7R"
        },

        "Electrolytic Capacitor": {
            "Voltage Rating": "50V"
        },

        "Inductor": {
            "Current Rating": "2A"
        },

        "Diode": {
        },

        "MOV": {
            "Voltage Rating": "300VAC"
        },

        "NTC": {
            "Tolerance": "5%"
        }

    }

    if part in defaults:

        for key, value in defaults[part].items():

            if attributes[key] == "":
                attributes[key] = value

    return attributes


def build_engineering_row(row):

    attributes = extract_attributes(row)

    attributes = fill_defaults(attributes)

    remarks = []

    if attributes["Part Type"] == "Unknown":
        remarks.append("Unknown Component")

    return {

        "Designator": row.get("Designator", ""),
        "Quantity": row.get("Quantity", 1),

        **attributes,

        "Remarks": ", ".join(remarks)

    }



def generate_engineering_bom(df):

    engineering_rows = []

    for _, row in df.iterrows():

        engineering_rows.append(
            build_engineering_row(row)
        )

    engineering_df = pd.DataFrame(engineering_rows)

    columns = [

        "Designator",
        "Quantity",
        "Part Type",
        "Value",
        "Package",
        "Tolerance",
        "Power Rating",
        "Voltage Rating",
        "Current Rating",
        "Dielectric",
        "Remarks"

    ]

    return engineering_df[columns]

