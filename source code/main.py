import requests
import json

url = "https://map.stoneworks.gg/abex1/maps/abexilas/live/markers.json?308516"

response = requests.get(url)

if response.status_code == 200:
    data = response.json() 

    with open("markers.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Markers data saved successfully!")
else:
    print(f"Failed to fetch data. Status Code: {response.status_code}")
