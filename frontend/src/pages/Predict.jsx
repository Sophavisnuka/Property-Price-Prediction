import { useState } from "react";
import PredictionForm from "../components/PredictionForm";
import PriceResult from "../components/PriceResult";

export default function Home() {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="flex flex-col gap-8 p-8 max-w-6xl mx-auto">
      <PredictionForm onResult={setResult} onLoading={setLoading} />
      
      {/* Container conditionally rendered to show below form */}
      {(result || loading) && (
        <div className="w-full mt-4">
          <PriceResult result={result} loading={loading} />
        </div>
      )}
    </div>
  );
}