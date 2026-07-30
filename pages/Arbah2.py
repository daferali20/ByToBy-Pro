import requests

API_KEY = "bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ"

# جرب مع Benzinga (الأكثر شيوعاً)
url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
params = {"token": API_KEY, "date_from": "2026-07-01", "date_to": "2026-07-30"}

response = requests.get(url, params=params)
print(f"الحالة: {response.status_code}")
print(f"البيانات: {response.text[:200]}")
