import requests

url = "https://api.fragment-api.com/v1/auth/authenticate/"

payload = {
    "api_key": "ce16eb0a-db4e-4597-b3f6-e6a8e901f82d",
    "phone_number": "+14175706252",
    "mnemonics": ["uncle", "bitter", "perfect", "dynamic", "jaguar", "decide", "sister", "grid", "vital", "amateur", "seed", "debate", "alien", "system", "tonight", "sausage", "rent", "idle", "earth", "secret", "swear", "renew", "sweet", "view"]
}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())