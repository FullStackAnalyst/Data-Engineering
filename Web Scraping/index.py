import requests
from bs4 import BeautifulSoup

url = "https://finance.yahoo.com/quote/GOOGL"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/152.0.0.0 Safari/537.36 OPR/136.0.0.0"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

response = requests.get(url, headers=headers, timeout=10)
print(response.status_code)
print(response.content)

if response.ok:
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.title.text)
else:
    print("Blocked:", response.status_code)
