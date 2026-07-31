import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Bot, Send, Mic, Globe, Heart, AlertTriangle, MapPin,
  Loader2, X, ExternalLink, RotateCcw, Volume2
} from 'lucide-react';

/* ── Language options ── */
const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'ta', label: 'Tamil' },
  { code: 'hi', label: 'Hindi' },
  { code: 'te', label: 'Telugu' },
  { code: 'kn', label: 'Kannada' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'bn', label: 'Bengali' },
  { code: 'mr', label: 'Marathi' },
];

/* ── Markdown-lite renderer ── */
function renderText(text) {
  // Bold **text**
  const boldified = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Bullet points
  const lines = boldified.split('\n').map(line => {
    if (line.trim().startsWith('* ') || line.trim().startsWith('- '))
      return `<li class="ml-4 list-disc">${line.replace(/^[\*\-]\s/, '')}</li>`;
    if (line.trim() === '') return '<br/>';
    return `<p>${line}</p>`;
  });
  return lines.join('');
}

/* ── Hospital card ── */
function HospitalCard({ hospital }) {
  return (
    <a
      href={hospital.maps_url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start gap-3 glass rounded-xl p-3 hover:border-blue-500/40 border border-white/5 transition-all hover:bg-blue-600/5 group"
    >
      <div className="w-8 h-8 rounded-lg bg-red-500/15 border border-red-500/30 flex items-center justify-center shrink-0 mt-0.5">
        <MapPin size={14} className="text-red-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white">{hospital.name}</p>
        <p className="text-xs text-slate-500 truncate mt-0.5">{hospital.address}</p>
      </div>
      <ExternalLink size={13} className="text-slate-600 group-hover:text-blue-400 shrink-0 mt-1 transition-colors" />
    </a>
  );
}

export default function Chat() {
  const [messages, setMessages]         = useState([]);
  const [input, setInput]               = useState('');
  const [lang, setLang]                 = useState('en');
  const [loading, setLoading]           = useState(false);
  const [emergency, setEmergency]       = useState(false);
  const [hospitals, setHospitals]       = useState([]);
  const [location, setLocation]         = useState('');
  const [searchingHosp, setSearchingHosp] = useState(false);
  const [user, setUser]                 = useState(null);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef       = useRef(null);
  const navigate       = useNavigate();

  /* Auth check */
  useEffect(() => {
    const stored = localStorage.getItem('authUser');
    if (!stored) { navigate('/login'); return; }
    setUser(JSON.parse(stored));
    // Greeting
    setMessages([{
      id: 1, role: 'bot', text:
        `Hello! 👋 I'm HealthBot AI, your personal health assistant.\n\nI can help you with:\n- **Symptoms & first aid guidance**\n- **Disease information**\n- **Nearby hospital search**\n- **Vaccination & prevention tips**\n\nHow can I assist you today?`,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }]);
  }, [navigate]);

  /* Scroll to bottom */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    const userMsg = {
      id: Date.now(), role: 'user', text: text.trim(),
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: text.trim(), language: lang }),
      });

      if (res.status === 401) { navigate('/login'); return; }

      const data = await res.json();
      const botMsg = {
        id: Date.now() + 1, role: 'bot',
        text: data.reply || data.error || 'Sorry, something went wrong.',
        timestamp: data.timestamp || new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMsg]);

      if (data.emergency) {
        setEmergency(true);
        // Auto-fetch nearby hospitals using geolocation
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async (pos) => {
            try {
              const hospRes = await fetch('/api/nearby-hospitals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
              });
              const hospData = await hospRes.json();
              if (hospData.hospitals) setHospitals(hospData.hospitals.slice(0, 5));
            } catch { /* silently fail */ }
          });
        }
      }
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'bot', text: '⚠️ Could not reach the server. Please check your connection.',
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const searchHospitalsByCity = async () => {
    if (!location.trim()) return;
    setSearchingHosp(true);
    try {
      const res = await fetch('/api/search-hospitals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ location: location.trim() }),
      });
      const data = await res.json();
      if (data.hospitals) setHospitals(data.hospitals.slice(0, 6));
    } catch { /* silently fail */ } finally {
      setSearchingHosp(false);
    }
  };

  const clearChat = () => {
    setMessages([{
      id: Date.now(), role: 'bot',
      text: 'Chat cleared. How can I help you today?',
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }]);
    setEmergency(false);
    setHospitals([]);
  };

  const speak = (text) => {
    if (!window.speechSynthesis) return;
    const utt = new SpeechSynthesisUtterance(text.replace(/<[^>]+>/g, '').replace(/\*/g, ''));
    utt.lang = lang === 'ta' ? 'ta-IN' : lang === 'hi' ? 'hi-IN' : 'en-US';
    window.speechSynthesis.speak(utt);
  };

  const currentLang = LANGUAGES.find(l => l.code === lang) || LANGUAGES[0];

  return (
    <div className="flex flex-col h-screen hero-bg">
      {/* ── Top Bar ── */}
      <header className="glass border-b border-white/10 shadow-lg shadow-black/20 z-30">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shadow-md shadow-blue-600/30 group-hover:scale-110 transition-transform">
              <Heart size={15} className="text-white" />
            </div>
            <span className="font-bold text-base tracking-tight hidden sm:block">
              <span className="gradient-text">Health</span><span className="text-white">Bot</span>
              <span className="text-blue-400 text-xs font-semibold ml-1">AI</span>
            </span>
          </Link>

          <div className="flex items-center gap-2">
            {/* Language picker */}
            <div className="relative">
              <button
                id="lang-picker"
                onClick={() => setShowLangMenu(!showLangMenu)}
                className="flex items-center gap-1.5 glass border border-white/10 px-3 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white hover:border-blue-500/40 transition-all"
              >
                <Globe size={13} />
                {currentLang.label}
              </button>
              {showLangMenu && (
                <div className="absolute right-0 top-full mt-2 w-36 glass border border-white/10 rounded-xl overflow-hidden shadow-xl z-50">
                  {LANGUAGES.map(l => (
                    <button
                      key={l.code}
                      onClick={() => { setLang(l.code); setShowLangMenu(false); }}
                      className={`w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors ${lang === l.code ? 'text-blue-400 font-medium bg-blue-600/10' : 'text-slate-300'}`}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Clear */}
            <button
              onClick={clearChat}
              title="Clear chat"
              className="flex items-center gap-1.5 glass border border-white/10 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:border-red-500/40 transition-all"
            >
              <RotateCcw size={13} />
              <span className="hidden sm:inline">Clear</span>
            </button>

            {/* Logout */}
            <button
              onClick={async () => {
                try { await fetch('/api/logout', { method: 'POST', credentials: 'include' }); } catch {}
                localStorage.removeItem('authUser');
                navigate('/login');
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/70 text-slate-300 text-xs hover:bg-slate-600 transition-all"
            >
              {user?.name ? `👤 ${user.name.split(' ')[0]}` : 'Logout'}
            </button>
          </div>
        </div>
      </header>

      {/* ── Main layout ── */}
      <div className="flex-1 overflow-hidden max-w-5xl mx-auto w-full flex gap-4 p-4">
        {/* Messages pane */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Emergency banner */}
          {emergency && (
            <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-300 rounded-2xl px-4 py-3 mb-3 text-sm">
              <AlertTriangle size={16} className="shrink-0 animate-pulse" />
              <span className="flex-1"><strong>Emergency detected.</strong> Please call emergency services immediately. Nearby hospitals are shown on the right.</span>
              <button onClick={() => setEmergency(false)} className="text-red-400 hover:text-red-200 transition-colors">
                <X size={14} />
              </button>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
            {messages.map(msg => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'bot' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shrink-0 mt-1 shadow-md shadow-blue-600/25">
                    <Bot size={15} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] group`}>
                  <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm shadow-lg shadow-blue-600/20'
                      : 'glass border border-white/8 text-slate-200 rounded-bl-sm'
                  }`}>
                    {msg.role === 'bot' ? (
                      <div
                        className="prose-sm [&>p]:mb-1 [&>li]:text-slate-300"
                        dangerouslySetInnerHTML={{ __html: renderText(msg.text) }}
                      />
                    ) : (
                      msg.text
                    )}
                  </div>
                  <div className={`flex items-center gap-2 mt-1 px-1 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <span className="text-xs text-slate-600">{msg.timestamp}</span>
                    {msg.role === 'bot' && (
                      <button
                        onClick={() => speak(msg.text)}
                        className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-blue-400 transition-all"
                        title="Read aloud"
                      >
                        <Volume2 size={11} />
                      </button>
                    )}
                  </div>
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 mt-1 text-sm font-bold text-slate-300 uppercase">
                    {user?.name?.[0] || 'U'}
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shrink-0">
                  <Bot size={15} className="text-white" />
                </div>
                <div className="glass border border-white/8 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full dot-1" />
                  <span className="w-2 h-2 bg-slate-400 rounded-full dot-2" />
                  <span className="w-2 h-2 bg-slate-400 rounded-full dot-3" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <div className="mt-4">
            <div className="glass border border-white/10 rounded-2xl p-2 flex items-end gap-2 focus-within:border-blue-500/40 transition-all shadow-lg shadow-black/20">
              <textarea
                ref={inputRef}
                id="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(input);
                  }
                }}
                placeholder="Describe your symptoms or ask a health question… (Enter to send)"
                rows={1}
                className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 focus:outline-none resize-none min-h-[36px] max-h-32 py-2 px-2 leading-relaxed"
                style={{ scrollbarWidth: 'thin' }}
              />
              <div className="flex items-center gap-1.5 pb-1">
                <button
                  onClick={() => {
                    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
                      alert('Voice input is not supported in this browser. Please use Chrome.');
                      return;
                    }
                    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                    const sr = new SR();
                    sr.lang = lang === 'ta' ? 'ta-IN' : lang === 'hi' ? 'hi-IN' : 'en-US';
                    sr.onresult = (e) => setInput(e.results[0][0].transcript);
                    sr.start();
                  }}
                  title="Voice input"
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 hover:text-blue-400 hover:bg-blue-600/10 transition-all"
                >
                  <Mic size={17} />
                </button>
                <button
                  id="chat-send"
                  onClick={() => sendMessage(input)}
                  disabled={loading || !input.trim()}
                  className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-500 flex items-center justify-center text-white shadow-lg shadow-blue-600/30 hover:from-blue-500 hover:to-emerald-500 transition-all hover:scale-110 active:scale-95 disabled:opacity-40 disabled:scale-100 disabled:cursor-not-allowed"
                >
                  {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
                </button>
              </div>
            </div>
            <p className="text-center text-xs text-slate-700 mt-2">
              HealthBot AI provides health information only. Always consult a qualified doctor for medical advice.
            </p>
          </div>
        </div>

        {/* ── Right sidebar — hospital search ── */}
        {emergency && (
          <div className="w-72 shrink-0 hidden lg:flex flex-col gap-4">
            <div className="glass rounded-2xl p-4 border border-red-500/20">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={16} className="text-red-400" />
                <h3 className="text-sm font-semibold text-red-300">Emergency — Hospitals</h3>
              </div>

              {/* City search */}
              <div className="flex gap-2 mb-3">
                <input
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && searchHospitalsByCity()}
                  placeholder="Search city..."
                  className="flex-1 bg-slate-800/60 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-red-500/50"
                />
                <button
                  onClick={searchHospitalsByCity}
                  disabled={searchingHosp}
                  className="px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-lg text-xs text-red-300 hover:bg-red-500/30 transition-all disabled:opacity-50"
                >
                  {searchingHosp ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
                </button>
              </div>

              <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
                {hospitals.length > 0
                  ? hospitals.map((h, i) => <HospitalCard key={i} hospital={h} />)
                  : (
                    <p className="text-xs text-slate-600 text-center py-4">
                      Nearby hospitals will appear here, or search by city above.
                    </p>
                  )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
