function PriceResult() {

  return (
    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-8 border border-purple-200 flex items-center justify-center min-h-[300px]">

      <div className="text-center">

        <p className="text-sm font-semibold text-purple-600 mb-2 uppercase tracking-wide">
          Estimated Price
        </p>

        <h2 className="text-6xl font-bold bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent mb-2">
          $82,000
        </h2>

        <p className="text-gray-600">Based on current market analysis</p>

      </div>

    </div>
  );
}

export default PriceResult;