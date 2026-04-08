let map;
let markers = [];

function initMap() {
    console.log("Initialisation de la carte...");
    try {
        const initialPos = { lat: 48.8566, lng: 2.3522 };
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 13,
            center: initialPos,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
        });
    } catch (e) {
        console.error("Erreur Google Maps:", e);
    }

    const input = document.getElementById("addressInput");
    const autocomplete = new google.maps.places.Autocomplete(input, {
        componentRestrictions: { country: "fr" },
        fields: ["geometry", "name"],
        types: ["address"]
    });

    autocomplete.addListener("place_changed", () => {
        searchStations();
    });

    document.getElementById("searchBtn").addEventListener("click", searchStations);
    document.getElementById("addressInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") searchStations();
    });

    displayHistory();
}

function getHistory() {
    return JSON.parse(localStorage.getItem("gas_finder_history") || "[]");
}

function saveToHistory(address) {
    if (!address) return;
    let history = getHistory();
    history = [address, ...history.filter(a => a !== address)].slice(0, 5);
    localStorage.setItem("gas_finder_history", JSON.stringify(history));
    displayHistory();
}

function displayHistory() {
    const historyContainer = document.getElementById("searchHistory");
    const history = getHistory();
    historyContainer.innerHTML = history.length > 0 ? "<span>Historique : </span>" : "";
    history.forEach(address => {
        const chip = document.createElement("span");
        chip.className = "history-chip";
        chip.textContent = address;
        chip.onclick = () => {
            document.getElementById("addressInput").value = address;
            searchStations();
        };
        historyContainer.appendChild(chip);
    });
}

// Fonction améliorée pour trouver la marque via Google Places
function findOfficialBrand(station, service) {
    return new Promise((resolve) => {
        // On construit une requête précise : "Adresse, Ville station service"
        const query = `${station.address}, ${station.city} station service`;
        
        const request = {
            query: query,
            fields: ['name', 'geometry'],
            locationBias: { lat: station.lat, lng: station.lon }
        };

        service.findPlaceFromQuery(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && results && results[0]) {
                // Google nous renvoie souvent le nom exact de l'enseigne
                resolve(results[0].name);
            } else {
                // Si Google ne trouve pas, on utilise la ville par défaut
                resolve(station.city || "Station Service");
            }
        });
    });
}

async function searchStations() {
    const address = document.getElementById("addressInput").value;
    const fuel = document.getElementById("fuelInput").value;
    if (!address) return;

    saveToHistory(address);
    const listContainer = document.getElementById("stationList");
    listContainer.innerHTML = "<p>Recherche des stations et des enseignes...</p>";

    try {
        const url = `/api/stations?address=${encodeURIComponent(address)}` + (fuel ? `&fuel_type=${fuel}` : "");
        const response = await fetch(url);
        const data = await response.json();
        await updateMap(data);
    } catch (error) {
        console.error(error);
        alert("Erreur lors de la recherche.");
    }
}

async function updateMap(data) {
    const { user_location, stations } = data;
    const fuelType = document.getElementById("fuelInput").value || "Gazole";
    const service = new google.maps.places.PlacesService(map);

    const sortedStations = [...stations].sort((a, b) => {
        const priceA = a.prices[fuelType] || 999;
        const priceB = b.prices[fuelType] || 999;
        return priceA - priceB;
    });

    markers.forEach(m => m.setMap(null));
    markers = [];
    const listContainer = document.getElementById("stationList");
    listContainer.innerHTML = "";

    map.setCenter({ lat: user_location.lat, lng: user_location.lon });
    map.setZoom(13);

    new google.maps.Marker({
        position: { lat: user_location.lat, lng: user_location.lon },
        map: map,
        icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
    });

    for (let i = 0; i < sortedStations.length; i++) {
        const station = sortedStations[i];
        const rank = i + 1;
        
        // RECHERCHE DE LA MARQUE OFFICIELLE VIA GOOGLE
        const officialName = await findOfficialBrand(station, service);
        const price = station.prices[fuelType] ? `${station.prices[fuelType].toFixed(3)}€` : "N/A";

        const marker = new google.maps.Marker({
            position: { lat: station.lat, lng: station.lon },
            map: map,
            label: rank.toString(),
            title: officialName
        });

        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div class="info-window">
                    <h3>#${rank} ${officialName}</h3>
                    <p>Prix ${fuelType}: <strong>${price}</strong></p>
                    <p><small>${station.address}</small></p>
                </div>`
        });

        marker.addListener("click", () => infoWindow.open(map, marker));
        markers.push(marker);

        const item = document.createElement("div");
        item.className = "station-item";
        item.innerHTML = `
            <span class="station-rank">${rank}</span>
            <div class="station-info">
                <strong>${officialName}</strong><br>
                <small>${station.address}, ${station.city}</small>
            </div>
            <span class="station-price">${price}</span>
        `;
        item.onclick = () => {
            map.setZoom(17);
            map.panTo({ lat: station.lat, lng: station.lon });
            infoWindow.open(map, marker);
        };
        listContainer.appendChild(item);
    }
}
