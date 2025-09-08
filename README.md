### How to make your own:
## Requirements

have python 3.8+
have atleast 4 braincells 

## Usage Guide

### 1. Get the `markers.json` URL

1. go to [Stoneworks Map](https://map.stoneworks.gg/abex1/).
2. Press **F12** on your keyboard
3. navigate to le **Network** tab.
4. Search for **markers**.
5. right click on `markers?(numbers).json` → **Copy** → **Copy URL**.
6. paste that into `main.py` inside the `url = "..."` line.

### 2. Fetch Marker Data

Run:

```
python main.py
```

downloads stuff as `markers.json`.

### 3. Process Marker Data

Run:

```
python mark.py
```
extracts the .json into `markers.txt`.

### 4. Nation Wealth

Run:

```
python nat_wealth.py
```

parses `markers.txt` and outpus nat wealth into `balance.txt`.

### 5. Nation Chunks lmao

Run:

```
python nat_chunks.py
```

parses `markers.txt` and puts it into `chunks.txt`.

