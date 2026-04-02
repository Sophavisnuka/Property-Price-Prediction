import { useState } from "react";
import PredictionForm from "../components/PredictionForm";
import PriceResult from "../components/PriceResult";

export default function Home() {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="grid grid-cols-2 gap-8 p-8">
      <PredictionForm onResult={setResult} onLoading={setLoading} />
      <PriceResult result={result} loading={loading} />
    </div>
  );
}