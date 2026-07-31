import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Activity, Search, Shield, Info, Heart, ExternalLink, X, Bot } from 'lucide-react';

export default function Diseases() {
  const [diseases, setDiseases]   = useState([]);
  const [search, setSearch]       = useState('');
  const [selected, setSelected]   = useState(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    fetch('/api/diseases')
      .then(res => res.json())
      .then(data => {
        if (data.diseases) setDiseases(data.diseases);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = diseases.filter(d =>
    d.name.toLowerCase().includes(search.toLowerCase()) ||
    d.symptoms.toLowerCase().includes(search.toLowerCase())
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
          <Link to="/diseases" className="text-blue-400 font-semibold">Diseases</Link>
          <Link to="/vaccines" className="text-slate-300 hover:text-white transition-colors">Vaccines</Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 glass px-3.5 py-1.5 rounded-full text-xs font-semibold text-rose-300 border border-rose-500/30 mb-3">
            <Activity size={14} className="text-rose-400" />
            Disease Knowledge Center
          </div>
          <h1 className="text-3xl font-extrabold text-white mb-2">Disease Awareness Library</h1>
          <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
            Evidence-based guidance on symptoms, prevention, home care, and official WHO resources for common public health conditions.
          </p>
        </div>

        {/* Search */}
        <div className="relative max-w-md mb-8">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search diseases or symptoms (e.g. Dengue, Fever, Cough)..."
            className="w-full bg-slate-800/60 border border-white/10 rounded-2xl pl-10 pr-4 py-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-lg shadow-black/20"
          />
        </div>

        {/* Grid */}
        {loading ? (
          <div className="text-center py-20 text-slate-500">Loading disease database...</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map(d => (
              <div key={d.id} className="glass rounded-3xl p-6 border border-white/8 hover:border-blue-500/30 card-hover flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">🦠</span>
                    <span className="text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-full font-medium">Verified</span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-300 transition-colors">{d.name}</h3>
                  
                  {/* Symptom Tags */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {d.symptoms.split(',').slice(0, 4).map((sym, idx) => (
                      <span key={idx} className="bg-slate-800/80 border border-white/5 text-slate-300 text-xs px-2.5 py-1 rounded-lg">
                        {sym.strip ? sym.strip() : sym.trim()}
                      </span>
                    ))}
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed line-clamp-3 mb-4">
                    {d.symptoms}
                  </p>
                </div>

                <div className="flex items-center gap-2 pt-4 border-t border-white/5">
                  <button
                    onClick={() => setSelected(d)}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 py-2 rounded-xl text-xs font-semibold transition-all"
                  >
                    <Info size={14} /> Full Details
                  </button>
                  <Link
                    to="/chat"
                    className="flex items-center justify-center gap-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 px-3 py-2 rounded-xl text-xs font-semibold transition-all"
                  >
                    <Bot size={14} /> Ask AI
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {selected && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-up">
            <div className="glass rounded-3xl max-w-2xl w-full p-6 sm:p-8 border border-white/10 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setSelected(null)}
                className="absolute top-6 right-6 text-slate-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>

              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl">🦠</span>
                <div>
                  <h2 className="text-2xl font-bold text-white">{selected.name}</h2>
                  <p className="text-xs text-emerald-400">Public Health Knowledge Base</p>
                </div>
              </div>

              {/* Symptoms */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <Activity size={16} className="text-rose-400" /> Symptoms & Indicators
                </h4>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-white/5">
                  {selected.symptoms}
                </p>
              </div>

              {/* Prevention */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <Shield size={16} className="text-emerald-400" /> Prevention & Care Guidelines
                </h4>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-white/5">
                  {selected.prevention}
                </p>
              </div>

              {/* Link */}
              {selected.info_link && (
                <a
                  href={selected.info_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 font-semibold"
                >
                  View Official WHO Fact Sheet <ExternalLink size={13} />
                </a>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
