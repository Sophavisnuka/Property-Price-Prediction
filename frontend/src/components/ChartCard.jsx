function ChartCard({ title }) {

  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">

      <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>

      <div className="h-64 flex items-center justify-center rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 text-gray-400">
        📊 Chart will go here
      </div>

    </div>
  );
}

export default ChartCard;