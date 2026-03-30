import ChartCard from "../components/ChartCard";

function Dashboard() {

  return (
    <div className="max-w-6xl mx-auto mt-10 grid grid-cols-2 gap-6">

      <ChartCard title="Price Distribution" />
      <ChartCard title="Average Price by Location" />
      <ChartCard title="Bedrooms vs Price" />
      <ChartCard title="Correlation Heatmap" />

    </div>
  );
}

export default Dashboard;