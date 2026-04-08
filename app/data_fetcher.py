import os
import httpx
import math
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

async def get_coordinates(address: str):
    """Convert address to GPS coordinates using Google Geocoding API."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = response.json()
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
        except Exception as e:
            print(f"Error during geocoding: {e}")
    return None, None

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points in km."""
    R = 6371  # Earth radius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def guess_brand(station_data):
    """Guess the brand name from the address or services if possible."""
    common_brands = [
        "TotalEnergies", "Total", "Shell", "BP", "Esso", "Avia", "Eni", "Agip",
        "E.Leclerc", "Leclerc", "Carrefour", "Intermarché", "Intermarche", "Super U", "Hyper U", "Système U",
        "Auchan", "Casino", "Cora", "Netto", "Géant", "Geant", "Elan"
    ]
    
    text_to_search = (station_data.get("adresse", "") + " " + station_data.get("ville", "")).lower()
    
    # Check services as well
    services = station_data.get("services_service", [])
    if isinstance(services, list):
        text_to_search += " " + " ".join(services).lower()
    
    for brand in common_brands:
        if brand.lower() in text_to_search:
            return brand
            
    return None

import time

# Cache global pour stocker les données et éviter de télécharger 10Mo à chaque clic
_cache = {
    "data": None,
    "last_updated": 0
}

CACHE_EXPIRATION = 1800  # 30 minutes

async def fetch_nearest_stations(lat: float, lon: float, fuel_type: str = None, limit: int = 5):
    """Fetch nearest stations with caching to avoid heavy downloads on each request."""
    global _cache
    resource_url = "https://www.data.gouv.fr/fr/datasets/r/b0561905-7b5e-4f38-be50-df05708acb80"
    
    current_time = time.time()
    
    # Si le cache est vide ou expiré, on télécharge
    if _cache["data"] is None or (current_time - _cache["last_updated"] > CACHE_EXPIRATION):
        print("Mise à jour du cache des prix (téléchargement)...")
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            try:
                response = await client.get(resource_url)
                if response.status_code == 200:
                    _cache["data"] = response.json()
                    _cache["last_updated"] = current_time
                    print("Cache mis à jour avec succès.")
            except Exception as e:
                print(f"Erreur de téléchargement du flux: {e}")
                if _cache["data"] is None: return [] # Si on n'a rien du tout, on s'arrête

    all_stations = _cache["data"]
    
    fuel_map = {
        "Gazole": "gazole_prix",
        "SP95": "sp95_prix",
        "SP98": "sp98_prix",
        "E10": "e10_prix"
    }

    processed_stations = []
    for s in all_stations:
        if not s.get("geom") or s["geom"].get("lat") is None:
            continue
            
        s_lat = s["geom"]["lat"]
        s_lon = s["geom"]["lon"]
        
        dist = haversine(lat, lon, s_lat, s_lon)
        if dist > 50: continue # Rayon de 50km max
            
        if fuel_type and fuel_type in fuel_map:
            price = s.get(fuel_map[fuel_type])
            if price is None or price <= 0:
                continue

        brand = guess_brand(s)
        processed_stations.append({
            "name": f"{brand if brand else s.get('ville', 'Station')}",
            "brand": brand or "Inconnu",
            "address": s.get("adresse", ""),
            "city": s.get("ville", ""),
            "lat": s_lat,
            "lon": s_lon,
            "distance": dist,
            "prices": {
                "Gazole": s.get("gazole_prix"),
                "SP95": s.get("sp95_prix"),
                "SP98": s.get("sp98_prix"),
                "E10": s.get("e10_prix"),
            }
        })

    processed_stations.sort(key=lambda x: x["distance"])
    return processed_stations[:limit]
