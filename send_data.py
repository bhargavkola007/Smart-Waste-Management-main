import requests

url = "http://127.0.0.1:5000/update"

data = {
    "bin1": 3.2,
    "bin2": 1.5,
    "bin3": 4.8,
    "gas": 320,
    "level": 12,
    "type": "Dry"
}

response = requests.post(url, json=data)

print(response.text)