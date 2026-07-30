import { useState, useEffect, useRef } from 'react'
import {
  Globe, Mic, MessageSquare, Zap, BarChart2, Shield,
  ChevronDown, ChevronUp, Menu, X, ArrowRight, Activity,
  AlertTriangle, CheckCircle2, Heart, Stethoscope, Brain,
  FileText, Bell, Users, Syringe, Bot, Cpu, Database,
  Code2, Server, FlaskConical
} from 'lucide-react'
import './index.css'

/* ─── Chat Mockup Component ─── */
function ChatMockup() {
  const messages = [
    { id: 1, role: 'user', text: 'I have a fever and headache. What should I do?', lang: 'en', delay: 0 },
    { id: 2, role: 'bot', text: 'Based on your symptoms, you may be experiencing a viral infection. Stay hydrated, rest, and monitor your temperature. If fever exceeds 103°F, consult a doctor immediately.', lang: 'en', delay: 800 },
    { id: 3, role: 'user', text: 'என் குழந்தைக்கு காய்ச்சல் உள்ளது.', lang: 'ta', delay: 1600 },
    { id: 4, role: 'bot', text: 'உங்கள் குழந்தைக்கு காய்ச்சல் இருந்தால், நிறைய தண்ணீர் கொடுங்கள். மருத்துவரை அணுகவும்.', lang: 'ta', delay: 2400 },
  ]

  const [visible, setVisible] = useState([])
  const [typing, setTyping] = useState(false)

  useEffect(() => {
    let timers = []
    messages.forEach((msg) => {
      if (msg.role === 'bot') {
        timers.push(setTimeout(() => setTyping(true), msg.delay - 400 < 0 ? 0 : msg.delay - 400))
      }
      timers.push(setTimeout(() => {
        setTyping(false)
        setVisible(prev => [...prev, msg.id])
      }, msg.delay + 600))
    })
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="relative w-full max-w-sm mx-auto animate-float">
      {/* Glow orbs behind */}
      <div className="absolute -top-8 -right-8 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

      <div className="glass rounded-3xl overflow-hidden shadow-2xl shadow-blue-900/40">
        {/* Chat header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-700/60 to-blue-600/40 border-b border-white/10">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-emerald-400 flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">HealthBot AI</p>
            <p className="text-xs text-emerald-400">● Online — Multilingual</p>
          </div>
          <div className="ml-auto flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
          </div>
        </div>

        {/* Messages */}
        <div className="p-4 space-y-3 min-h-[280px] bg-slate-900/60">
          {messages.map(msg => (
            visible.includes(msg.id) && (
              <div key={msg.id} className={"flex " + (msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                {msg.role === 'bot' && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center mr-2 mt-1 shrink-0">
                    <Bot size={13} className="text-white" />
                  </div>
                )}
                <div className={"max-w-[82%] px-3 py-2 rounded-2xl text-xs leading-relaxed " +
                  (msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-slate-700/80 text-slate-100 rounded-bl-sm border border-white/5') +
                  (msg.lang === 'ta' ? ' font-medium' : '')
                }>
                  {msg.text}
                </div>
              </div>
            )
          ))}

          {typing && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center mr-2 shrink-0">
                <Bot size={13} className="text-white" />
              </div>
              <div className="bg-slate-700/80 border border-white/5 px-4 py-3 rounded-2xl rounded-bl-sm flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full dot-1" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full dot-2" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full dot-3" />
              </div>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="flex items-center gap-2 px-3 py-3 border-t border-white/10 bg-slate-900/80">
          <Mic size={16} className="text-blue-400 shrink-0" />
          <div className="flex-1 bg-slate-800/60 rounded-full px-3 py-1.5 text-xs text-slate-500">
            Ask a health question…
          </div>
          <button className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center">
            <ArrowRight size={12} className="text-white" />
          </button>
        </div>
      </div>

      {/* Language badge */}
      <div className="absolute -top-3 -left-3 glass px-3 py-1.5 rounded-full text-xs font-semibold text-emerald-400 border border-emerald-500/30 shadow-lg">
        🌍 Multilingual AI
      </div>
    </div>
  )
}

/* ─── Features Data ─── */
const features = [
  {
    icon: Globe,
    title: 'Multilingual Support',
    desc: 'Communicate in Tamil, Hindi, English, and more regional languages with native-level accuracy.',
    color: 'from-blue-500 to-cyan-400',
    glow: 'group-hover:shadow-blue-500/25',
  },
  {
    icon: Mic,
    title: 'Voice Input & Response',
    desc: 'Hands-free interaction through Speech-to-Text and Text-to-Speech for accessibility-first design.',
    color: 'from-violet-500 to-purple-400',
    glow: 'group-hover:shadow-violet-500/25',
  },
  {
    icon: MessageSquare,
    title: 'Disease Awareness Bot',
    desc: 'Get instant, reliable information about Fever, Cold, Dengue, Malaria, and common ailments.',
    color: 'from-emerald-500 to-teal-400',
    glow: 'group-hover:shadow-emerald-500/25',
  },
  {
    icon: Zap,
    title: 'Instant AI-Powered Replies',
    desc: 'NLP-driven engine delivers accurate health guidance in under a second, 24/7.',
    color: 'from-amber-500 to-yellow-400',
    glow: 'group-hover:shadow-amber-500/25',
  },
  {
    icon: BarChart2,
    title: 'Health Tips & Prevention',
    desc: 'Curated prevention strategies, vaccination reminders, and wellness advice tailored to you.',
    color: 'from-rose-500 to-pink-400',
    glow: 'group-hover:shadow-rose-500/25',
  },
  {
    icon: Shield,
    title: 'Reliable & Safe Information',
    desc: 'All responses verified against trusted public health databases and WHO guidelines.',
    color: 'from-sky-500 to-blue-400',
    glow: 'group-hover:shadow-sky-500/25',
  },
]

/* ─── Modules Data ─── */
const modules = [
  {
    id: 'registration',
    icon: Users,
    title: 'User Registration & Profile',
    content: 'Secure onboarding with personal health profile management. Supports multi-language preference, location-based health alerts, and personalized history tracking for better recommendations.',
  },
  {
    id: 'chatbot',
    icon: Bot,
    title: 'Health Query Chatbot',
    content: 'The core NLP engine processes natural-language health queries and provides structured, accurate responses. Supports conversational context, follow-up questions, and severity escalation prompts.',
  },
  {
    id: 'disease',
    icon: Activity,
    title: 'Disease Awareness Module',
    content: 'A curated knowledge base covering symptoms, causes, treatment, and prevention for 50+ diseases including Fever, Dengue, Malaria, COVID-19, Cholera, and more—updated continuously.',
  },
  {
    id: 'symptom',
    icon: Stethoscope,
    title: 'Symptom Information System',
    content: 'Users describe symptoms in plain language; the AI maps them to probable conditions with confidence scores, safety triage flags, and recommendations to seek professional care when needed.',
  },
  {
    id: 'vaccination',
    icon: Syringe,
    title: 'Vaccination Module',
    content: 'Maintains vaccination schedules, sends automated reminders, and provides information on available vaccines, their efficacy, and nearby health centers—integrated with government health portals.',
  },
  {
    id: 'alerts',
    icon: Bell,
    title: 'Health Alert System',
    content: 'Real-time outbreak and epidemic alert notifications based on geo-location. Pushes critical advisories from WHO and local health departments directly to users in their preferred language.',
  },
  {
    id: 'reports',
    icon: FileText,
    title: 'Report Generation',
    content: 'Generates structured health summary reports from chat sessions for sharing with doctors. Exports as PDF with symptom timelines, AI assessments, and triage recommendations.',
  },
]

/* ─── Technologies Data ─── */
const techStack = [
  { category: 'Frontend', icon: Code2, color: 'from-blue-500 to-cyan-400', items: ['HTML5', 'CSS3', 'JavaScript', 'Bootstrap'] },
  { category: 'Backend', icon: Server, color: 'from-emerald-500 to-teal-400', items: ['Python', 'Flask', 'REST API'] },
  { category: 'Database', icon: Database, color: 'from-violet-500 to-purple-400', items: ['MySQL', 'Relational DB'] },
  { category: 'Core AI', icon: Brain, color: 'from-rose-500 to-pink-400', items: ['NLP Engine', 'Intent Detection', 'Speech AI'] },
]

/* ─── Navbar ─── */
function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const links = [
    { label: 'Features', href: '#features' },
    { label: 'Modules', href: '#modules' },
    { label: 'Technologies', href: '#technologies' },
  ]

  return (
    <nav className={"fixed top-0 inset-x-0 z-50 transition-all duration-300 " + (scrolled ? 'glass border-b border-white/10 shadow-lg shadow-black/20' : 'bg-transparent')}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-blue-600/30 group-hover:scale-110 transition-transform">
              <Heart size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">
              <span className="gradient-text">Health</span>
              <span className="text-white">Bot</span>
              <span className="text-blue-400 text-xs font-semibold ml-1">AI</span>
            </span>
          </a>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-1">
            {links.map(l => (
              <a key={l.label} href={l.href}
                className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition-all duration-200">
                {l.label}
              </a>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden md:block">
            <a href="#chatbot-demo"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/30 hover:from-blue-500 hover:to-emerald-500 hover:shadow-emerald-500/20 transition-all duration-300 hover:scale-105 active:scale-95">
              <Bot size={15} />
              Try the Chatbot
            </a>
          </div>

          {/* Mobile burger */}
          <button className="md:hidden p-2 text-slate-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden glass border-t border-white/10 px-4 py-4 space-y-1">
          {links.map(l => (
            <a key={l.label} href={l.href} onClick={() => setMenuOpen(false)}
              className="block px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition-all">
              {l.label}
            </a>
          ))}
          <a href="#chatbot-demo" onClick={() => setMenuOpen(false)}
            className="block mt-3 text-center px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white text-sm font-semibold">
            Try the Chatbot
          </a>
        </div>
      )}
    </nav>
  )
}

/* ─── Hero Section ─── */
function Hero() {
  return (
    <section className="hero-bg min-h-screen flex items-center pt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left */}
          <div className="space-y-8 animate-fade-up">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-sm font-medium text-blue-300 border border-blue-500/30">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              AI-Powered • Multilingual • Free
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight">
              Instant Healthcare<br />
              <span className="gradient-text">Guidance in Your</span><br />
              Language.
            </h1>

            <p className="text-slate-400 text-lg leading-relaxed max-w-xl">
              An AI-powered public health assistant providing reliable disease awareness,
              symptom guidance, and prevention methods—accessible via{' '}
              <span className="text-blue-400 font-medium">voice or text</span> in your native language.
            </p>

            {/* Stats row */}
            <div className="flex gap-6 flex-wrap">
              {[
                { val: '50+', label: 'Diseases Covered' },
                { val: '10+', label: 'Languages' },
                { val: '24/7', label: 'Availability' },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-2xl font-bold gradient-text">{s.val}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4">
              <a href="#features"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold shadow-xl shadow-blue-600/30 hover:from-blue-500 hover:to-emerald-500 hover:shadow-emerald-500/20 transition-all duration-300 hover:scale-105 active:scale-95">
                Get Started
                <ArrowRight size={17} />
              </a>
              <a href="#modules"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl glass border border-white/10 text-slate-300 font-semibold hover:text-white hover:border-blue-500/40 hover:bg-blue-600/10 transition-all duration-300">
                View Architecture
                <Brain size={17} />
              </a>
            </div>
          </div>

          {/* Right — Chat Mockup */}
          <div id="chatbot-demo" className="flex justify-center lg:justify-end">
            <ChatMockup />
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─── Problem & Solution ─── */
function ProblemSolution() {
  return (
    <section className="py-24 section-glow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-blue-400 text-sm font-semibold uppercase tracking-widest mb-3">Why We Built This</p>
          <h2 className="text-3xl sm:text-4xl font-bold">The Problem. The Solution.</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Problem */}
          <div className="glass rounded-3xl p-8 border border-rose-500/20 card-hover group">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <AlertTriangle size={22} className="text-rose-400" />
              </div>
              <h3 className="text-xl font-bold text-rose-300">The Problem</h3>
            </div>
            <ul className="space-y-4 text-slate-300 text-sm leading-relaxed">
              {[
                'Millions lack immediate access to reliable, localized healthcare information.',
                'Health misinformation spreads faster than verified guidance during outbreaks.',
                'Language barriers prevent rural populations from accessing critical medical advice.',
                'Delayed diagnosis due to unawareness leads to preventable deaths and complications.',
                'Overburdened health systems cannot respond to every individual query in real time.',
              ].map((item, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-1 w-5 h-5 rounded-full bg-rose-500/20 border border-rose-500/30 flex items-center justify-center shrink-0 text-rose-400 font-bold text-xs">{i + 1}</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Solution */}
          <div className="glass rounded-3xl p-8 border border-emerald-500/20 card-hover group">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                <CheckCircle2 size={22} className="text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold text-emerald-300">The Solution</h3>
            </div>
            <ul className="space-y-4 text-slate-300 text-sm leading-relaxed">
              {[
                'An intelligent AI chatbot that delivers instant, verified health information 24/7.',
                'Multilingual NLP engine breaks language barriers across 10+ regional languages.',
                'Automated health alerts notify communities of outbreaks before they escalate.',
                'Voice interface ensures accessibility for non-literate and visually impaired users.',
                'Structured triage system escalates critical cases to professional medical attention.',
              ].map((item, i) => (
                <li key={i} className="flex gap-3">
                  <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─── Features Grid ─── */
function Features() {
  return (
    <section id="features" className="py-24 bg-slate-900/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-400 text-sm font-semibold uppercase tracking-widest mb-3">Capabilities</p>
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Key Features</h2>
          <p className="text-slate-400 max-w-xl mx-auto">Designed for universal accessibility with cutting-edge AI at its core.</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={i}
              className={"group glass rounded-2xl p-6 card-hover border border-white/5 hover:border-white/15 transition-all duration-300"}
              style={{ animationDelay: i * 100 + 'ms' }}
            >
              <div className={"w-12 h-12 rounded-xl bg-gradient-to-br " + f.color + " p-0.5 mb-5 group-hover:scale-110 transition-transform duration-300 shadow-lg " + f.glow}>
                <div className="w-full h-full rounded-[10px] bg-slate-900/70 flex items-center justify-center">
                  <f.icon size={22} className="text-white" />
                </div>
              </div>
              <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─── Modules Accordion ─── */
function Modules() {
  const [open, setOpen] = useState('chatbot')

  return (
    <section id="modules" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-400 text-sm font-semibold uppercase tracking-widest mb-3">Architecture</p>
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">System Modules</h2>
          <p className="text-slate-400 max-w-xl mx-auto">Explore the core building blocks powering the platform.</p>
        </div>

        <div className="max-w-3xl mx-auto space-y-3">
          {modules.map((mod) => {
            const isOpen = open === mod.id
            return (
              <div key={mod.id}
                className={"glass rounded-2xl border transition-all duration-300 overflow-hidden " +
                  (isOpen ? 'border-blue-500/40 shadow-lg shadow-blue-500/10' : 'border-white/5 hover:border-white/15')}>
                <button
                  onClick={() => setOpen(isOpen ? null : mod.id)}
                  className="w-full flex items-center gap-4 px-6 py-5 text-left"
                >
                  <div className={"w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-300 " +
                    (isOpen ? 'bg-blue-600' : 'bg-white/5')}>
                    <mod.icon size={18} className={isOpen ? 'text-white' : 'text-slate-400'} />
                  </div>
                  <span className={"font-semibold flex-1 text-left transition-colors " + (isOpen ? 'text-white' : 'text-slate-300')}>
                    {mod.title}
                  </span>
                  {isOpen
                    ? <ChevronUp size={18} className="text-blue-400 shrink-0" />
                    : <ChevronDown size={18} className="text-slate-500 shrink-0" />
                  }
                </button>
                {isOpen && (
                  <div className="px-6 pb-5 animate-fade-up">
                    <p className="text-sm text-slate-400 leading-relaxed border-t border-white/5 pt-4 ml-14">
                      {mod.content}
                    </p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

/* ─── Technologies ─── */
function Technologies() {
  return (
    <section id="technologies" className="py-24 bg-slate-900/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-400 text-sm font-semibold uppercase tracking-widest mb-3">Stack</p>
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Technologies Used</h2>
          <p className="text-slate-400 max-w-xl mx-auto">A robust, scalable stack built for performance, reliability, and AI capability.</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {techStack.map((tech, i) => (
            <div key={i} className="glass rounded-2xl p-6 card-hover border border-white/5 hover:border-white/15 group text-center">
              <div className={"w-14 h-14 rounded-2xl bg-gradient-to-br " + tech.color + " p-0.5 mx-auto mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg"}>
                <div className="w-full h-full rounded-[14px] bg-slate-900/80 flex items-center justify-center">
                  <tech.icon size={24} className="text-white" />
                </div>
              </div>
              <h3 className="font-bold text-white mb-4">{tech.category}</h3>
              <div className="flex flex-wrap justify-center gap-2">
                {tech.items.map((item, j) => (
                  <span key={j} className="px-2.5 py-1 text-xs font-medium rounded-full glass border border-white/10 text-slate-300">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Data flow row */}
        <div className="mt-12 glass rounded-2xl p-6 border border-white/5">
          <p className="text-center text-xs text-slate-500 uppercase tracking-widest font-semibold mb-6">Data Flow</p>
          <div className="flex flex-wrap items-center justify-center gap-2 text-sm font-medium">
            {['User (Voice/Text)', '→', 'Speech-to-Text', '→', 'NLP Engine', '→', 'Flask API', '→', 'MySQL DB', '→', 'Response Generation', '→', 'User'].map((step, i) => (
              step === '→'
                ? <span key={i} className="text-blue-500 text-lg font-bold">{step}</span>
                : <span key={i} className="glass px-3 py-1.5 rounded-lg text-slate-300 border border-white/10 text-xs">{step}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer className="border-t border-white/5 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center">
              <Heart size={15} className="text-white" />
            </div>
            <span className="font-bold text-base">
              <span className="gradient-text">Health</span>
              <span className="text-white">Bot</span>
              <span className="text-blue-400 text-xs font-semibold ml-1">AI</span>
            </span>
          </div>

          {/* Disclaimer */}
          <p className="text-xs text-slate-500 text-center max-w-md leading-relaxed">
            ⚕️ <strong className="text-slate-400">Disclaimer:</strong> For informational purposes only.
            Not a substitute for professional medical advice, diagnosis, or treatment.
            Always consult a qualified healthcare provider.
          </p>

          {/* Copyright */}
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} HealthBot AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

/* ─── Root App ─── */
export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <ProblemSolution />
      <Features />
      <Modules />
      <Technologies />
      <Footer />
    </div>
  )
}
