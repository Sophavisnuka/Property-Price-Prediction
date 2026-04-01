import PredictionForm from "../components/PredictionForm";
import PriceResult from "../components/PriceResult";

function Predict() {
    return (
        <div className="w-full">
            <div className="max-w-6xl mx-auto px-6 py-12">
                <div className="mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">Price Prediction</h1>
                    <p className="text-gray-500">Enter property details to get an accurate price estimate</p>
                </div>
                <div className="grid md:grid-cols-2 gap-8">
                    <PredictionForm />
                    <PriceResult />
                </div>
            </div>
        </div>
    );
}

export default Predict;