import ChartCard from "../components/ChartCard";

function Dashboard() {

  return (
    <div className="w-full">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
          <p className="text-gray-500">Market insights and property analysis</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <ChartCard title="Price Distribution" />
          <ChartCard title="Average Price by Location" />
          <ChartCard title="Bedrooms vs Price" />
          <ChartCard title="Correlation Heatmap" />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;