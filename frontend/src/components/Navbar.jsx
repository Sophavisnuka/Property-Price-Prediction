import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav>
            <div className="flex justify-between items-center max-w-7xl mx-auto py-4">
                <h1 className="font-semibold text-lg">PPP</h1>
                <div className="space-x-10">
                    <Link to="/">Home</Link>
                    <Link to="/predict">Predict</Link>
                    <Link to="/dashboard">Analytic</Link>
                    <button className="bg-blue-600 text-white px-6 py-3 rounded-lg">
                        English
                    </button>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;