from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://finance.yahoo.com/quote/{}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/152.0.0.0 Safari/537.36 OPR/136.0.0.0"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_soup(ticker):
    """Load the page in a real browser so JavaScript fills in the values."""
    url = BASE_URL.format(ticker.upper())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # browser dekhte paba
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="en-US",
        )
        page = context.new_page()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        section = page.locator("section[data-testid='valuation-measures']")
        section.scroll_into_view_if_needed(timeout=20000)

        try:
            page.wait_for_selector(
                "section[data-testid='valuation-measures'] p.value",
                state="attached",
                timeout=20000,
            )
        except Exception:
            page.screenshot(path="debug.png", full_page=True)
            print("Timeout: debug.png save hoyeche")

        html = page.content()
        browser.close()

    return BeautifulSoup(html, "lxml")


def get_text(element):
    """Safely extract text from an HTML element."""
    return element.get_text(" ", strip=True) if element else None


def get_stock_title(soup):
    element = soup.select_one('h1[data-testid="quote-header"]')

    if not element:
        element = soup.find("h1", class_="heading yf-ndxd9a")

    return get_text(element)


def get_market_prices(soup):
    """Extract regular and overnight market prices."""
    selectors = {
        "regular_market": {
            "price": "qsp-price",
            "change": "qsp-price-change",
            "change_percent": "qsp-price-change-percent",
        },
        "overnight_market": {
            "price": "qsp-overnight-price",
            "change": "qsp-overnight-price-change",
            "change_percent": "qsp-overnight-price-change-percent",
        },
        "pre_market": {
            "price": "qsp-pre-price",
            "change": "qsp-pre-price-change",
            "change_percent": "qsp-pre-price-change-percent",
        },
    }

    market_data = {}

    for market, fields in selectors.items():
        market_data[market] = {}

        for field, test_id in fields.items():
            element = soup.find(
                "span",
                attrs={"data-testid": test_id},
            )
            market_data[market][field] = get_text(element)

    notices = soup.find_all("span", class_=lambda x: x and "marketTimeNotice" in x)
    market_data["notices"] = [get_text(n) for n in notices]

    return market_data


def get_valuation_measures(soup):
    section = soup.find("section", attrs={"data-testid": "valuation-measures"})

    if section is None:
        return None

    date_element = section.find("div", class_=lambda x: x and "asofdate" in x)

    valuation_data = {}

    for item in section.find_all("li"):
        label = item.find(class_=lambda x: x and "label" in x)

        value = item.find(class_=lambda x: x and "value" in x)

        if label and value:
            valuation_data[label.get_text(strip=True)] = value.get_text(strip=True)

    return {
        "as_of_date": (date_element.get_text(strip=True) if date_element else None),
        "metrics": valuation_data,
    }


def get_key_statistics(soup):
    """Extract label/value pairs from the quote statistics list."""
    stats = {}

    for item in soup.find_all("li"):
        label = item.find("span", class_=lambda x: x and x == "label")
        value = item.find("span", class_=lambda x: x and x == "value")

        if label and value:
            name = label.get("title") or label.get_text(strip=True)
            stats[name] = value.get_text(strip=True)

    return stats


def scrape_stock(ticker):
    """Collect all supported stock data."""
    try:
        soup = get_soup(ticker)

        return {
            "ticker": ticker.upper(),
            "title": get_stock_title(soup),
            "market_prices": get_market_prices(soup),
            "valuation_measures": get_valuation_measures(soup),
            "key_statistics": get_key_statistics(soup),
        }

    except Exception as error:
        print(f"Failed to fetch {ticker}: {error}")
        return None


def display_stock_data(data):
    """Display the extracted stock data."""
    if not data:
        return

    print(f"\nStock: {data['title']}")
    print(f"Ticker: {data['ticker']}")

    print("\n--- Regular Market ---")
    for key, value in data["market_prices"]["regular_market"].items():
        print(f"{key}: {value or 'Not found'}")

    print("\n--- Overnight Market ---")
    for key, value in data["market_prices"]["overnight_market"].items():
        print(f"{key}: {value or 'Not found'}")

    print("\n--- Pre-Market ---")
    for key, value in data["market_prices"]["pre_market"].items():
        print(f"{key}: {value or 'Not found'}")

    print("\n--- Market Time Notices ---")
    for notice in data["market_prices"]["notices"]:
        print(notice)

    print("\n--- Valuation Measures ---")
    valuation = data["valuation_measures"]

    if valuation:
        print("Date:", valuation["as_of_date"] or "Not found")

        for key, value in valuation["metrics"].items():
            print(f"{key}: {value}")
    else:
        print("Valuation Measures section not found.")

    print("\n--- Key Statistics ---")
    for key, value in data["key_statistics"].items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    stock_data = scrape_stock("GOOGL")
    display_stock_data(stock_data)
