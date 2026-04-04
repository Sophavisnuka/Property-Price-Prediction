import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";

function PriceResult({ result, loading }) {
  const fmt = (v) =>
    "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });

  // Force it to use the backend payload instead of fallbacks
  const averageMarketPrice = result?.average_market_price || 0;
  
  // Calculate percentage difference vs. average area market price
  const diffRaw = result && averageMarketPrice > 0 ? ((result.predicted_price - averageMarketPrice) / averageMarketPrice) * 100 : 0;
  const isHigher = diffRaw > 0;
  const percentageDiff = Math.abs(diffRaw).toFixed(1);

  // Directly map the new backend response arrays
  const featureImportanceData = result?.feature_importances || [];
  const locationData = result?.location_data || [];
  const sizeCorrelationData = result?.size_correlation_data || [];

  return (
    <div className="relative bg-slate-900 rounded-3xl p-5 border border-indigo-500/30 shadow-[0_0_30px_rgba(79,70,229,0.1)] flex flex-col min-h-[380px] overflow-hidden text-white">
      {/* Decorative background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/10 rounded-full blur-[80px] pointer-events-none"></div>

      {/* Loading state */}
      {loading && (
        <div className="flex-1 flex flex-col items-center justify-center z-10 py-6">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-t-2 border-indigo-400 animate-spin duration-1000"></div>
            <div className="absolute inset-2 rounded-full border-r-2 border-purple-400 animate-spin duration-700"></div>
            <div className="absolute inset-4 rounded-full border-b-2 border-pink-400 animate-spin duration-500"></div>
          </div>
          <h3 className="text-lg font-semibold bg-gradient-to-r from-indigo-300 to-purple-300 bg-clip-text text-transparent animate-pulse mb-1">
            Loading Model Intel...
          </h3>
          <p className="text-indigo-200/60 text-xs">
            Calculating prediction and querying feature importance
          </p>
        </div>
      )}

      {/* Empty state  */}
      {!loading && !result && (
        <div className="flex-1 flex flex-col items-center justify-center z-10 py-6">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-slate-800/80 border border-slate-700 shadow-inner flex items-center justify-center">
            <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <p className="text-xs font-bold text-indigo-400 mb-1 uppercase tracking-widest">
            AI Prediction Engine
          </p>
          <h2 className="text-2xl font-semibold text-slate-500 mb-2">
            Awaiting Input
          </h2>
          <p className="text-slate-400 text-xs max-w-[200px] mx-auto text-center">
            Provide property parameters to activate the neural network and forecast market rent.
          </p>
        </div>
      )}

      {/* Result Display */}
      {!loading && result && (
        <div className="z-10 w-full animate-fade-in flex flex-col h-full gap-4">
          
          {/* Header Section: Price & Confidence Range */}
          <div className="text-center md:text-left flex flex-col md:flex-row items-center justify-between border-b border-indigo-500/20 pb-3 gap-4 md:gap-0">
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1 tracking-wide uppercase">
                Predicted Monthly Rent
              </p>
              <div className="flex items-baseline gap-2 justify-center md:justify-start">
                <h2 className="text-4xl font-extrabold bg-gradient-to-r from-cyan-300 via-indigo-300 to-purple-300 bg-clip-text text-transparent drop-shadow-sm">
                  {fmt(result.predicted_price)}
                </h2>
                <span className="text-lg text-slate-500 font-medium">/ mo</span>
              </div>
            </div>
            
            <div className="bg-white/5 p-3 rounded-xl border border-white/10 backdrop-blur-md w-full md:w-auto text-center">
              <p className="text-[10px] text-slate-400 tracking-wider uppercase mb-1">
                Expected Range <span className="lowercase text-slate-500">(±10%)</span>
              </p>
              <div className="flex items-center justify-center gap-2">
                <span className="font-semibold text-indigo-300 text-lg">{fmt(result.price_range_low)}</span>
                <span className="text-slate-500">-</span>
                <span className="font-semibold text-purple-300 text-lg">{fmt(result.price_range_high)}</span>
              </div>
            </div>
          </div>

          {/* Analysis & Explanations (Dense Grid) */}
          <div className="grid grid-cols-1 xl:grid-cols-2 xl:grid-rows-2 gap-4 h-full">
            
            {/* Market Comparison & Explanation */}
            <div className="bg-indigo-500/10 border border-indigo-500/30 p-4 rounded-xl flex flex-col justify-center">
              <h4 className="text-indigo-300 font-semibold mb-1 text-sm flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                Market Insight
              </h4>
              <p className="text-slate-300 text-xs leading-relaxed mb-2">
                Based on machine learning insights, this prediction is about <strong className={`text-white px-1 py-0.5 rounded ${isHigher ? 'bg-red-500/30' : 'bg-green-500/30'}`}>
                  {percentageDiff}% {isHigher ? 'higher' : 'lower'}
                </strong> than the baseline ({fmt(averageMarketPrice)}).
              </p>
              <p className="text-slate-400 text-[11px] leading-snug">
                <span className="text-slate-300 font-medium">Model Evaluation:</span> The influential variables determining this footprint belong to the features outlined below based directly on the Random Forest node weights.
              </p>
            </div>

            {/* Data-driven Feature Importance (Tailwind Progress Bars) */}
            <div className="bg-slate-800/50 border border-white/10 p-4 rounded-xl flex flex-col justify-center">
              <h4 className="text-slate-200 font-semibold mb-2 text-xs uppercase tracking-wide">
                Top Pricing Characteristics
              </h4>
              <div className="flex flex-col gap-2">
                {featureImportanceData.slice(0, 4).map((item, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-[10px] text-slate-400 mb-0.5">
                      <span className="font-mono truncate pr-2" title={item.feature}>{item.feature}</span>
                      <span className="shrink-0">{item.waitWeight}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-1 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full rounded-full"
                        style={{ width: `${item.waitWeight}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Dynamic Price vs Size - Line Chart */}
            <div className="bg-slate-800/50 border border-white/10 p-3 rounded-xl h-[150px] flex flex-col">
              <h4 className="text-slate-200 font-medium mb-1 text-[11px] uppercase tracking-wide text-center">
                Predicted Rent vs Size
              </h4>
              <div className="flex-1 w-full h-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sizeCorrelationData} margin={{ top: 5, right: 10, left: -25, bottom: -5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="size" tick={{ fill: '#94a3b8', fontSize: 9 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '6px', color: '#f8fafc', fontSize: '10px' }}
                      formatter={(value) => [`$${value}`, "Expected Price"]}
                      labelFormatter={(label) => `${label} Sqm`}
                    />
                    <Line type="monotone" dataKey="price" stroke="#c084fc" strokeWidth={2} dot={{ fill: '#c084fc', strokeWidth: 1, r: 3 }} activeDot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Avg Price By Location - Bar Chart */}
            <div className="bg-slate-800/50 border border-white/10 p-3 rounded-xl h-[150px] flex flex-col">
              <h4 className="text-slate-200 font-medium mb-1 text-[11px] uppercase tracking-wide text-center">
                Top Sample Regions
              </h4>
              <div className="flex-1 w-full h-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={locationData} margin={{ top: 5, right: 10, left: -25, bottom: -5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="location" tick={{ fill: '#94a3b8', fontSize: 9 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '6px', color: '#f8fafc', fontSize: '10px' }}
                      itemStyle={{ color: '#818cf8' }}
                      formatter={(value) => [`$${value}`, "Average Price"]}
                    />
                    <Bar dataKey="price" fill="#6366f1" radius={[3, 3, 0, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

export default PriceResult;