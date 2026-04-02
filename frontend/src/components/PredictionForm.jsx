import { useState, useEffect, useRef } from "react";

const leafletCSS = document.createElement("link");
leafletCSS.rel = "stylesheet";
leafletCSS.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
document.head.appendChild(leafletCSS);

function useLeaflet(onReady) {
    useEffect(() => {
        if (window.L) { onReady(window.L); return; }
        const s = document.createElement("script");
        s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        s.onload = () => onReady(window.L);
        document.head.appendChild(s);
    }, []);
}

async function reverseGeocode(lat, lng) {
    try {
        const r = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
        );
        const d = await r.json();
        const addr = d.address || {};
        return {
            city:     addr.city     || addr.town     || addr.county   || "",
            district: addr.suburb   || addr.quarter  || addr.district || "",
            location: addr.suburb   || addr.quarter  || addr.neighbourhood || addr.village || "",
        };
    } catch {
        return { city: "", district: "", location: "" };
    }
}

function LocationMap({ onSelect }) {
    const mapRef      = useRef(null);
    const instanceRef = useRef(null);
    const markerRef   = useRef(null);
    const [hint, setHint]             = useState("Click on the map to auto-fill location");
    const [locLoading, setLocLoading] = useState(false);

    useLeaflet((L) => {
        if (instanceRef.current) return;
            const map = L.map(mapRef.current, { zoomControl: true })
                        .setView([11.5564, 104.9282], 13);
            instanceRef.current = map;

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors", maxZoom: 19,
        }).addTo(map);

        const icon = L.divIcon({
            className: "",
            html: `<div style="width:26px;height:26px;background:#7c3aed;border:3px solid #fff;
                    border-radius:50% 50% 50% 0;transform:rotate(-45deg);
                    box-shadow:0 2px 8px rgba(0,0,0,.35)"></div>`,
            iconSize: [26, 26], iconAnchor: [13, 26],
        });

    map.on("click", async (e) => {
        const { lat, lng } = e.latlng;
        if (markerRef.current) markerRef.current.remove();
            markerRef.current = L.marker([lat, lng], { icon }).addTo(map);
            setLocLoading(true);
            setHint("Detecting location…");
        const geo = await reverseGeocode(lat, lng);
            setLocLoading(false);
            setHint(geo.city ? `📍 ${geo.district}, ${geo.city}` : "Location pinned");
            onSelect(geo);
        });
    });

  return (
    <div>
      <div
        ref={mapRef}
        style={{ width: "100%", height: 260, borderRadius: 8, overflow: "hidden" }}
        className="border border-gray-300"
      />
      <p className={`text-xs mt-2 ${locLoading ? "text-purple-500" : "text-gray-400"}`}>
        {hint}
      </p>
    </div>
  );
}

const PROPERTY_TYPES = [
  "apartment", "house", "villa", "condo", "shophouse",
  "studio", "room", "office", "land", "townhouse",
  "penthouse", "duplex", "other",
];

// ← now accepts onResult and onLoading from parent
function PredictionForm({ onResult, onLoading }) {
  const [city,         setCity]         = useState("");
  const [district,     setDistrict]     = useState("");
  const [location,     setLocation]     = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState("");

  const handleMapSelect = (geo) => {
    if (geo.city)     setCity(geo.city);
    if (geo.district) setDistrict(geo.district);
    if (geo.location) setLocation(geo.location);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    onResult(null);       // reset result in parent

    if (!city || !district || !location || !propertyType) {
      setError("Please fill in all fields or pin a location on the map.");
      return;
    }

    setLoading(true);
    onLoading(true);      // tell parent loading started
    try {
      const res = await fetch("/api/predict", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city:          city.trim().toLowerCase(),
          district:      district.trim().toLowerCase(),
          location:      location.trim().toLowerCase(),
          property_type: propertyType.trim().toLowerCase(),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      onResult(data);     // send result up to parent → PriceResult will show it
    } catch (err) {
      setError(err.message || "Prediction failed. Is the backend running?");
    } finally {
      setLoading(false);
      onLoading(false);   // tell parent loading finished
    }
  };

  return (
    <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">

      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Property Details
      </h2>

      <form onSubmit={handleSubmit} className="space-y-5">

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pin Location on Map
          </label>
          <LocationMap onSelect={handleMapSelect} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">District</label>
            <input
              placeholder="e.g. phnom penh"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">City</label>
            <input
              placeholder="e.g. toul kork"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location / Area
          </label>
          <input
            placeholder="e.g. boeung kak"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Property Type
          </label>
          <select
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition bg-white"
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
          >
            <option value="">— select type —</option>
            {PROPERTY_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="text-red-500 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            ⚠ {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white font-semibold py-3 rounded-lg transition-all mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Predicting…" : "Predict Price"}
        </button>

      </form>
    </div>
  );
}

export default PredictionForm;