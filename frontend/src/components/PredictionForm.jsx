import { useState, useEffect, useRef } from "react";
import { predictPrice } from "../api/api";

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
        style={{ width: "100%", height: "100%", minHeight: 300, borderRadius: 8, overflow: "hidden" }}
        className="border border-gray-300"
      />
      <p className={`text-xs mt-2 ${locLoading ? "text-purple-500" : "text-gray-400"}`}>
        {hint}
      </p>
    </div>
  );
}

const PROPERTY_TYPES = [
  "apartment", "house", "room", "condo",
];

// ← now accepts onResult and onLoading from parent
function PredictionForm({ onResult, onLoading }) {
  const [city,         setCity]         = useState("");
  const [district,     setDistrict]     = useState("");
  const [location,     setLocation]     = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [sizeSqm,      setSizeSqm]      = useState("");
  const [bedrooms,     setBedrooms]     = useState("");
  const [bathrooms,    setBathrooms]    = useState("");
  const [furnishing,   setFurnishing]   = useState("unfurnished");
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

    if (!sizeSqm || !bedrooms || !bathrooms || !propertyType) {
      setError("Please fill in size, bedrooms, bathrooms, and property type (or pin a location on the map).");
      return;
    }

    setLoading(true);
    onLoading(true);      // tell parent loading started
    try {
      const data = await predictPrice({
          size_sqm:      parseFloat(sizeSqm),
          bedrooms:      parseInt(bedrooms),
          bathrooms:     parseInt(bathrooms),
          property_type: propertyType.trim().toLowerCase(),
          furnishing:    furnishing,
        });
      onResult(data);
    } catch (err) {
      setError(err.message || "Prediction failed. Is the backend running?");
    } finally {
      setLoading(false);
      onLoading(false);   // tell parent loading finished
    }
  };

  return (
    <div className="bg-white rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500"></div>

      <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <svg className="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
        Property Parameters
      </h2>

      <form onSubmit={handleSubmit} className="mt-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Side: Map */}
          <div className="flex flex-col">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pin Location on Map
            </label>
            <div className="flex-1 min-h-[300px] h-full relative">
              {/* Ensure LocationMap fills the parent */}
              <div className="absolute inset-0 w-full h-full">
                <LocationMap onSelect={handleMapSelect} />
              </div>
            </div>
          </div>

          {/* Right Side: Form Fields */}
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">City</label>
                <input
                  placeholder="e.g. Phnom Penh"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">District</label>
                <input
                  placeholder="e.g. Chroy Chanva"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
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
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Size (sqm)</label>
                <input
                  type="number"
                  placeholder="e.g. 75"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  value={sizeSqm}
                  onChange={(e) => setSizeSqm(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bedrooms</label>
                <input
                  type="number"
                  placeholder="e.g. 2"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  value={bedrooms}
                  onChange={(e) => setBedrooms(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bathrooms</label>
                <input
                  type="number"
                  placeholder="e.g. 2"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  value={bathrooms}
                  onChange={(e) => setBathrooms(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Furnishing</label>
              <select
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition bg-white"
                value={furnishing}
                onChange={(e) => setFurnishing(e.target.value)}
              >
                <option value="unfurnished">Unfurnished</option>
                <option value="furnished">Furnished</option>
              </select>
            </div>

            {error && (
              <div className="text-red-500 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                ⚠ {error}
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full relative group overflow-hidden bg-slate-900 border border-slate-800 text-white font-semibold py-4 rounded-xl transition-all mt-8 disabled:opacity-70 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(79,70,229,0.3)]"
        >
          <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <span className="relative flex items-center justify-center gap-3">
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing Request...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                Run AI Optimization
              </>
            )}
          </span>
        </button>

      </form>
    </div>
  );
}

export default PredictionForm;