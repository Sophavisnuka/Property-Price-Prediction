function PriceResult({ result, loading }) {

  const fmt = (v) =>
    "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });

  return (
    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-8 border border-purple-200 flex items-center justify-center min-h-[300px]">

      {/* Loading spinner */}
      {loading && (
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-purple-300 border-t-purple-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-purple-500 text-sm font-medium">Predicting…</p>
        </div>
      )}

      {/* Empty state — before any prediction */}
      {!loading && !result && (
        <div className="text-center">
          <p className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wide">
            Estimated Price
          </p>
          <h2 className="text-6xl font-bold bg-gradient-to-r from-purple-300 to-purple-200 bg-clip-text text-transparent mb-3">
            —
          </h2>
          <p className="text-gray-400 text-sm">
            Fill in the form and click Predict Price
          </p>
        </div>
      )}

      {/* Real result from model */}
      {!loading && result && (
        <div className="text-center w-full">
          <p className="text-sm font-semibold text-purple-600 mb-2 uppercase tracking-wide">
            Estimated Monthly Rent
          </p>
          <h2 className="text-6xl font-bold bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent mb-3">
            {fmt(result.predicted_price)}
          </h2>
          <p className="text-gray-500 text-sm mb-5">
            Range: {fmt(result.price_range_low)} — {fmt(result.price_range_high)}
          </p>
          <div className="flex items-center justify-center gap-2 pt-4 border-t border-purple-200">
            <span className="text-xs bg-purple-100 text-purple-600 px-3 py-1 rounded-full font-medium">
              {result.model_used}
            </span>
            <span className="text-xs text-gray-400">
              Estimated ±10% · For reference only
            </span>
          </div>
        </div>
      )}

    </div>
  );
}

export default PriceResult;