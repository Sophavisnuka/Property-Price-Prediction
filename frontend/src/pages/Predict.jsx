import PredictionForm from "../components/PredictionForm";
import PriceResult from "../components/PriceResult";

function Predict() {
    return (
        <div className="max-w-5xl mx-auto grid grid-cols-2 gap-6  mb-20">
            <PredictionForm />
            <PriceResult />
        </div>
    );
}

export default Predict;