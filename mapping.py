import pandas as pd



COLUMN_MAPPING = {

    "Designator": [
        "Designator",
        "Reference",
        "Ref",
        "RefDes",
        "Component",
        "Ref Designator"
    ],

    "Description": [
        "Description",
        "DESCRIPTION",
        "Part Description",
        "Component Description",
        "Desc"
    ],

    "Comment": [
        "Comment",
        "Value",
        "=Value",
        "Component Value"
    ],

    "Footprint": [
        "Footprint",
        "Package",
        "PCB Footprint",
        "Land Pattern",
        "Pattern"
    ],

    "Quantity": [
        "Quantity",
        "Qty",
        "QTY"
    ],

    "Manufacturer": [
        "Manufacturer",
        "Mfr"
    ],

    "Manufacturer Part Number": [
        "Manufacturer Part Number",
        "MPN",
        "Part Number",
        "Mfr Part Number"
    ]

}


def find_column(df, standard_name):

    aliases = [
        alias.strip().lower()
        for alias in COLUMN_MAPPING[standard_name]
    ]

    for column in df.columns:

        if str(column).strip().lower() in aliases:
            return column

    return None

def standardize_bom(df):

    mapped = {}

    for standard_name in COLUMN_MAPPING:

        column = find_column(df, standard_name)

        if column is not None:

            mapped[standard_name] = df[column]

        else:

            mapped[standard_name] = [""] * len(df)

    return pd.DataFrame(mapped)


