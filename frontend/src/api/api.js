const BASE_URL = "/api";

export async function predictPrice({
  size_sqm,
  bedrooms,
  bathrooms,
  property_type,
  city,
  district,
  location,
}) {
  const res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      size_sqm,
      bedrooms,
      bathrooms,
      property_type,
      city,
      district,
      location,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    const detail = Array.isArray(err.detail)
      ? err.detail.map((e) => `${e.loc.slice(-1)}: ${e.msg}`).join(", ")
      : err.detail;
    throw new Error(detail || `Server error ${res.status}`);
  }

  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${BASE_URL}/stats`);
  if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`);
  return res.json();
}
