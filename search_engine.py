
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from digikey_api import (
    search_keyword,
    parse_products
)

from validators import score_candidate


# ==========================================
# Search Query Generator
# ==========================================

def create_search_query(row):

    part_type = str(row["Part Type"]).strip()

    value = str(row["Value"]).strip().upper()

    # =====================================================
    # Resistor
    # =====================================================

    if part_type == "Resistor":
        value = str(row["Value"]).strip().upper()

        if value.replace(".", "").isdigit():
            value += "R"

        elif value.endswith(" OHM"):
            value = value.replace(" OHM", "R")

        return (
            f"{value} "
            f"RESISTOR "
            f"{row['Package']} "
            f"{row['Tolerance']} "
            f"{row['Power Rating']}"
        ).strip()

    # =====================================================
    # Ceramic Capacitor
    # =====================================================

    elif part_type == "Ceramic Capacitor":

        return (
            f"{row['Value']} "
            f"{row['Voltage Rating']} "
            f"{row['Dielectric']} "
            f"{row['Package']}"
        ).strip()

    # =====================================================
    # Electrolytic Capacitor
    # =====================================================

    elif part_type == "Electrolytic Capacitor":

        return (
            f"{row['Value']} "
            f"{row['Voltage Rating']} "
            f"ELECTROLYTIC CAPACITOR"
        ).strip()

    # =====================================================
    # Inductor
    # =====================================================

    elif part_type == "Inductor":

        return (
            f"{row['Value']} "
            f"INDUCTOR "
            f"{row['Current Rating']}"
        ).strip()

    # =====================================================
    # Diode
    # =====================================================

    elif part_type == "Diode":

        # Prefer searching by exact part number (MPN)
        if value != "":
            return value

        return (
            f"{row['Voltage Rating']} "
            f"{row['Current Rating']} "
            f"DIODE "
            f"{row['Package']}"
        ).strip()

    # =====================================================
    # Zener
    # =====================================================

    elif part_type == "Zener":

        return (
            f"{row['Voltage Rating']} "
            f"ZENER DIODE "
            f"{row['Power Rating']}"
        ).strip()

    # =====================================================
    # TVS
    # =====================================================

    elif part_type == "TVS":

        return (
            f"{row['Voltage Rating']} "
            f"TVS DIODE "
            f"{row['Package']}"
        ).strip()

    # =====================================================
    # Bridge Rectifier
    # =====================================================

    elif part_type == "Bridge Rectifier":

        return (
            f"{row['Voltage Rating']} "
            f"{row['Current Rating']} "
            f"BRIDGE RECTIFIER"
        ).strip()

    # =====================================================
    # MOV
    # =====================================================

    elif part_type == "MOV":

        return (
            f"{row['Voltage Rating']} "
            f"MOV "
            f"{row['Package']}"
        ).strip()

    # =====================================================
    # NTC
    # =====================================================

    elif part_type == "NTC":

        return (
            f"{row['Value']} "
            f"NTC "
            f"{row['Package']} "
            f"{row['Tolerance']}"
        ).strip()

    # =====================================================
    # IC
    # =====================================================

    elif part_type == "IC":

        return value

    # =====================================================
    # Default
    # =====================================================

    return value


# ==========================================
# Find Best Component
# ==========================================
def find_best_component(row):

    query = create_search_query(row)

    # ---------------- DEBUG ----------------
    print("=" * 80)
    print("ROW:")
    print(row.to_dict())
    print("SEARCH QUERY:", query)
    print("=" * 80)
    # ---------------------------------------

    queries = []

    if query:
        queries.append(query)

    # -------------------------------------------------
    # Resistor fallback
    # -------------------------------------------------
    if row["Part Type"] == "Resistor":

        value = str(row["Value"]).strip().upper()
        package = str(row["Package"]).strip()
        tolerance = str(row["Tolerance"]).strip()
        power = str(row["Power Rating"]).strip()

        # Convert 100 -> 100R
        if value.replace(".", "").isdigit():
            value += "R"

        elif value.endswith(" OHM"):
            value = value.replace(" OHM", "R")

        # Progressive query relaxation

        # Level 3
        queries.append(
            f"{value} RESISTOR {package}"
        )


        # Level 5
        queries.append(value)

    # -------------------------------------------------
    # Search using fallbacks
    # -------------------------------------------------

    best_product = None
    best_score = -1

    for q in queries:

        print("\n" + "="*60)
        print("Searching:", q)

        response = search_keyword(q)

        products = parse_products(response)

        print("Products Returned:", len(products))

        if not products:
            continue

        for product in products:

            print("--------------------------------")
            print("MPN:", product["Manufacturer Part Number"])

            result = score_candidate(row, product)

            print("Score:", result["Score"])
            print("Matched:", result["Matched"])
            print("Mismatched:", result["Mismatched"])

            product["Validation"] = result

            if result["Score"] == 100:

                print(">>>> PERFECT MATCH <<<<")
                return product

            if result["Score"] > best_score:

                best_score = result["Score"]
                best_product = product

        print("Best Score after this query:", best_score)

        if best_score >= 95:

            return best_product

    # No product matched
    if best_product is None:

        return {
            "Manufacturer": "",
            "Manufacturer Part Number": "",
            "DigiKey Part Number": "",
            "Description": "",
            "Unit Price": 0.0,
            "Stock": 0,
            "Product URL": "",
            "Datasheet": "",
            "Search Query": query,
            "Validation": {
                "Matched": [],
                "Mismatched": [],
                "Score": 0,
                "Status": "No Match"
            }
        }

    return best_product

# ==========================================
# Complete BOM Search
# ==========================================

def process_row(row):

    result = find_best_component(row)

    row_dict = row.to_dict()

    if result:

        row_dict["Manufacturer"] = result["Manufacturer"]
        row_dict["Manufacturer Part Number"] = result["Manufacturer Part Number"]
        row_dict["DigiKey Part Number"] = result["DigiKey Part Number"]
        row_dict["Description"] = result["Description"]
        row_dict["Stock"] = result["Stock"]
        row_dict["Unit Price"] = result["Unit Price"]
        row_dict["Product URL"] = result["Product URL"]

        row_dict["Validation Score"] = result["Validation"]["Score"]
        row_dict["Matched"] = ", ".join(result["Validation"]["Matched"])
        row_dict["Mismatched"] = ", ".join(result["Validation"]["Mismatched"])
        row_dict["Status"] = result["Validation"]["Status"]

    else:

        row_dict["Manufacturer"] = ""
        row_dict["Manufacturer Part Number"] = ""
        row_dict["DigiKey Part Number"] = ""
        row_dict["Description"] = ""
        row_dict["Stock"] = ""
        row_dict["Unit Price"] = ""
        row_dict["Product URL"] = ""
        row_dict["Validation Score"] = 0
        row_dict["Matched"] = ""
        row_dict["Mismatched"] = ""
        row_dict["Status"] = "Not Found"

    return row_dict



def search_bom(df, target_cost=0,progress_bar=None, status_text=None,api_callback=None):

    final_rows = []

    total = len(df)

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = {}

        for index, row in df.iterrows():

            future = executor.submit(process_row, row)

            futures[future] = index

        completed = 0

        results = {}

        for future in as_completed(futures):

            index = futures[future]

            results[index] = future.result()

            completed += 1

            if progress_bar:

                progress_bar.progress(completed / total)

            if status_text:

                status_text.text(
                    f"Searched {completed}/{total}"
                )

            # -------------------------
            # Refresh DigiKey panel
            # -------------------------

            if api_callback:

                api_callback()

                
        for i in sorted(results):

            final_rows.append(results[i])

    details_df = pd.DataFrame(final_rows)

    details_df["Total Cost"] = (
        details_df["Quantity"].astype(float) *
        details_df["Unit Price"].astype(float)
    )

    USD_TO_INR = 95.38

    actual_cost = round(
        details_df["Total Cost"].sum() * USD_TO_INR,
        2
    )

    summary_columns = [
        "Designator",
        "Part Type",
        "Value",
        "Manufacturer",
        "Manufacturer Part Number",
        "DigiKey Part Number",
        "Unit Price",
        "Total Cost",
        "Stock",
        "Validation Score"
    ]

    summary_df = details_df[summary_columns].copy()

    # Add Status if available
    if "Status" in details_df.columns:
        summary_df["Status"] = details_df["Status"]

    dashboard = {
    "Total Parts": len(details_df),

    "Found": len(
        details_df[
            details_df["Validation Score"] == 100
        ]
    ),

    "Partially Matched": len(
        details_df[
            (details_df["Validation Score"] > 20) &
            (details_df["Validation Score"] < 100)
        ]
    ),

    "Few Parameters Matched": len(
        details_df[
            (details_df["Validation Score"] > 0) &
            (details_df["Validation Score"] <= 20)
        ]
    ),

    "Not Found": len(
        details_df[
            details_df["Validation Score"] == 0
        ]
    )
    }

    dashboard["Automation"] = round(
        dashboard["Found"] / dashboard["Total Parts"] * 100,
        1
    )

    dashboard["Actual Cost"] = round(actual_cost, 2)

    if target_cost is not None:

        dashboard["Target Cost"] = round(target_cost, 2)

        dashboard["Difference"] = round(
            actual_cost - target_cost,
            2
        )

        dashboard["Difference %"] = round(
            ((actual_cost - target_cost) / target_cost) * 100,
            2
        )

    else:

        dashboard["Target Cost"] = None
        dashboard["Difference"] = None
        dashboard["Difference %"] = None

    return {
        "summary": summary_df,
        "details": details_df,
        "dashboard": dashboard
    }

    