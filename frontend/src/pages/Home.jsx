import { Link } from "react-router-dom";

function Home() {
    return (
        <div className="flex items-center justify-center">
            <div className="h-full max-w-7xl mx-auto text-center mb-20">
                <h1 className="text-4xl font-bold mb-6">
                    Property Price Prediction
                </h1>
                <p className="text-gray-600 mb-8">
                    Predict property prices using machine learning based on
                    location and property features.
                </p>
                <Link
                    to="/predict"
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg"
                    >
                    Start Prediction
                </Link>
            </div>
        </div>
    );
}

export default Home;