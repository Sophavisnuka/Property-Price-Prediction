import { useEffect, useState } from "react";
import ChartCard from "../components/ChartCard";
import { fetchStats } from "../api/api";

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="w-full">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
          <p className="text-gray-500">Market insights and property analysis</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            Failed to load stats: {error}. Make sure the backend is running.
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <ChartCard
            title="Price Distribution"
            data={stats?.price_distribution ?? []}
            xKey="range"
            yKey="count"
            color="#7c3aed"
          />
          <ChartCard
            title="Average Price by District"
            data={stats?.avg_price_by_district ?? []}
            xKey="location"
            yKey="avg_price"
            color="#6d28d9"
          />
          <ChartCard
            title="Bedrooms vs Average Price"
            data={stats?.avg_price_by_bedrooms ?? []}
            xKey="bedrooms"
            yKey="avg_price"
            color="#8b5cf6"
          />
          <ChartCard
            title="Average Price by Property Type"
            data={stats?.avg_price_by_type ?? []}
            xKey="type"
            yKey="avg_price"
            color="#a78bfa"
          />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;