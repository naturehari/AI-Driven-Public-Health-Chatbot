import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Syringe, Search, Heart, Calendar, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function Vaccines() {
  const [vaccines, setVaccines] = useState([]);
  const [search, setSearch]     = useState('');
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    fetch('/api/vaccines')
      .then(res => res.json())
      .then(data => {
        if (data.vaccines) setVaccines(data.vaccines);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = vaccines.filter(v =>
    v.vaccine_name.toLowerCase().includes(search.toLowerCase()) ||
    v.disease_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen hero-bg flex flex-col">
      {/* Top Navbar */}
      <header className="glass border-b border-white/10 h-16 flex items-center justify-between px-4 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-blue-600/30">
            <Heart size={18} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">
            <span className="gradient-text">Health</span><span className="text-white">Bot</span>
            <span className="text-blue-400 text-xs font-semibold ml-1">AI</span>
          </span>
        </Link>
        <div className="flex items-center gap-4 text-sm font-medium">
          <Link to="/dashboard" className="text-slate-300 hover:text-white transition-colors">Dashboard</Link>
          <Link to="/chat" className="text-slate-300 hover:text-white transition-colors">Chatbot</Link>
          <Link to="/diseases" className="text-slate-300 hover:text-white transition-colors">Diseases</Link>
          <Link to="/vaccines" className="text-blue-400 font-semibold">Vaccines</Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 glass px-3.5 py-1.5 rounded-full text-xs font-semibold text-emerald-300 border border-emerald-500/30 mb-3">
            <Syringe size={14} className="text-emerald-400" />
            Immunization & Vaccine Guide
          </div>
          <h1 className="text-3xl font-extrabold text-white mb-2">Vaccination Schedule & Module</h1>
          <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
            Essential immunization schedules, age-wise eligibility, efficacy details, and WHO recommendations.
          </p>
        </div>

        {/* Search */}
        <div className="relative max-w-md mb-8">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search vaccines or target disease (e.g. Covishield, Dengvaxia, Flu)..."
            className="w-full bg-slate-800/60 border border-white/10 rounded-2xl pl-10 pr-4 py-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all shadow-lg shadow-black/20"
          />
        </div>

        {/* Grid */}
        {loading ? (
          <div className="text-center py-20 text-slate-500">Loading vaccine schedule...</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map(v => (
              <div key={v.id} className="glass rounded-3xl p-6 border border-white/8 hover:border-emerald-500/30 card-hover flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">💉</span>
                    <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full font-medium flex items-center gap-1">
                      <CheckCircle2 size={12} /> Approved
                    </span>
                  </div>

                  <span className="text-xs text-blue-400 font-semibold uppercase tracking-wider block mb-1">
                    Target: {v.disease_name}
                  </span>
                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-emerald-300 transition-colors">
                    {v.vaccine_name}
                  </h3>

                  <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-white/5 mb-4">
                    <Calendar size={15} className="text-emerald-400 shrink-0" />
                    <span><strong>Recommended Age:</strong> {v.recommended_age}</span>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed mb-4">
                    {v.description}
                  </p>
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1"><ShieldCheck size={14} className="text-emerald-400" /> Safe & Verified</span>
                  <Link to="/chat" className="text-blue-400 hover:text-blue-300 font-semibold">Consult AI Assistant →</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
