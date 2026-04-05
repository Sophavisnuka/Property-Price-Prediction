function Section({ label, children }) {
  return (
    <div className="border-t border-gray-100 pt-12">
      <p className="text-xs font-semibold uppercase tracking-widest text-purple-500 mb-4">{label}</p>
      {children}
    </div>
  );
}

function getInitials(name) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join("");
}

const AVATAR_COLORS = [
  "from-purple-600 to-indigo-500",
  "from-violet-600 to-purple-500",
  "from-indigo-600 to-blue-500",
  "from-purple-700 to-violet-500",
  "from-fuchsia-600 to-purple-500",
];

function TeamMember({ name, role, contributions, colorIndex = 0 }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow flex items-start gap-4">
      <div className={`shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br ${AVATAR_COLORS[colorIndex % AVATAR_COLORS.length]} flex items-center justify-center shadow-sm`}>
        <span className="text-white font-bold text-sm tracking-wide">{getInitials(name)}</span>
      </div>
      <div className="min-w-0">
        <h3 className="font-semibold text-gray-900 text-sm">{name}</h3>
        <p className="text-purple-600 text-xs font-semibold uppercase tracking-wide mt-0.5 mb-2">{role}</p>
        <ul className="space-y-1">
          {contributions.map((c, i) => (
            <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
              <span className="mt-1.5 w-1 h-1 rounded-full bg-purple-200 shrink-0" />
              {c}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="text-center">
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

const TEAM = [
  {
    name: "Lon Mengheng",
    role: "Data Collection & Scraping",
    contributions: [
      "Web scraping pipeline with Scrapy",
      "Raw data collection from Khmer24",
      "Multi-district data aggregation",
    ],
  },
  {
    name: "Long Chhunhour",
    role: "Data Cleaning & Frontend",
    contributions: [
      "Data preprocessing and cleaning",
      "Exploratory data analysis",
      "Dashboard charts and analytics",
    ],
  },
  {
    name: "Vy Vicheka",
    role: "Machine Learning",
    contributions: [
      "Hyperparameter tuning",
      "Model evaluation and comparison",
    ],
  },
  {
    name: "Khun Sophavisnuka",
    role: "Fullstack Development",
    contributions: [
      "Model selection and training",
      "Prediction endpoint integration",
      "React UI components",
      "Interactive prediction form",
    ],
  },
  {
    name: "May Kunaphivath",
    role: "EDA ",
    contributions: [
      "Data preprocessing and cleaning",
      "Model evaluation and comparison",
      "Web scraping pipeline with Scrapy",
    ],
  },
];

const TECH = [
  { category: "Data Collection", items: ["Python", "Scrapy", "Requests"] },
  { category: "Data Processing", items: ["Pandas", "NumPy", "Scikit-learn"] },
  { category: "Machine Learning", items: ["Random Forest", "Gradient Boosting", "Ridge Regression"] },
  { category: "Backend", items: ["FastAPI", "Uvicorn", "Pydantic"] },
  { category: "Frontend", items: ["React", "Vite", "Tailwind CSS", "Recharts"] },
];

export default function AboutUs() {
  return (
    <div className="w-full min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="text-xs font-semibold uppercase tracking-widest text-purple-500 mb-4">
            Fundamentals of Data Science — Term II, Year 3
          </p>
          <h1 className="text-5xl font-bold text-gray-900 leading-tight max-w-2xl">
            Property Price
            <span className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent"> Prediction</span>
          </h1>
          <p className="mt-6 text-lg text-gray-500 leading-relaxed max-w-2xl">
            A full-stack machine learning application that predicts residential
            rental prices in Phnom Penh, Cambodia, using data collected from
            Khmer24 property listings.
          </p>

          {/* Stats */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-8 py-10 border-t border-gray-100">
            <Stat value="1,096" label="Property listings" />
            <Stat value="5" label="ML models compared" />
            <Stat value="0.59" label="Best model R² score" />
            <Stat value="4" label="Districts covered" />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-16 space-y-16">

        {/* About the project */}
        <Section label="About the Project">
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">What We Built</h2>
              <p className="text-gray-500 leading-relaxed">
                This project addresses the lack of transparent pricing in
                Cambodia's rental property market. Using machine learning, we
                built a tool that estimates monthly rent based on property
                attributes such as size, number of bedrooms and bathrooms, and
                property type.
              </p>
              <p className="text-gray-500 leading-relaxed mt-4">
                The system was trained on over 1,000 real listings scraped from
                Khmer24, one of Cambodia's largest property platforms. A Random
                Forest model was selected as the best performer after comparing
                five regression algorithms.
              </p>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">How It Works</h2>
              <ol className="space-y-4">
                {[
                  ["Data Collection", "Scrapy spider collects listings from Khmer24 across multiple Phnom Penh districts."],
                  ["Preprocessing", "Raw data is cleaned, outliers are removed, and features are engineered for model input."],
                  ["Model Training", "Five regression models are trained and evaluated. The best is saved for inference."],
                  ["Prediction API", "FastAPI serves predictions in real time based on user inputs from the web interface."],
                ].map(([step, desc], i) => (
                  <li key={i} className="flex gap-4">
                    <span className="shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-600 text-xs font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-800 text-sm">{step}</p>
                      <p className="text-gray-500 text-sm mt-0.5">{desc}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </Section>

        {/* Model results */}
        <Section label="Model Performance">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Regression Models Compared</h2>
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-6 py-3 font-semibold text-gray-600">Model</th>
                  <th className="text-right px-6 py-3 font-semibold text-gray-600">MAE</th>
                  <th className="text-right px-6 py-3 font-semibold text-gray-600">RMSE</th>
                  <th className="text-right px-6 py-3 font-semibold text-gray-600">R²</th>
                  <th className="text-right px-6 py-3 font-semibold text-gray-600"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {[
                  ["Random Forest",      "$796",   "$1,454", "0.5877", true],
                  ["Gradient Boosting",  "$784",   "$1,472", "0.5775", false],
                  ["Ridge Regression",   "$1,086", "$1,745", "0.4062", false],
                  ["Linear Regression",  "$1,090", "$1,746", "0.4057", false],
                  ["SVM (SVR)",          "$971",   "$1,883", "0.3085", false],
                ].map(([model, mae, rmse, r2, best]) => (
                  <tr key={model} className={best ? "bg-purple-50" : ""}>
                    <td className="px-6 py-4 font-medium text-gray-800 flex items-center gap-2">
                      {model}
                      {best && (
                        <span className="text-xs bg-purple-600 text-white px-2 py-0.5 rounded-full font-medium">
                          Selected
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-gray-600">{mae}</td>
                    <td className="px-6 py-4 text-right text-gray-600">{rmse}</td>
                    <td className={`px-6 py-4 text-right font-semibold ${best ? "text-purple-600" : "text-gray-600"}`}>{r2}</td>
                    <td className="px-6 py-4 text-right w-32">
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${best ? "bg-purple-500" : "bg-gray-300"}`}
                          style={{ width: `${(parseFloat(r2) / 0.5877) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Tech stack */}
        <Section label="Technology Stack">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Tools and Libraries</h2>
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
            {TECH.map(({ category, items }) => (
              <div key={category} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">{category}</p>
                <ul className="space-y-1.5">
                  {items.map((item) => (
                    <li key={item} className="text-sm font-medium text-gray-700">{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        {/* Team */}
        <Section label="The Team">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Meet the Team</h2>
          <p className="text-gray-500 text-sm mb-8">Supervised by <span className="font-semibold text-gray-700">Ms. Kim Sokhey</span> Institute of Digital Technology </p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {TEAM.map((member, i) => (
              <TeamMember key={member.name} {...member} colorIndex={i} />
            ))}
          </div>

          {/* Supervisor card */}
          <div className="mt-6 bg-white border border-purple-100 rounded-2xl p-6 shadow-sm flex items-center gap-5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-400 flex items-center justify-center shadow-sm shrink-0">
              <span className="text-white font-bold text-sm tracking-wide">KS</span>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-rose-400 mb-0.5">Advisor</p>
              <h3 className="font-semibold text-gray-900 text-base">Ms. Kim Sokhey</h3>
              <p className="text-sm text-gray-500 mt-0.5">Lecturer, Fundamentals of Data Science - Cambodia Accdemic Digital Technology</p>
            </div>
          </div>
        </Section>

        {/* Footer note */}
        <div className="border-t border-gray-100 pt-10 text-center">
          <p className="text-sm text-gray-400">
            Submitted for Fundamentals of Data Science — Institute of Technology of Cambodia, 2026
          </p>
        </div>

      </div>
    </div>
  );
}
