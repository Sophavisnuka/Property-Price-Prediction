function ChartCard({ title }) {

  return (
    <div className="bg-white shadow-md rounded-xl p-6">

      <h2 className="font-semibold mb-4">{title}</h2>

      <div className="h-60 flex items-center justify-center text-gray-400">
        Chart will go here
      </div>

    </div>
  );
}

export default ChartCard;