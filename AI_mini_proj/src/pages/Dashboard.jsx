import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Bell, Activity, Syringe, MapPin, Heart, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function Dashboard() {
  const [alerts, setAlerts]   = useState([]);
  const [user, setUser]       = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('authUser');
    if (stored) setUser(JSON.parse(stored));

    fetch('/api/alerts')
      .then(res => res.json())
      .then(data => {
        if (data.alerts) setAlerts(data.alerts);
      })
      .catch(() => {});
  }, []);

  const getSeverityBadge = (sev) => {
    switch (sev.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'medium':
        return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
      default:
        return 'bg-blue-500/10 border-blue-500/30 text-blue-400';
    }
  };

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
          <Link to="/dashboard" className="text-blue-400 font-semibold">Dashboard</Link>
          <Link to="/chat" className="text-slate-300 hover:text-white transition-colors">Chatbot</Link>
          <Link to="/diseases" className="text-slate-300 hover:text-white transition-colors">Diseases</Link>
          <Link to="/vaccines" className="text-slate-300 hover:text-white transition-colors">Vaccines</Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome */}
        <div className="glass rounded-3xl p-8 border border-white/10 mb-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10">
            <h1 className="text-3xl font-extrabold text-white mb-2">
              Welcome back, <span className="gradient-text">{user?.name || 'Health User'}</span> 👋
            </h1>
            <p className="text-slate-400 text-sm max-w-2xl leading-relaxed mb-6">
              Your central AI public health hub. Access disease guidance, local health advisories, vaccination schedules, and live AI symptom triage.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                to="/chat"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/30 hover:scale-105 active:scale-95 transition-all"
              >
                <Bot size={16} /> Start AI Symptom Chat
              </Link>
              <Link
                to="/diseases"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl glass border border-white/10 text-slate-300 text-sm font-semibold hover:text-white transition-all"
              >
                <Activity size={16} className="text-rose-400" /> Explore Diseases
              </Link>
            </div>
          </div>
        </div>

        {/* Action Modules Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-10">
          <Link to="/chat" className="glass rounded-3xl p-6 border border-white/8 hover:border-blue-500/40 card-hover group">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Bot size={22} className="text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">AI Chatbot</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Interactive multi-turn disease guidance & triage.</p>
          </Link>

          <Link to="/diseases" className="glass rounded-3xl p-6 border border-white/8 hover:border-rose-500/40 card-hover group">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Activity size={22} className="text-rose-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Disease Center</h3>
            <p className="text-xs text-slate-400 leading-relaxed">50+ disease symptoms, prevention & WHO guides.</p>
          </Link>

          <Link to="/vaccines" className="glass rounded-3xl p-6 border border-white/8 hover:border-emerald-500/40 card-hover group">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Syringe size={22} className="text-emerald-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Vaccines</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Schedule & age eligibility recommendations.</p>
          </Link>

          <Link to="/chat" className="glass rounded-3xl p-6 border border-white/8 hover:border-amber-500/40 card-hover group">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <MapPin size={22} className="text-amber-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Hospitals</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Find nearby hospitals & emergency rooms.</p>
          </Link>
        </div>

        {/* Public Health Alerts Section */}
        <div className="glass rounded-3xl p-8 border border-white/10">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center justify-center">
                <Bell size={18} className="text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Public Health & Outbreak Alerts</h3>
                <p className="text-xs text-slate-400">Real-time WHO & local health department advisories</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {alerts.map(a => (
              <div key={a.id} className="glass rounded-2xl p-5 border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-white/5 transition-all">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${getSeverityBadge(a.severity)}`}>
                      {a.severity}
                    </span>
                    <span className="text-xs text-slate-500">{a.date_issued}</span>
                  </div>
                  <h4 className="text-base font-semibold text-white">{a.title}</h4>
                  <p className="text-xs text-slate-400 leading-relaxed">{a.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
