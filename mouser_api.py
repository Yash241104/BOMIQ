import requests
import pandas as pd

API_KEY = "31fee1d2-78a9-46cf-8f5c-d1fd3d08b917"

SEARCH_CACHE = {}


# =====================================================
# Mouser Search
# =====================================================

def search_keyword(keyword):

    keyword = str(keyword).strip()

    if keyword in SEARCH_CACHE:
        return SEARCH_CACHE[keyword]

    url = (
        f"https://api.mouser.com/api/v2/"
        f"search/keyword?apiKey={API_KEY}"
    )

    payload = {
        "SearchByKeywordRequest": {
            "keyword": keyword,
            "records": 20,
            "startingRecord": 0,
            "searchOptions": "None"
        }
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20
        )

        data = response.json()

        import json

        print("=" * 80)
        print("FIRST MOUSER PRODUCT")
        print("=" * 80)

        if data.get("SearchResults") and data["SearchResults"].get("Parts"):
            print(json.dumps(data["SearchResults"]["Parts"][0], indent=2))
        else:
            print(data)

        if not data.get("SearchResults"):
            SEARCH_CACHE[keyword] = []
            return []

        parts = data["SearchResults"]["Parts"]

        candidates = []

        for part in parts:

            price = ""

            if part.get("PriceBreaks"):
                price = part["PriceBreaks"][0]["Price"]

            candidate = {

                "Manufacturer":
                    part.get("Manufacturer", ""),

                "Manufacturer Part Number":
                    part.get(
                        "ManufacturerPartNumber",
                        ""
                    ),

                "Mouser Part Number":
                    part.get(
                        "MouserPartNumber",
                        ""
                    ),

                "Description":
                    part.get(
                        "Description",
                        ""
                    ),

                "Stock":
                    part.get(
                        "AvailabilityInStock",
                        ""
                    ),

                "Unit Price":
                    price,

                "Product URL":
                    part.get(
                        "ProductDetailUrl",
                        ""
                    )
            }

            candidates.append(candidate)

        SEARCH_CACHE[keyword] = candidates

        return candidates

    except Exception as e:

        print("ERROR:", e)

        SEARCH_CACHE[keyword] = []

        return []
    


# =====================================================
# Test
# =====================================================

if __name__ == "__main__":

    import json

    print("=" * 80)
    print("MOUSER API TEST")
    print("=" * 80)

    query = "RC1206FR-0710KL"

    print(f"\nSearching: {query}\n")

    response = search_keyword(query)

    print("\n" + "=" * 80)
    print("RAW RESPONSE")
    print("=" * 80)

    print(json.dumps(response, indent=4))