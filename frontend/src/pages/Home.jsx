import { Link } from "react-router-dom";

function Home() {
    return (
        <div className="w-full flex items-center justify-center">
            <div className="w-full max-w-6xl px-6 py-20">
                <div className="grid md:grid-cols-2 gap-12 items-center">
                    <div className="space-y-6">
                        <div className="space-y-3">
                            <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
                                Smart Property
                                <span className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent"> Pricing</span>
                            </h1>
                        </div>
                        <p className="text-lg text-gray-500 leading-relaxed">
                            Leverage AI-powered machine learning to accurately predict property prices based on location, features, and market trends.
                        </p>
                        <div className="flex gap-4 pt-6">
                            <Link
                                to="/predict"
                                className="px-8 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                            >
                                Start Predicting
                            </Link>
                            <Link
                                to="/dashboard"
                                className="px-8 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:border-gray-400 hover:bg-gray-50 transition-colors"
                            >
                                View Analytics
                            </Link>
                        </div>
                    </div>

                    <div className="relative hidden md:block">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-200 to-purple-100 rounded-3xl blur-3xl opacity-40"></div>
                        <div className="relative bg-white rounded-3xl p-8 shadow-lg">
                            <div className="space-y-4">
                                <div className="h-3 bg-gradient-to-r from-purple-600 to-purple-400 rounded-full w-24"></div>
                                <div className="h-32 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl"></div>
                                <div className="space-y-2">
                                    <div className="h-2 bg-gray-200 rounded-full w-3/4"></div>
                                    <div className="h-2 bg-gray-200 rounded-full w-1/2"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid md:grid-cols-3 gap-6 mt-20">
                    {[
                        {
                            title: "Accurate Predictions",
                            description: "Advanced ML algorithms for precise price estimation"
                        },
                        {
                            title: "Real-time Analysis",
                            description: "Instant market insights and trend analysis"
                        },
                        {
                            title: "Data-Driven",
                            description: "Based on comprehensive property and location data"
                        }
                    ].map((feature, i) => (
                        <div key={i} className="p-6 bg-gray-50 rounded-2xl border border-gray-100 hover:border-purple-200 transition-colors">
                            <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                            <p className="text-sm text-gray-600">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default Home;