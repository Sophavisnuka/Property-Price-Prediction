import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200">
            <div className="flex justify-between items-center max-w-7xl mx-auto px-6 py-4">
                <Link to="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-purple-400 rounded-lg"></div>
                    <span className="font-bold text-lg text-gray-900">PPP</span>
                </Link>
                <div className="flex items-center gap-8">
                    <Link to="/" className="text-gray-700 hover:text-gray-900 font-medium transition-colors">Home</Link>
                    <Link to="/predict" className="text-gray-700 hover:text-gray-900 font-medium transition-colors">Predict</Link>
                    <Link to="/dashboard" className="text-gray-700 hover:text-gray-900 font-medium transition-colors">Analytics</Link>
                    <Link to="/about" className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2 rounded-lg font-medium transition-colors">
                        About Us
                    </Link>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;