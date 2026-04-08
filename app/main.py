from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from app.data_fetcher import get_coordinates, fetch_nearest_stations
import uvicorn

app = FastAPI(title="Gas Finder API")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/api/stations")
async def get_stations(address: str, fuel_type: str = None):
    """API endpoint to get the nearest gas stations for a given address."""
    if not address:
        raise HTTPException(status_code=400, detail="Address is required")
    
    # 1. Geocode the address
    lat, lon = await get_coordinates(address)
    if lat is None or lon is None:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # 2. Fetch nearest stations with optional fuel filtering
    stations = await fetch_nearest_stations(lat, lon, fuel_type=fuel_type)
    
    return {
        "user_location": {"lat": lat, "lon": lon},
        "stations": stations
    }

@app.get("/")
async def root():
    """Redirect to the frontend index.html."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
