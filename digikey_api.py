import requests
import time
import threading

ACCESS_TOKEN = None
TOKEN_EXPIRY = 0

TOKEN_LOCK = threading.Lock()

# ==============================
# API Statistics
# ==============================

API_STATS = {

    "connected": False,

    "daily_limit": None,

    "daily_remaining": None,

    "session_calls": 0,

    "status": "Idle"

}



SESSION = requests.Session()

REQUEST_LOCK = threading.Lock()
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 0.35   # seconds

CLIENT_ID = "Q3TFn6QmphwVdRVKlxkTWspmetXnUgETdEfUfmck9Ikdtni8"
CLIENT_SECRET = "I0HdgT9Y6MZLXsj7UyuoFYmtRIpiyD7tAtmtWq2hXKUEAuNAp6cm7RssF4dwaBeX"

# ==============================
# Token Cache
# ==============================

def get_access_token():

    global ACCESS_TOKEN
    global TOKEN_EXPIRY

    with TOKEN_LOCK:

        if ACCESS_TOKEN and time.time() < TOKEN_EXPIRY:
            return ACCESS_TOKEN

        url = "https://api.digikey.com/v1/oauth2/token"

        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }


        print(">>> Requesting OAuth token")

        response = SESSION.post(
            url,
            data=payload,
            headers=headers,
            timeout=30
        )
        print(">>> OAuth token received")

        response.raise_for_status()

        token_data = response.json()

        ACCESS_TOKEN = token_data["access_token"]

        TOKEN_EXPIRY = (
            time.time()
            + token_data["expires_in"]
            - 30
        )

        return ACCESS_TOKEN



def search_keyword(keyword):

    API_STATS["status"] = "Connecting"

    access_token = get_access_token()

  

    url = "https://api.digikey.com/products/v4/search/keyword"

    headers = {

        "Authorization": f"Bearer {access_token}",

        "X-DIGIKEY-Client-Id": CLIENT_ID,

        "X-DIGIKEY-Locale-Site": "US",

        "X-DIGIKEY-Locale-Language": "en",

        "X-DIGIKEY-Locale-Currency": "USD",

        "X-DIGIKEY-Locale-ShipToCountry": "US",

        "Content-Type": "application/json"

    }

    payload = {

        "Keywords": keyword,
        "Limit": 10,
        "Offset": 0

    }

    for attempt in range(3):

        try:

            global LAST_REQUEST_TIME

            with REQUEST_LOCK:

                elapsed = time.time() - LAST_REQUEST_TIME

                if elapsed < MIN_REQUEST_INTERVAL:
                    time.sleep(MIN_REQUEST_INTERVAL - elapsed)

                LAST_REQUEST_TIME = time.time()

            response = SESSION.post(

                url,
                json=payload,
                headers=headers,
                timeout=30

            )

            response.raise_for_status()

            API_STATS["connected"] = True


            API_STATS["status"] = "Connected"

            API_STATS["session_calls"] += 1

            # Read rate limit headers (if DigiKey provides them)
            API_STATS["daily_limit"] = response.headers.get(
                "X-RateLimit-Limit"
            )

            API_STATS["daily_remaining"] = response.headers.get(
                "X-RateLimit-Remaining"
            )

            return response.json()

        except requests.exceptions.Timeout:

            print(f"Timeout ({attempt+1}/3): {keyword}")

            time.sleep(1)

        except requests.exceptions.ConnectionError:

            print(f"Connection Error ({attempt+1}/3): {keyword}")

            time.sleep(1)

        except requests.exceptions.HTTPError:

            API_STATS["connected"] = False

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                wait = int(retry_after) if retry_after else (2 ** attempt)

                print(f"429 Rate Limited. Waiting {wait}s")

                time.sleep(wait)

                continue

            print(f"HTTP Error {response.status_code}")

            return {"Products": []}

        except Exception as e:
            API_STATS["connected"] = False

            print(e)

            return {"Products": []}

    return {"Products": []}



def parse_product(product):

    parsed = {}

    parsed["Manufacturer"] = (
        product["Manufacturer"]["Name"]
    )

    parsed["Manufacturer Part Number"] = (
        product["ManufacturerProductNumber"]
    )

    parsed["Description"] = (
        product["Description"]["ProductDescription"]
    )

    parsed["Detailed Description"] = (
        product["Description"]["DetailedDescription"]
    )

    parsed["Unit Price"] = (
        product.get("UnitPrice", "")
    )

    parsed["Stock"] = (
        product.get("QuantityAvailable", "")
    )

    parsed["Product URL"] = (
        product.get("ProductUrl", "")
    )
    # -------------------------
    # Datasheet
    # -------------------------

    parsed["Datasheet"] = product.get(
        "PrimaryDatasheet",
        ""
    )

    # -------------------------
    # DigiKey Part Number
    # -------------------------

    if product["ProductVariations"]:

        parsed["DigiKey Part Number"] = (
            product["ProductVariations"][0][
                "DigiKeyProductNumber"
            ]
        )

    else:

        parsed["DigiKey Part Number"] = ""

    # -------------------------
    # Parameters
    # -------------------------

    # -------------------------
# Parameters
# -------------------------

    parameters = {}

    for parameter in product.get("Parameters", []):

        key = parameter.get("ParameterText", "").strip()
        value = parameter.get("ValueText", "").strip()

        if key:
            parameters[key] = value

    parsed["Parameters"] = parameters

    parsed["Search Score"] = 0

    return parsed

def parse_products(response):

    parsed_products = []

    for product in response["Products"]:

        parsed_products.append(

            parse_product(product)

        )

    return parsed_products


def get_parameter(product, parameter_name):
    return product["Parameters"].get(parameter_name, "")



if __name__ == "__main__":

    print("=" * 70)
    print("DIGIKEY SEARCH TEST")
    print("=" * 70)

    # ---------------------------------------------------
    # Search
    # ---------------------------------------------------

    search_query = "10k resistor 0603"

    print(f"\nSearching for: {search_query}\n")

    response = search_keyword(search_query)

    # ---------------------------------------------------
    # Parse Products
    # ---------------------------------------------------

    products = parse_products(response)

    print(f"\nProducts Parsed : {len(products)}")

    if len(products) == 0:
        print("\nNo Products Found")
        exit()

    # ---------------------------------------------------
    # First Product
    # ---------------------------------------------------

    first = products[0]

    print("\n" + "=" * 70)
    print("FIRST PRODUCT")
    print("=" * 70)

    print(f"Manufacturer              : {first['Manufacturer']}")
    print(f"Manufacturer Part Number  : {first['Manufacturer Part Number']}")
    print(f"DigiKey Part Number       : {first['DigiKey Part Number']}")
    print(f"Description               : {first['Description']}")
    print(f"Price                     : {first['Unit Price']}")
    print(f"Stock                     : {first['Stock']}")

    print("\nProduct Parameters")
    print("-" * 70)

    for key, value in first["Parameters"].items():
        print(f"{key:30} : {value}")

    # ---------------------------------------------------
    # Test get_parameter()
    # ---------------------------------------------------

    print("\n" + "=" * 70)
    print("ATTRIBUTE TEST")
    print("=" * 70)

    print("Resistance :", get_parameter(first, "Resistance"))
    print("Tolerance  :", get_parameter(first, "Tolerance"))
    print("Power      :", get_parameter(first, "Power (Watts)"))
    print("Package    :", get_parameter(first, "Package / Case"))

    print("\nDone.")


def get_api_stats():

    return API_STATS