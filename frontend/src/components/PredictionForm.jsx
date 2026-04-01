import { useState } from "react";

function PredictionForm() {

    const [bedrooms, setBedrooms] = useState(3);
    const [bathrooms, setBathrooms] = useState(2);
    const [size, setSize] = useState(120);
    const [location, setLocation] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();

        console.log({
            location,
            bedrooms,
            bathrooms,
            size
        });

        // later connect API
    };

    return (
        <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">

            <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Property Details
            </h2>

            <form onSubmit={handleSubmit} className="space-y-5">

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                    <input
                        placeholder="Enter property location"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Bedrooms</label>
                        <input
                            type="number"
                            placeholder="0"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                            value={bedrooms}
                            onChange={(e) => setBedrooms(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Bathrooms</label>
                        <input
                            type="number"
                            placeholder="0"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                            value={bathrooms}
                            onChange={(e) => setBathrooms(e.target.value)}
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Size (m²)</label>
                    <input
                        type="number"
                        placeholder="120"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                        value={size}
                        onChange={(e) => setSize(e.target.value)}
                    />
                </div>

                <button
                    className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white font-semibold py-3 rounded-lg transition-all mt-6"
                >
                    Predict Price
                </button>

            </form>
        </div>
    );
}

export default PredictionForm;