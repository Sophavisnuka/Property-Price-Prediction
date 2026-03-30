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
        <div className="bg-white shadow-md rounded-xl p-6">

            <h2 className="text-xl font-semibold mb-4">
                Property Details
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">

                <input
                    placeholder="Location"
                    className="w-full border p-2 rounded"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                />

                <input
                    type="number"
                    placeholder="Bedrooms"
                    className="w-full border p-2 rounded"
                    value={bedrooms}
                    onChange={(e) => setBedrooms(e.target.value)}
                />

                <input
                    type="number"
                    placeholder="Bathrooms"
                    className="w-full border p-2 rounded"
                    value={bathrooms}
                    onChange={(e) => setBathrooms(e.target.value)}
                />

                <input
                    type="number"
                    placeholder="Size (m²)"
                    className="w-full border p-2 rounded"
                    value={size}
                    onChange={(e) => setSize(e.target.value)}
                />

                <button
                    className="w-full bg-blue-600 text-white py-2 rounded"
                >
                    Predict Price
                </button>

            </form>
        </div>
    );
}

export default PredictionForm;