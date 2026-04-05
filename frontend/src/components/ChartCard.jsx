import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

function ChartCard({ title, data = [], xKey, yKey, color = "#7c3aed" }) {

  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">

      <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>

      {data.length === 0 ? (
        <div className="h-64 flex items-center justify-center rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 text-gray-400">
          Loading data…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 11 }}
              angle={-35}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickFormatter={(v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`}
              width={48}
            />
            <Tooltip
              formatter={(v) => [`$${Number(v).toLocaleString()}`, title]}
              labelStyle={{ color: "#374151" }}
            />
            <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}

    </div>
  );
}

export default ChartCard;