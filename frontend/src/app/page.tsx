"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Upload, BarChart3, Binary, Settings, AlertCircle, CheckCircle2,
  Database, Play, Layers, RefreshCw, FileText, ChevronRight,
  TrendingUp, TrendingDown, Minus, Sparkles, Activity, Target,
  Brain, Globe, Zap, Star, ArrowRight, Terminal as TerminalIcon,
  ChevronUp, ChevronDown, Sliders, PlayCircle
} from "lucide-react";
import { motion, AnimatePresence, useSpring, useTransform, useMotionValue } from "framer-motion";
import * as api from "../lib/api";

// ─── Animation Variants ────────────────────────────────────────────────────────

const fadeUpVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] as const, delay: i * 0.07 },
  }),
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
};

const cardVariants = {
  hidden: { opacity: 0, scale: 0.97, y: 12 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};

// ─── 3D Parallax Tilt Card ──────────────────────────────────────────────────

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
}
function TiltCard({ children, className = "" }: TiltCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [15, -15]), { stiffness: 300, damping: 30 });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-15, 15]), { stiffness: 300, damping: 30 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = cardRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left - width / 2;
    const mouseY = e.clientY - rect.top - height / 2;
    x.set(mouseX / width);
    y.set(mouseY / height);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      className={`group relative ${className}`}
    >
      <div style={{ transform: "translateZ(10px)" }} className="h-full w-full">
        {children}
      </div>
    </motion.div>
  );
}

// ─── AnimatedCounter ──────────────────────────────────────────────────────────

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
  decimals?: number;
}
function AnimatedCounter({ value, prefix = "", suffix = "", duration = 1200, decimals }: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let rafId: number;
    let startTs: number | null = null;
    const from = 0;
    const to = value;

    const step = (ts: number) => {
      if (!startTs) startTs = ts;
      const progress = Math.min((ts - startTs) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4); // easeOutQuart
      setDisplayValue(from + (to - from) * eased);
      if (progress < 1) rafId = requestAnimationFrame(step);
      else setDisplayValue(to);
    };

    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  }, [value, duration]);

  const isFloat = decimals !== undefined ? true : value % 1 !== 0;
  const formatted = isFloat
    ? displayValue.toFixed(decimals ?? 2)
    : Math.floor(displayValue).toLocaleString();

  return (
    <span className="tabular-nums">
      {prefix}{formatted}{suffix}
    </span>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

interface KpiCardProps {
  title: string;
  value: number | string;
  suffix?: string;
  prefix?: string;
  icon?: React.ReactNode;
}
function KpiCard({ title, value, suffix, prefix, icon }: KpiCardProps) {
  const numVal = typeof value === "string" ? parseFloat(value) : value;
  const isNumeric = !isNaN(numVal);

  return (
    <TiltCard className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 overflow-hidden hover:border-zinc-700 transition-colors duration-300">
      {/* Ambient glow on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none bg-gradient-to-br from-blue-950/20 to-transparent rounded-xl" />
      
      <div className="relative flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2">
            {icon && <span className="text-zinc-600 group-hover:text-blue-500 transition-colors duration-300">{icon}</span>}
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-zinc-500">{title}</p>
          </div>
          <p className="text-3xl font-semibold tracking-tight text-white">
            {isNumeric ? (
              <AnimatedCounter value={numVal} prefix={prefix} suffix={suffix} />
            ) : (
              <span>{value}</span>
            )}
          </p>
        </div>
      </div>
    </TiltCard>
  );
}

// ─── Quality Gauge ────────────────────────────────────────────────────────────

interface QualityGaugeProps { score: number; label?: string; }
function QualityGauge({ score, label = "Quality Score" }: QualityGaugeProps) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const strokeColor = score >= 80 ? "#10B981" : score >= 50 ? "#F59E0B" : "#EF4444";
  const glowColor = score >= 80 ? "rgba(16,185,129,0.3)" : score >= 50 ? "rgba(245,158,11,0.3)" : "rgba(239,68,68,0.3)";

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-44 h-44 flex items-center justify-center">
        {/* Outer glow ring */}
        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{ boxShadow: [`0 0 0px ${glowColor}`, `0 0 30px ${glowColor}`, `0 0 0px ${glowColor}`] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
        />

        <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="10" />
          <motion.circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.5, ease: [0.25, 0.46, 0.45, 0.94] as const, delay: 0.3 }}
            style={{ filter: `drop-shadow(0 0 8px ${strokeColor})` }}
          />
        </svg>

        <div className="absolute flex flex-col items-center">
          <motion.span
            className="text-4xl font-bold tracking-tight text-white"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <AnimatedCounter value={score} />
          </motion.span>
          <span className="text-xs text-zinc-500 mt-0.5 font-mono">/ 100</span>
        </div>
      </div>
      <motion.span
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500"
      >
        {label}
      </motion.span>
    </div>
  );
}

// ─── Physics Universe Canvas ──────────────────────────────────────────────────

interface PhysicsUniverseProps {
  nodes: { label: string }[];
  edges: { source: number; target: number; strength: number }[];
}
function PhysicsUniverse({ nodes: initialNodes, edges: initialEdges }: PhysicsUniverseProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Live simulation settings
  const [repulsion, setRepulsion] = useState(3200);
  const [springStrength, setSpringStrength] = useState(0.025);
  const [gravity, setGravity] = useState(0.004);
  const [idealDistance, setIdealDistance] = useState(150);

  // Sync ref variables for canvas animation loop to avoid dependency updates interrupting
  const paramsRef = useRef({ repulsion, springStrength, gravity, idealDistance });
  useEffect(() => {
    paramsRef.current = { repulsion, springStrength, gravity, idealDistance };
  }, [repulsion, springStrength, gravity, idealDistance]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = container.clientWidth || 600;
    const height = 480;
    canvas.width = width;
    canvas.height = height;

    const nodes = initialNodes.map((n, i) => ({
      id: i, label: n.label,
      x: width / 2 + (Math.random() - 0.5) * width * 0.5,
      y: height / 2 + (Math.random() - 0.5) * height * 0.5,
      vx: 0, vy: 0, r: 5,
    }));

    const DAMPING = 0.78;
    let dragNode: typeof nodes[0] | null = null, ox = 0, oy = 0;
    let frameCount = 0;

    const handleResize = () => { width = container.clientWidth || 600; canvas.width = width; };
    window.addEventListener("resize", handleResize);

    let rafId: number;

    const sim = () => {
      const { repulsion: rep, springStrength: spr, gravity: grav, idealDistance: idealDist } = paramsRef.current;

      nodes.forEach(n => { n.vx += (width / 2 - n.x) * grav; n.vy += (height / 2 - n.y) * grav; });
      for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y;
        const d2 = dx * dx + dy * dy + 1, d = Math.sqrt(d2), f = rep / d2;
        nodes[i].vx -= (dx / d) * f; nodes[i].vy -= (dy / d) * f;
        nodes[j].vx += (dx / d) * f; nodes[j].vy += (dy / d) * f;
      }
      initialEdges.forEach(e => {
        const a = nodes[e.source], b = nodes[e.target];
        if (!a || !b) return;
        const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) + 1;
        const ideal = idealDist - Math.abs(e.strength) * 80, f = spr * (d - ideal) * Math.abs(e.strength);
        a.vx += (dx / d) * f; a.vy += (dy / d) * f;
        b.vx -= (dx / d) * f; b.vy -= (dy / d) * f;
      });
      nodes.forEach(n => {
        if (n === dragNode) return;
        n.vx *= DAMPING; n.vy *= DAMPING; n.x += n.vx; n.y += n.vy;
        n.x = Math.max(16, Math.min(width - 16, n.x));
        n.y = Math.max(16, Math.min(height - 16, n.y));
      });
    };

    const draw = () => {
      frameCount++;
      ctx.clearRect(0, 0, width, height);

      // Subtle particle background
      if (frameCount % 3 === 0) {
        ctx.fillStyle = "rgba(59,130,246,0.3)";
        const px = Math.random() * width, py = Math.random() * height;
        ctx.beginPath();
        ctx.arc(px, py, 0.5, 0, Math.PI * 2);
        ctx.fill();
      }

      initialEdges.forEach(e => {
        const a = nodes[e.source], b = nodes[e.target];
        if (!a || !b) return;
        const alpha = 0.12 + Math.abs(e.strength) * 0.5;
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
        if (e.strength > 0) {
          grad.addColorStop(0, `rgba(59,130,246,${alpha})`);
          grad.addColorStop(1, `rgba(99,102,241,${alpha})`);
        } else {
          grad.addColorStop(0, `rgba(239,68,68,${alpha})`);
          grad.addColorStop(1, `rgba(236,72,153,${alpha})`);
        }
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 0.8 + Math.abs(e.strength) * 2.2;
        ctx.stroke();
      });

      nodes.forEach(n => {
        const isDrag = n === dragNode;
        const glowRadius = isDrag ? 24 : 12;
        const glowColor = isDrag ? "rgba(59,130,246,0.4)" : "rgba(255,255,255,0.06)";
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, glowRadius);
        grad.addColorStop(0, glowColor);
        grad.addColorStop(1, "transparent");
        ctx.beginPath(); ctx.arc(n.x, n.y, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = grad; ctx.fill();

        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = isDrag ? "#3B82F6" : "#E4E4E7";
        ctx.shadowColor = isDrag ? "#3B82F6" : "rgba(255,255,255,0.3)";
        ctx.shadowBlur = isDrag ? 14 : 4;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = "#71717A";
        ctx.font = "500 10.5px 'Inter', system-ui, sans-serif";
        ctx.textAlign = "center"; ctx.textBaseline = "top";
        ctx.fillText(n.label, n.x, n.y + n.r + 5);
      });
    };

    const tick = () => { sim(); draw(); rafId = requestAnimationFrame(tick); };
    tick();

    const getPos = (e: MouseEvent | TouchEvent) => {
      const r = canvas.getBoundingClientRect();
      const t = "touches" in e ? e.touches[0] : e;
      return { x: t.clientX - r.left, y: t.clientY - r.top };
    };
    const onStart = (p: { x: number; y: number }) => {
      dragNode = nodes.find(n => Math.hypot(n.x - p.x, n.y - p.y) < 20) || null;
      if (dragNode) { ox = dragNode.x - p.x; oy = dragNode.y - p.y; }
    };
    const onMove = (p: { x: number; y: number }) => { if (dragNode) { dragNode.x = p.x + ox; dragNode.y = p.y + oy; } };
    const onEnd = () => { dragNode = null; };

    canvas.addEventListener("mousedown", e => onStart(getPos(e)));
    window.addEventListener("mousemove", e => onMove(getPos(e)));
    window.addEventListener("mouseup", onEnd);
    canvas.addEventListener("touchstart", e => onStart(getPos(e)));
    window.addEventListener("touchmove", e => onMove(getPos(e)));
    window.addEventListener("touchend", onEnd);

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(rafId);
    };
  }, [initialNodes, initialEdges]);

  return (
    <div className="grid grid-cols-4 gap-6">
      <motion.div
        ref={containerRef}
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="col-span-3 relative w-full h-[480px] bg-[#020204] border border-zinc-900 rounded-xl overflow-hidden"
      >
        <canvas ref={canvasRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
        <div className="absolute bottom-4 left-4 flex gap-4 text-[11px] text-zinc-600 font-medium">
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.7)]" />Positive Correlation</div>
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.7)]" />Negative Correlation</div>
          <div className="flex items-center gap-1.5 text-zinc-500">Drag nodes to explore</div>
        </div>
        <div className="absolute top-4 right-4 px-2.5 py-1 rounded bg-blue-950/50 border border-blue-900/50 text-[10px] text-blue-400 font-mono uppercase tracking-wider">
          Live Physics
        </div>
      </motion.div>

      {/* Physics Sliders */}
      <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-6 flex flex-col justify-center">
        <div className="space-y-2">
          <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5"><Sliders size={13} /> Physics Tuner</p>
          <p className="text-xs text-zinc-600">Adjust the forces controlling the correlation universe in real-time.</p>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono"><span className="text-zinc-500">Node Repulsion</span><span className="text-zinc-400">{repulsion}</span></div>
            <input type="range" min="1000" max="6000" step="100" value={repulsion} onChange={e => setRepulsion(Number(e.target.value))} className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono"><span className="text-zinc-500">Spring Strength</span><span className="text-zinc-400">{springStrength.toFixed(3)}</span></div>
            <input type="range" min="0.005" max="0.08" step="0.005" value={springStrength} onChange={e => setSpringStrength(Number(e.target.value))} className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono"><span className="text-zinc-500">Center Gravity</span><span className="text-zinc-400">{gravity.toFixed(4)}</span></div>
            <input type="range" min="0.001" max="0.015" step="0.001" value={gravity} onChange={e => setGravity(Number(e.target.value))} className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono"><span className="text-zinc-500">Ideal Separation</span><span className="text-zinc-400">{idealDistance}px</span></div>
            <input type="range" min="80" max="220" step="10" value={idealDistance} onChange={e => setIdealDistance(Number(e.target.value))} className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          </div>
        </div>

        <button onClick={() => { setRepulsion(3200); setSpringStrength(0.025); setGravity(0.004); setIdealDistance(150); }}
          className="w-full bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-400 text-xs font-semibold py-2 rounded-lg transition-colors">
          Reset to default
        </button>
      </div>
    </div>
  );
}

// ─── Loading Overlay ──────────────────────────────────────────────────────────

function LoadingOverlay({ label }: { label: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center py-24 gap-5"
    >
      <div className="relative">
        <motion.div
          className="w-14 h-14 rounded-full border-2 border-blue-500/30"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute inset-0 w-14 h-14 rounded-full border-t-2 border-blue-500"
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <Sparkles size={16} className="text-blue-500" />
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm text-zinc-300 font-medium">{label}</p>
        <motion.p
          className="text-xs text-zinc-600 mt-1"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          Processing…
        </motion.p>
      </div>
    </motion.div>
  );
}

// ─── Sidebar Nav Item ─────────────────────────────────────────────────────────

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
  badge?: string;
}
function NavItem({ icon, label, active, disabled, onClick, badge }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full group flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative
        ${disabled ? "opacity-30 cursor-not-allowed" : "cursor-pointer"}
        ${active ? "bg-zinc-900 text-white" : "text-zinc-500 hover:bg-zinc-900/60 hover:text-zinc-200"}
      `}
    >
      {active && (
        <motion.div
          layoutId="nav-pill"
          className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500 rounded-full"
          transition={{ type: "spring", stiffness: 400, damping: 35 }}
        />
      )}
      <span className={`${active ? "text-blue-400" : "text-zinc-600 group-hover:text-zinc-400"} transition-colors`}>
        {icon}
      </span>
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <span className="text-[10px] bg-blue-600/20 border border-blue-500/30 text-blue-400 px-1.5 py-0.5 rounded font-mono">
          {badge}
        </span>
      )}
    </button>
  );
}

// ─── Insight Chip ─────────────────────────────────────────────────────────────

function InsightChip({ text, index }: { text: string; index: number }) {
  return (
    <motion.div
      variants={fadeUpVariants}
      custom={index}
      className="group flex items-start gap-3 p-3.5 bg-zinc-950 border border-zinc-900 rounded-lg hover:border-zinc-700 transition-colors duration-200"
    >
      <motion.div
        className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 shrink-0"
        animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 3, repeat: Infinity, delay: index * 0.2 }}
      />
      <p className="text-xs text-zinc-400 leading-relaxed group-hover:text-zinc-300 transition-colors">{text}</p>
    </motion.div>
  );
}

// ─── Progress Bar ─────────────────────────────────────────────────────────────

function ProgressBar({ label, value, max = 1 }: { label: string; value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center text-xs">
        <span className="text-zinc-300 font-medium truncate max-w-[160px]">{label}</span>
        <span className="text-zinc-500 font-mono">{(pct).toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-zinc-900 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] as const, delay: 0.2 }}
        />
      </div>
    </div>
  );
}

// ─── Interactive Console Terminal ───────────────────────────────────────────

interface TerminalLog {
  timestamp: string;
  message: string;
  type: "info" | "success" | "warning" | "error" | "system";
}

interface InteractiveConsoleProps {
  logs: TerminalLog[];
  onClear: () => void;
}
function InteractiveConsole({ logs, onClear }: InteractiveConsoleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, isOpen]);

  return (
    <motion.div
      initial={{ height: 40 }}
      animate={{ height: isOpen ? 220 : 40 }}
      transition={{ type: "spring", stiffness: 350, damping: 30 }}
      className="fixed bottom-0 left-60 right-0 bg-[#06060a] border-t border-zinc-900 font-mono z-40 overflow-hidden shadow-[0_-8px_30px_rgba(0,0,0,0.8)]"
    >
      {/* Console Bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="h-10 px-5 flex items-center justify-between border-b border-zinc-900/50 cursor-pointer select-none bg-zinc-950/60 hover:bg-zinc-950 transition-colors"
      >
        <div className="flex items-center gap-2 text-zinc-400">
          <TerminalIcon size={14} className="text-blue-500" />
          <span className="text-xs font-semibold uppercase tracking-wider">FastAPI Execution Terminal</span>
          <span className="text-[10px] bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded text-zinc-500 font-mono">
            {logs.length} events
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="text-[10px] text-zinc-600 hover:text-zinc-400 font-semibold tracking-wider uppercase transition-colors"
          >
            Clear Log
          </button>
          {isOpen ? <ChevronDown size={14} className="text-zinc-500" /> : <ChevronUp size={14} className="text-zinc-500" />}
        </div>
      </div>

      {/* Terminal Output */}
      <div className="p-4 h-[180px] overflow-y-auto space-y-1.5 text-xs text-zinc-400">
        {logs.length === 0 ? (
          <p className="text-zinc-700 italic">Terminal idle. Logs will stream in real-time as you execute tasks.</p>
        ) : (
          logs.map((log, idx) => {
            let color = "text-zinc-500";
            if (log.type === "success") color = "text-emerald-400";
            if (log.type === "warning") color = "text-amber-500";
            if (log.type === "error") color = "text-red-500";
            if (log.type === "system") color = "text-cyan-500";

            return (
              <div key={idx} className="flex gap-2 items-start hover:bg-zinc-900/35 px-1 py-0.5 rounded">
                <span className="text-zinc-700 select-none">[{log.timestamp}]</span>
                <span className={`font-semibold shrink-0 select-none ${color}`}>{log.type.toUpperCase()}:</span>
                <span className="text-zinc-300 whitespace-pre-wrap">{log.message}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </motion.div>
  );
}

// ─── Simulated ML Training Terminal ──────────────────────────────────────────

interface MLTrainingLog {
  step: string;
  status: "pending" | "running" | "done" | "error";
  duration?: string;
}

interface TrainingTerminalProps {
  logs: MLTrainingLog[];
  onComplete: () => void;
  targetCol: string;
}
function TrainingTerminal({ logs, onComplete, targetCol }: TrainingTerminalProps) {
  return (
    <div className="bg-[#020204] border border-zinc-900 rounded-xl p-5 space-y-4 max-w-xl mx-auto font-mono text-xs shadow-[0_0_40px_rgba(59,130,246,0.15)]">
      <div className="flex justify-between items-center border-b border-zinc-900 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
          <span className="font-semibold text-zinc-400">ML Training Pipeline: {targetCol}</span>
        </div>
        <span className="text-[10px] text-zinc-600 font-semibold tracking-wider uppercase">Active Pipeline Thread</span>
      </div>

      <div className="space-y-2.5 py-2">
        {logs.map((log, idx) => {
          let icon = <div className="w-1.5 h-1.5 rounded-full bg-zinc-800 mt-1" />;
          let color = "text-zinc-600";

          if (log.status === "running") {
            icon = <RefreshCw size={11} className="animate-spin text-blue-500 mt-0.5" />;
            color = "text-blue-400 font-semibold";
          } else if (log.status === "done") {
            icon = <CheckCircle2 size={11} className="text-emerald-500 mt-0.5" />;
            color = "text-zinc-300";
          } else if (log.status === "error") {
            icon = <AlertCircle size={11} className="text-red-500 mt-0.5" />;
            color = "text-red-400";
          }

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start gap-3"
            >
              {icon}
              <div className="flex-1 flex justify-between">
                <span className={color}>{log.step}</span>
                {log.duration && <span className="text-zinc-600 font-mono">{log.duration}</span>}
              </div>
            </motion.div>
          );
        })}
      </div>

      {logs.every(l => l.status === "done") && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="pt-2 border-t border-zinc-900 flex justify-end"
        >
          <button
            onClick={onComplete}
            className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-[0_0_15px_rgba(59,130,246,0.4)]"
          >
            <span>Load Model Workspace</span>
            <ArrowRight size={13} />
          </button>
        </motion.div>
      )}
    </div>
  );
}

// ─── MAIN PAGE ────────────────────────────────────────────────────────────────

type Tab = "upload" | "profiling" | "correlation" | "ml" | "insights";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("upload");

  // Console Logs
  const [consoleLogs, setConsoleLogs] = useState<TerminalLog[]>([
    { timestamp: new Date().toLocaleTimeString(), type: "system", message: "Initial connection handshake to FastAPI server completed at http://127.0.0.1:8000" }
  ]);

  const addLog = useCallback((message: string, type: TerminalLog["type"] = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setConsoleLogs(prev => [...prev, { timestamp, message, type }]);
  }, []);

  // Upload
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [mergeStrategy, setMergeStrategy] = useState("Stack (Union)");
  const [keyCol, setKeyCol] = useState("");
  const [how, setHow] = useState("inner");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  // Overview
  const [datasetOverview, setDatasetOverview] = useState<any>(null);
  const [columnRoles, setColumnRoles] = useState<any>(null);
  const [autoNarrative, setAutoNarrative] = useState("");
  const [previewData, setPreviewData] = useState<any>(null);

  // Profiling
  const [profilingLoading, setProfilingLoading] = useState(false);
  const [qualityScore, setQualityScore] = useState<any>(null);
  const [profilingRows, setProfilingRows] = useState<any[]>([]);
  const [profilingNarration, setProfilingNarration] = useState("");
  const [aiSummary, setAiSummary] = useState("");
  const [outlierMethod, setOutlierMethod] = useState<"IQR" | "Z-Score">("IQR");
  const [outliersSummary, setOutliersSummary] = useState<any>(null);
  const [outliersNarration, setOutliersNarration] = useState("");
  const [outlierDetails, setOutlierDetails] = useState<any>(null);
  const [selectedOutlierCol, setSelectedOutlierCol] = useState("");
  const [flagDesc, setFlagDesc] = useState("");
  const [flagType, setFlagType] = useState("anomaly");

  // Correlation
  const [corrLoading, setCorrLoading] = useState(false);
  const [corrCols, setCorrCols] = useState<string[]>([]);
  const [corrMatrix, setCorrMatrix] = useState<any>(null);
  const [physicsData, setPhysicsData] = useState<any>(null);
  const [corrTab, setCorrTab] = useState<"heatmap" | "universe">("universe");

  // ML
  const [targetCol, setTargetCol] = useState("");
  const [mlLoading, setMlLoading] = useState(false);
  const [mlTask, setMlTask] = useState("");
  const [mlResults, setMlResults] = useState<any>(null);
  const [mlOpinion, setMlOpinion] = useState("");
  const [bestModel, setBestModel] = useState("");
  const [featureImportance, setFeatureImportance] = useState<any[]>([]);

  // Simulated ML Training logs
  const [showTrainingTerminal, setShowTrainingTerminal] = useState(false);
  const [trainingLogs, setTrainingLogs] = useState<MLTrainingLog[]>([]);

  // Insights
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsList, setInsightsList] = useState<string[]>([]);
  const [insightsNarrative, setInsightsNarrative] = useState("");
  const [flagsList, setFlagsList] = useState<any[]>([]);

  // Preview on upload success
  useEffect(() => {
    if (datasetOverview) {
      api.getPreview(60).then(res => setPreviewData(res)).catch(console.error);
    }
  }, [datasetOverview]);

  // Drag-and-drop handlers
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setSelectedFiles(files);
      addLog(`File drop detected: selected ${files.length} file(s).`, "info");
    }
  }, [addLog]);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);

  const executeUpload = async () => {
    if (!selectedFiles.length) return;
    setIsUploading(true); setUploadError("");
    addLog(`Initiating HTTP POST upload request to FastAPI backend. Files: ${selectedFiles.map(f=>f.name).join(", ")}. Strategy: ${mergeStrategy}`, "info");
    try {
      const res = await api.uploadDataset(selectedFiles, mergeStrategy, keyCol || undefined, how);
      setDatasetOverview(res.overview);
      setColumnRoles(res.roles);
      setAutoNarrative(res.narrative);
      setQualityScore(null); setProfilingRows([]); setCorrMatrix(null); setMlResults(null);
      addLog(`Dataset parsed successfully. Resolved shapes: ${res.overview.rows} rows x ${res.overview.columns} columns.`, "success");
    } catch (err: any) {
      const msg = err.message || "Upload failed.";
      setUploadError(msg);
      addLog(`API Upload Error: ${msg}`, "error");
    } finally {
      setIsUploading(false);
    }
  };

  const executeProfiling = async () => {
    setProfilingLoading(true);
    addLog(`Initiating Deep Profiling dataset request on core engine.`, "info");
    try {
      const res = await api.runProfile();
      setQualityScore(res.quality_score);
      setProfilingRows(res.profiling);
      setProfilingNarration(res.narration);
      setAiSummary(res.ai_summary || "");
      addLog(`Quality score matrix calculated: ${res.quality_score.score}/100. Deductions found: ${res.quality_score.details.length}.`, "success");

      const outRes = await api.runOutliers(outlierMethod);
      setOutliersSummary(outRes.summary);
      setOutliersNarration(outRes.narration);
      setOutlierDetails(outRes.details);
      const cols = Object.keys(outRes.summary);
      if (cols.length > 0) setSelectedOutlierCol(cols[0]);
      addLog(`Outlier calculations complete using ${outlierMethod} method.`, "info");
    } catch (err) {
      addLog(`Deep profiling endpoint failed.`, "error");
      console.error(err);
    } finally {
      setProfilingLoading(false);
    }
  };

  const handleOutlierMethodChange = async (method: "IQR" | "Z-Score") => {
    setOutlierMethod(method);
    addLog(`Recalculating outliers using ${method} method...`, "info");
    try {
      const outRes = await api.runOutliers(method);
      setOutliersSummary(outRes.summary);
      setOutliersNarration(outRes.narration);
      setOutlierDetails(outRes.details);
      const cols = Object.keys(outRes.summary);
      if (cols.length > 0 && !cols.includes(selectedOutlierCol)) setSelectedOutlierCol(cols[0]);
      addLog(`Outlier recalculation finished.`, "success");
    } catch (err) { console.error(err); }
  };

  const executeCorrelation = async () => {
    setCorrLoading(true);
    addLog(`Computing correlation matrices and physics force weights...`, "info");
    try {
      const res = await api.getCorrelation();
      if (res.error) {
        addLog(`Correlation error: ${res.error}`, "warning");
        alert(res.error);
        return;
      }
      setCorrCols(res.columns);
      setCorrMatrix(res.matrix);
      setPhysicsData(res.physics);
      addLog(`Physics nodes instantiated: ${res.physics.nodes.length} variables.`, "success");
    } catch (err) { console.error(err); } finally { setCorrLoading(false); }
  };

  // Simulated ML Training sequence with logs
  const simulateMLTraining = async () => {
    if (!targetCol) return;
    setShowTrainingTerminal(true);
    setMlResults(null);

    const steps: { name: string; run: () => Promise<any> }[] = [
      { name: "Fetching dataset from memory cache...", run: async () => new Promise(r => setTimeout(r, 600)) },
      { name: "Detecting task formulation...", run: async () => new Promise(r => setTimeout(r, 700)) },
      { name: "Checking class distribution / continuous values...", run: async () => new Promise(r => setTimeout(r, 600)) },
      { name: "Executing K-Fold stratification splits...", run: async () => new Promise(r => setTimeout(r, 800)) },
      { name: "Optimizing hyperparameters & grid cross-validation...", run: async () => api.trainModel(targetCol) }
    ];

    const currentLogs: MLTrainingLog[] = [];
    setTrainingLogs(currentLogs);

    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      const start = Date.now();
      currentLogs.push({ step: s.name, status: "running" });
      setTrainingLogs([...currentLogs]);

      try {
        const result = await s.run();
        const duration = ((Date.now() - start) / 1000).toFixed(2) + "s";
        currentLogs[i] = { step: s.name, status: "done", duration };
        setTrainingLogs([...currentLogs]);

        // If it was the final step, store values
        if (i === steps.length - 1) {
          setMlTask(result.ml_task);
          setMlResults(result.results);
          setMlOpinion(result.opinion);
          setBestModel(result.best_model);
          setFeatureImportance(result.feature_importance || []);
          addLog(`ML models trained successfully. Best: ${result.best_model}`, "success");
        }
      } catch (err: any) {
        currentLogs[i] = { step: s.name, status: "error" };
        setTrainingLogs([...currentLogs]);
        addLog(`ML training pipeline failed on step ${s.name}: ${err.message || err}`, "error");
        break;
      }
    }
  };

  const executeAddFlag = async () => {
    if (!flagDesc) return;
    addLog(`Adding Flag note: "${flagDesc}" (${flagType})`, "info");
    try {
      await api.addFlag(activeTab, flagType, flagDesc);
      setFlagDesc("");
      addLog(`Flag recorded on server.`, "success");
      if (insightsList.length > 0) executeInsights();
    } catch (err) { console.error(err); }
  };

  const executeInsights = async () => {
    setInsightsLoading(true);
    addLog(`Compiling executive courtroom summary insights...`, "info");
    try {
      const res = await api.getInsights();
      setInsightsList(res.insights);
      setInsightsNarrative(res.narrative);
      setFlagsList(res.flags || []);
      addLog(`Insights compiled. Generated ${res.insights.length} detailed observations.`, "success");
    } catch (err) { console.error(err); } finally { setInsightsLoading(false); }
  };

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    addLog(`Navigation: switched active page to "${tab}"`, "system");
    if (tab === "profiling" && !qualityScore && datasetOverview) executeProfiling();
    if (tab === "correlation" && !corrMatrix && datasetOverview) executeCorrelation();
    if (tab === "insights") executeInsights();
  };

  const navItems: { id: Tab; icon: React.ReactNode; label: string; badge?: string }[] = [
    { id: "upload", icon: <Upload size={15} />, label: "Data Loader" },
    { id: "profiling", icon: <BarChart3 size={15} />, label: "Profiling & Outliers" },
    { id: "correlation", icon: <Binary size={15} />, label: "Correlation Map" },
    { id: "ml", icon: <Settings size={15} />, label: "ML Engine" },
    { id: "insights", icon: <FileText size={15} />, label: "Executive Summary" },
  ];

  return (
    <div className="flex h-screen bg-black overflow-hidden relative">
      {/* Dynamic Grid Background Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#09090b_1px,transparent_1px),linear-gradient(to_bottom,#09090b_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none opacity-40" />

      {/* ── Sidebar ── */}
      <aside className="w-60 shrink-0 border-r border-zinc-900 bg-zinc-950/80 backdrop-blur flex flex-col z-10">
        {/* Brand */}
        <div className="p-5 border-b border-zinc-900">
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2.5"
          >
            <div className="relative w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-[0_0_20px_rgba(59,130,246,0.4)]">
              D
              <motion.div
                className="absolute inset-0 rounded-lg bg-blue-400/20"
                animate={{ opacity: [0, 0.5, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
            <div>
              <span className="text-sm font-bold text-white tracking-tight">DataSense AI</span>
              <p className="text-[10px] text-zinc-600">Intelligence Platform</p>
            </div>
          </motion.div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-0.5 flex-1">
          {navItems.map((item) => (
            <NavItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={activeTab === item.id}
              disabled={item.id !== "upload" && !datasetOverview}
              onClick={() => handleTabChange(item.id)}
              badge={item.badge}
            />
          ))}
        </nav>

        {/* Status footer */}
        <div className="p-4 border-t border-zinc-900">
          <div className={`flex items-center gap-2 text-xs font-medium ${datasetOverview ? "text-emerald-400" : "text-zinc-600"}`}>
            <motion.div
              className={`w-1.5 h-1.5 rounded-full ${datasetOverview ? "bg-emerald-500" : "bg-zinc-700"}`}
              animate={datasetOverview ? { opacity: [1, 0.4, 1], scale: [1, 1.2, 1] } : {}}
              transition={{ duration: 2, repeat: Infinity }}
            />
            {datasetOverview ? "Dataset Active" : "No Data Loaded"}
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="flex-1 overflow-y-auto pb-14 z-10">
        <AnimatePresence mode="wait">

          {/* ───────── UPLOAD ───────── */}
          {activeTab === "upload" && (
            <motion.div key="upload" variants={staggerContainer} initial="hidden" animate="visible" exit={{ opacity: 0 }}
              className="p-8 space-y-8 max-w-6xl mx-auto">

              <motion.div variants={fadeUpVariants}>
                <h1 className="text-2xl font-bold text-white tracking-tight">📂 Data Loader</h1>
                <p className="text-zinc-500 text-sm mt-1">Upload files to begin your intelligence pipeline.</p>
              </motion.div>

              <div className="grid grid-cols-3 gap-6">
                {/* Upload Zone */}
                <motion.div variants={fadeUpVariants} custom={1} className="col-span-2 space-y-5">
                  {/* Drop Zone */}
                  <motion.div
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    animate={{ borderColor: dragOver ? "rgba(59,130,246,0.7)" : "rgba(63,63,70,0.5)" }}
                    className="relative border border-dashed border-zinc-800 rounded-xl p-10 flex flex-col items-center justify-center text-center bg-zinc-950/80 backdrop-blur overflow-hidden cursor-pointer"
                    onClick={() => document.getElementById("file-input")?.click()}
                    whileHover={{ borderColor: "rgba(59,130,246,0.4)" }}
                    transition={{ duration: 0.2 }}
                  >
                    {/* Background animation */}
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-br from-blue-950/10 to-indigo-950/10"
                      animate={{ opacity: dragOver ? 1 : 0 }}
                      transition={{ duration: 0.3 }}
                    />

                    <motion.div
                      animate={dragOver ? { scale: 1.1, color: "#3B82F6" } : { scale: 1 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      className="text-zinc-600 mb-4 relative z-10"
                    >
                      <Upload size={40} strokeWidth={1.5} />
                    </motion.div>

                    <p className="text-sm font-medium text-zinc-300 relative z-10">
                      {dragOver ? "Drop files here" : "Drag & drop files, or click to browse"}
                    </p>
                    <p className="text-xs text-zinc-600 mt-1 relative z-10">CSV, Excel, JSON, Parquet supported</p>

                    <input id="file-input" type="file" multiple accept=".csv,.xlsx,.xls,.json,.parquet"
                      onChange={e => {
                        if (e.target.files && e.target.files.length > 0) {
                          const files = Array.from(e.target.files);
                          setSelectedFiles(files);
                          addLog(`Manual file selection: selected ${files.length} file(s).`, "info");
                        }
                      }}
                      className="hidden" />
                  </motion.div>

                  {/* Selected files */}
                  <AnimatePresence>
                    {selectedFiles.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-4"
                      >
                        <div className="flex gap-2 flex-wrap">
                          {selectedFiles.map((f, i) => (
                            <motion.div
                              key={f.name}
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: i * 0.05 }}
                              className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs animate-pulse-once"
                            >
                              <FileText size={12} className="text-blue-400" />
                              <span className="text-zinc-300 font-medium truncate max-w-[140px]">{f.name}</span>
                              <span className="text-zinc-600">{(f.size / 1024).toFixed(0)}KB</span>
                            </motion.div>
                          ))}
                        </div>

                        {selectedFiles.length > 1 && (
                          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-4">
                            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5"><Layers size={12} />Merge Settings</p>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="block text-[11px] text-zinc-500 mb-1.5">Strategy</label>
                                <select value={mergeStrategy} onChange={e => { setMergeStrategy(e.target.value); addLog(`Changed merge strategy to ${e.target.value}`, "info"); }}
                                  className="w-full bg-zinc-900 border border-zinc-800 text-sm rounded-lg p-2.5 text-zinc-300 focus:border-blue-500 focus:outline-none">
                                  <option>Stack (Union)</option>
                                  <option>Join on Key</option>
                                </select>
                              </div>
                              {mergeStrategy === "Join on Key" && (
                                <div>
                                  <label className="block text-[11px] text-zinc-500 mb-1.5">Join Type</label>
                                  <select value={how} onChange={e => setHow(e.target.value)}
                                    className="w-full bg-zinc-900 border border-zinc-800 text-sm rounded-lg p-2.5 text-zinc-300 focus:border-blue-500 focus:outline-none">
                                    <option value="inner">Inner</option>
                                    <option value="left">Left</option>
                                    <option value="outer">Outer</option>
                                  </select>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="flex justify-end">
                          <motion.button
                            onClick={executeUpload} disabled={isUploading}
                            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-sm px-6 py-2.5 rounded-lg flex items-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] transition-all duration-300"
                          >
                            {isUploading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                            {isUploading ? "Analyzing…" : "Analyze Dataset"}
                          </motion.button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {uploadError && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      className="bg-red-950/20 border border-red-900/50 text-red-400 text-sm p-4 rounded-xl flex items-start gap-2">
                      <AlertCircle size={16} className="shrink-0 mt-0.5" />
                      {uploadError}
                    </motion.div>
                  )}
                </motion.div>

                {/* Stats sidebar */}
                <motion.div variants={fadeUpVariants} custom={2}>
                  <AnimatePresence mode="wait">
                    {datasetOverview ? (
                      <motion.div
                        key="stats"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="space-y-4"
                      >
                        <motion.div variants={staggerContainer} initial="hidden" animate="visible"
                          className="grid grid-cols-2 gap-3">
                          <KpiCard title="Rows" value={datasetOverview.rows} icon={<Activity size={13} />} />
                          <KpiCard title="Columns" value={datasetOverview.columns} icon={<Database size={13} />} />
                          <KpiCard title="Missing" value={datasetOverview.missing_pct} suffix="%" icon={<AlertCircle size={13} />} />
                          <KpiCard title="Duplicates" value={datasetOverview.duplicate_rows} icon={<Layers size={13} />} />
                        </motion.div>

                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.4 }}
                          className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 space-y-3"
                        >
                          <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-zinc-500 flex items-center gap-1.5">
                            <Brain size={11} /> AutoNarrate
                          </p>
                          <p className="text-xs text-zinc-400 leading-relaxed italic border-l-2 border-blue-900 pl-3">
                            "{autoNarrative}"
                          </p>
                        </motion.div>

                        <motion.button
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.6 }}
                          onClick={() => handleTabChange("profiling")}
                          whileHover={{ x: 4 }}
                          className="w-full flex items-center justify-between p-3.5 bg-blue-950/20 border border-blue-900/40 rounded-xl text-sm text-blue-400 font-medium hover:bg-blue-950/30 transition-colors duration-200"
                        >
                          <span>Run Deep Profiling</span>
                          <ArrowRight size={14} />
                        </motion.button>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="bg-zinc-950 border border-zinc-900 rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[280px]"
                      >
                        <motion.div
                          animate={{ y: [0, -4, 0] }}
                          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                        >
                          <Database size={36} className="text-zinc-800 mb-3" />
                        </motion.div>
                        <p className="text-xs text-zinc-600">Upload a dataset to see live statistics and AutoNarrate insights here.</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </div>

              {/* Data Preview Table */}
              <AnimatePresence>
                {previewData && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden"
                  >
                    <div className="p-4 border-b border-zinc-900 flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Dataset Preview</p>
                      <span className="text-[11px] text-zinc-600 font-mono">First 60 rows</span>
                    </div>
                    <div className="overflow-x-auto max-h-72">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="sticky top-0 bg-zinc-900 text-zinc-400 uppercase font-semibold tracking-wider border-b border-zinc-800">
                          <tr>
                            {previewData.columns.map((col: string) => (
                              <th key={col} className="p-3 border-r border-zinc-800 font-mono whitespace-nowrap">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900 font-mono">
                          {previewData.preview.map((row: any, i: number) => (
                            <motion.tr
                              key={i}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: i * 0.01 }}
                              className="hover:bg-zinc-900/40 transition-colors"
                            >
                              {previewData.columns.map((col: string) => (
                                <td key={col} className="p-3 border-r border-zinc-900 text-zinc-400 max-w-[180px] truncate">{String(row[col])}</td>
                              ))}
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* ───────── PROFILING ───────── */}
          {activeTab === "profiling" && (
            <motion.div key="profiling" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="p-8 space-y-8 max-w-6xl mx-auto">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">📊 Profiling & Outliers</h1>
                <p className="text-zinc-500 text-sm mt-1">Deep analysis of data quality, null rates, and anomaly distribution.</p>
              </div>

              {profilingLoading ? (
                <LoadingOverlay label="Computing column profiles and quality matrices…" />
              ) : (
                <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-8">
                  {qualityScore && (
                    <motion.div variants={fadeUpVariants} className="grid grid-cols-3 gap-6">
                      <div className="bg-zinc-950 border border-zinc-900 rounded-xl flex items-center justify-center">
                        <QualityGauge score={qualityScore.score} />
                      </div>
                      <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Quality Analysis & Deductions</p>
                        <div className="space-y-2">
                          {qualityScore.details?.length > 0 ? (
                            qualityScore.details.map((d: string, idx: number) => (
                              <motion.div key={idx}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.07 }}
                                className="flex items-start gap-2.5 text-xs text-zinc-400 bg-amber-950/10 border border-amber-900/30 p-3 rounded-lg"
                              >
                                <AlertCircle size={13} className="text-amber-500 mt-0.5 shrink-0" />
                                {d}
                              </motion.div>
                            ))
                          ) : (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                              className="flex items-center gap-2.5 text-sm text-emerald-400 bg-emerald-950/10 border border-emerald-900/30 p-4 rounded-xl">
                              <CheckCircle2 size={16} />
                              No deductions — dataset is in pristine condition!
                            </motion.div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {profilingRows.length > 0 && (
                    <motion.div variants={fadeUpVariants} className="grid grid-cols-3 gap-6">
                      <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-zinc-900">
                          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Column Profiling Matrix</p>
                        </div>
                        <div className="overflow-x-auto max-h-64">
                          <table className="w-full text-left text-xs border-collapse">
                            <thead className="sticky top-0 bg-zinc-900 text-zinc-400 uppercase tracking-wider border-b border-zinc-800">
                              <tr>
                                {["Column", "Type", "Unique", "Nulls", "Null %"].map(h => (
                                  <th key={h} className="p-3 border-r border-zinc-800 font-semibold">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-900 font-mono">
                              {profilingRows.map((row: any, i: number) => (
                                <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                  transition={{ delay: i * 0.02 }} className="hover:bg-zinc-900/40 transition-colors">
                                  <td className="p-3 border-r border-zinc-900 text-zinc-200 font-medium font-sans">{row.Column}</td>
                                  <td className="p-3 border-r border-zinc-900 text-zinc-500">{row.Type}</td>
                                  <td className="p-3 border-r border-zinc-900 text-zinc-400">{row.Unique}</td>
                                  <td className="p-3 border-r border-zinc-900 text-zinc-400">{row.Nulls}</td>
                                  <td className="p-3 border-r border-zinc-900">
                                    <div className="flex items-center gap-2">
                                      <div className="flex-1 h-1 bg-zinc-900 rounded-full overflow-hidden max-w-16">
                                        <motion.div
                                          className={`h-full rounded-full ${parseFloat(row["Null %"]) > 20 ? "bg-red-500" : parseFloat(row["Null %"]) > 5 ? "bg-amber-500" : "bg-emerald-500"}`}
                                          initial={{ width: 0 }}
                                          animate={{ width: `${Math.min(parseFloat(row["Null %"]), 100)}%` }}
                                          transition={{ duration: 0.8, delay: i * 0.03 }}
                                        />
                                      </div>
                                      <span className="text-zinc-500">{row["Null %"]}%</span>
                                    </div>
                                  </td>
                                </motion.tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <div className="space-y-4">
                        {aiSummary && (
                          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                            className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-3">
                            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                              <motion.div className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                                animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.5, repeat: Infinity }} />
                              AI Auto-Summary
                            </p>
                            <p className="text-xs text-zinc-300 leading-relaxed border-l-2 border-blue-900 pl-3">{aiSummary}</p>
                          </motion.div>
                        )}
                        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-3">
                          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Column Summary</p>
                          <p className="text-xs text-zinc-500 leading-relaxed">{profilingNarration}</p>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Outliers */}
                  {outliersSummary && (
                    <motion.div variants={fadeUpVariants} className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
                      <div className="p-5 border-b border-zinc-900 flex items-center justify-between">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">🚨 Outlier Detection Analysis</p>
                        <div className="flex gap-1">
                          {(["IQR", "Z-Score"] as const).map(m => (
                            <button key={m} onClick={() => handleOutlierMethodChange(m)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${outlierMethod === m ? "bg-zinc-900 text-white border border-zinc-800" : "text-zinc-600 hover:text-zinc-400"}`}>
                              {m}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="p-5 grid grid-cols-3 gap-6">
                        <div className="col-span-2 space-y-4">
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-zinc-500 uppercase font-semibold tracking-wider">Inspect:</span>
                            <select value={selectedOutlierCol} onChange={e => { setSelectedOutlierCol(e.target.value); addLog(`Selected outlier inspection column: ${e.target.value}`, "info"); }}
                              className="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-300 focus:outline-none">
                              {Object.keys(outliersSummary).map(col => (
                                <option key={col} value={col}>{col} ({outliersSummary[col]} outliers)</option>
                              ))}
                            </select>
                          </div>

                          {selectedOutlierCol && outlierDetails?.[selectedOutlierCol]?.length > 0 ? (
                            <div className="overflow-x-auto border border-zinc-900 rounded-lg max-h-60">
                              <table className="w-full text-xs font-mono border-collapse">
                                <thead className="sticky top-0 bg-zinc-900 border-b border-zinc-800">
                                  <tr>
                                    {datasetOverview.numeric_col_names.map((c: string) => (
                                      <th key={c} className="p-2.5 border-r border-zinc-800 text-zinc-400 font-semibold text-left">{c}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-zinc-900">
                                  {outlierDetails[selectedOutlierCol].slice(0, 10).map((row: any, i: number) => (
                                    <tr key={i} className="hover:bg-zinc-900/40 transition-colors">
                                      {datasetOverview.numeric_col_names.map((c: string) => (
                                        <td key={c} className="p-2.5 border-r border-zinc-900 text-zinc-500">{String(row[c])}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p className="text-xs text-zinc-600 italic py-4">No outliers found in this column.</p>
                          )}
                        </div>

                        <div className="space-y-4">
                          <div className="bg-zinc-900/40 border border-zinc-900 p-4 rounded-xl">
                            <p className="text-[11px] text-zinc-500 font-semibold mb-2">Narration</p>
                            <p className="text-xs text-zinc-400 leading-relaxed">{outliersNarration}</p>
                          </div>
                          <div className="border border-zinc-900 bg-zinc-950 p-4 rounded-xl space-y-3">
                            <p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Flag Observation</p>
                            <input type="text" value={flagDesc} onChange={e => setFlagDesc(e.target.value)} placeholder="Describe what you observe…"
                              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-700 transition-colors" />
                            <select value={flagType} onChange={e => setFlagType(e.target.value)}
                              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-xs text-zinc-300 focus:outline-none">
                              <option value="anomaly">Anomaly</option>
                              <option value="pattern">Pattern</option>
                              <option value="question">Question</option>
                              <option value="domain knowledge">Domain Knowledge</option>
                            </select>
                            <motion.button onClick={executeAddFlag} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
                              className="w-full bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 text-xs font-semibold py-2 rounded-lg transition-colors">
                              Add Flag
                            </motion.button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}

          {/* ───────── CORRELATION ───────── */}
          {activeTab === "correlation" && (
            <motion.div key="correlation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="p-8 space-y-6 max-w-6xl mx-auto">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">🌌 Correlation Map</h1>
                  <p className="text-zinc-500 text-sm mt-1">Force-directed physics visualization of variable relationships.</p>
                </div>
                <div className="flex gap-1.5">
                  {(["universe", "heatmap"] as const).map(t => (
                    <button key={t} onClick={() => setCorrTab(t)}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${corrTab === t ? "bg-zinc-900 text-white border-zinc-700" : "text-zinc-600 border-transparent hover:text-zinc-400"}`}>
                      {t === "universe" ? "🌌 Physics" : "📊 Matrix"}
                    </button>
                  ))}
                </div>
              </div>

              {corrLoading ? (
                <LoadingOverlay label="Computing correlation weights and physics nodes…" />
              ) : (
                <>
                  {physicsData && corrTab === "universe" && (
                    <PhysicsUniverse nodes={physicsData.nodes} edges={physicsData.edges} />
                  )}
                  {corrMatrix && corrTab === "heatmap" && (
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
                      className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
                      <div className="p-4 border-b border-zinc-900">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Correlation Coefficients Matrix</p>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-center text-xs border-collapse">
                          <thead className="bg-zinc-900 border-b border-zinc-800">
                            <tr>
                              <th className="p-3 border-r border-zinc-800 text-left text-zinc-400 font-semibold">Variable</th>
                              {corrCols.map(c => (
                                <th key={c} className="p-3 border-r border-zinc-800 text-zinc-500 font-mono truncate max-w-[70px]">{c}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-900 font-mono">
                            {corrCols.map(row => (
                              <tr key={row} className="hover:bg-zinc-900/30 transition-colors">
                                <td className="p-3 border-r border-zinc-900 text-left text-zinc-300 font-medium font-sans">{row}</td>
                                {corrCols.map(col => {
                                  const val = corrMatrix[row]?.[col] ?? 0;
                                  const abs = Math.abs(val);
                                  const bg = abs > 0.7 ? (val > 0 ? "bg-blue-950/60 text-blue-300" : "bg-red-950/60 text-red-300") :
                                    abs > 0.4 ? (val > 0 ? "bg-blue-950/30 text-blue-400" : "bg-red-950/30 text-red-400") : "text-zinc-600";
                                  return <td key={col} className={`p-3 border-r border-zinc-900 ${bg}`}>{val.toFixed(2)}</td>;
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </motion.div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {/* ───────── ML ENGINE ───────── */}
          {activeTab === "ml" && (
            <motion.div key="ml" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="p-8 space-y-8 max-w-6xl mx-auto">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">⚙️ Machine Learning Engine</h1>
                <p className="text-zinc-500 text-sm mt-1">Auto task detection, multi-model training, and explainability.</p>
              </div>

              {!showTrainingTerminal && !mlResults && (
                <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-3">
                    <Target size={15} className="text-zinc-500" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Target Variable</span>
                  </div>
                  <select value={targetCol} onChange={e => setTargetCol(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 text-sm rounded-lg px-3 py-2 text-zinc-300 focus:outline-none focus:border-blue-600 min-w-[200px]">
                    <option value="">— Select target column —</option>
                    {columnRoles && Object.keys(columnRoles).map(col => (
                      <option key={col} value={col}>{col} ({columnRoles[col]})</option>
                    ))}
                  </select>
                  <motion.button onClick={simulateMLTraining} disabled={!targetCol || mlLoading}
                    whileHover={targetCol && !mlLoading ? { scale: 1.02 } : {}} whileTap={targetCol && !mlLoading ? { scale: 0.98 } : {}}
                    className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold text-sm px-5 py-2 rounded-lg flex items-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all">
                    <PlayCircle size={14} />
                    <span>Run ML Pipeline</span>
                  </motion.button>
                </div>
              )}

              {showTrainingTerminal && !mlResults && (
                <div className="py-8">
                  <TrainingTerminal
                    logs={trainingLogs}
                    targetCol={targetCol}
                    onComplete={() => {
                      setShowTrainingTerminal(false);
                    }}
                  />
                </div>
              )}

              {mlResults && !showTrainingTerminal && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-3 gap-6">
                  <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
                    <div className="p-5 border-b border-zinc-900 flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Model Evaluation Matrix</p>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-blue-400 font-mono uppercase tracking-wider">{mlTask} detected</span>
                        <button
                          onClick={() => { setMlResults(null); setTargetCol(""); }}
                          className="text-[10px] text-zinc-500 hover:text-zinc-300 uppercase tracking-wider font-semibold border border-zinc-800 px-2 py-1 rounded"
                        >
                          Retrain
                        </button>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-zinc-900 border-b border-zinc-800">
                          <tr>
                            <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">Model</th>
                            {mlTask === "classification" ? (
                              <>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">Accuracy</th>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">F1 Score</th>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">ROC-AUC</th>
                              </>
                            ) : mlTask === "regression" ? (
                              <>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">R²</th>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">MAE</th>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">RMSE</th>
                              </>
                            ) : (
                              <>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">Silhouette</th>
                                <th className="p-3.5 border-r border-zinc-800 text-zinc-400 font-semibold">Clusters (k)</th>
                              </>
                            )}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900 font-mono">
                          {Object.keys(mlResults).map((name, i) => {
                            const m = mlResults[name];
                            const isBest = name === bestModel;
                            return (
                              <motion.tr key={name}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.08 }}
                                className={`hover:bg-zinc-900/40 transition-colors ${isBest ? "bg-blue-950/10" : ""}`}>
                                <td className="p-3.5 border-r border-zinc-900 text-zinc-200 font-medium font-sans flex items-center gap-2">
                                  {isBest && <Star size={11} className="text-blue-400 shrink-0" />}
                                  {name}
                                  {isBest && <span className="text-[10px] bg-blue-600/20 border border-blue-500/30 text-blue-400 px-1.5 py-0.5 rounded font-mono ml-1">BEST</span>}
                                </td>
                                {mlTask === "classification" ? (
                                  <>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["Accuracy"]?.toFixed ? m["Accuracy"].toFixed(4) : "N/A"}</td>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["F1 (weighted)"]?.toFixed ? m["F1 (weighted)"].toFixed(4) : "N/A"}</td>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["ROC-AUC"]?.toFixed ? m["ROC-AUC"].toFixed(4) : "N/A"}</td>
                                  </>
                                ) : mlTask === "regression" ? (
                                  <>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["R²"]?.toFixed ? m["R²"].toFixed(4) : "N/A"}</td>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["MAE"]?.toFixed ? m["MAE"].toFixed(4) : "N/A"}</td>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m["RMSE"]?.toFixed ? m["RMSE"].toFixed(4) : "N/A"}</td>
                                  </>
                                ) : (
                                  <>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m.silhouette?.toFixed(4) ?? "N/A"}</td>
                                    <td className="p-3.5 border-r border-zinc-900 text-zinc-400">{m.k ?? "N/A"}</td>
                                  </>
                                )}
                              </motion.tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Opinion + Feature Importance */}
                  <div className="space-y-5">
                    {mlOpinion && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                        className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-3">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5"><Brain size={11} />Strategy Opinion</p>
                        <p className="text-xs text-zinc-400 leading-relaxed border-l-2 border-blue-900 pl-3">{mlOpinion}</p>
                      </motion.div>
                    )}

                    {featureImportance.length > 0 && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
                        className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Variable Importance</p>
                        <div className="space-y-3">
                          {featureImportance.slice(0, 7).map((item, i) => (
                            <ProgressBar key={i} label={item.Feature} value={item.Importance} max={1} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

          {/* ───────── INSIGHTS ───────── */}
          {activeTab === "insights" && (
            <motion.div key="insights" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="p-8 space-y-8 max-w-6xl mx-auto">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">💡 Executive Summary</h1>
                <p className="text-zinc-500 text-sm mt-1">Unified analytics matrix with automated insights and human annotations.</p>
              </div>

              {insightsLoading ? (
                <LoadingOverlay label="Synthesizing observations and building report…" />
              ) : (
                <div className="grid grid-cols-3 gap-6">
                  <div className="col-span-2 space-y-6">
                    {/* KPI snapshot */}
                    {datasetOverview && (
                      <motion.div variants={staggerContainer} initial="hidden" animate="visible"
                        className="grid grid-cols-4 gap-3">
                        <KpiCard title="Rows" value={datasetOverview.rows} icon={<Activity size={12} />} />
                        <KpiCard title="Columns" value={datasetOverview.columns} icon={<Database size={12} />} />
                        <KpiCard title="Missing" value={datasetOverview.missing_pct} suffix="%" icon={<AlertCircle size={12} />} />
                        <KpiCard title="Best Model" value={bestModel || "N/A"} icon={<Star size={12} />} />
                      </motion.div>
                    )}

                    {insightsNarrative && (
                      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
                        className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Boardroom Narrative</p>
                        <div className="text-sm text-zinc-300 leading-loose border-l-2 border-blue-900 pl-4 italic">
                          {insightsNarrative}
                        </div>
                      </motion.div>
                    )}

                    {insightsList.length > 0 && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
                        className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-3">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Core Observations ({insightsList.length})</p>
                        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-2">
                          {insightsList.map((ins, i) => <InsightChip key={i} text={ins} index={i} />)}
                        </motion.div>
                      </motion.div>
                    )}
                  </div>

                  <div className="space-y-5">
                    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">🚩 Pipeline Flags</p>
                      {flagsList.length > 0 ? (
                        <motion.div className="space-y-3" variants={staggerContainer} initial="hidden" animate="visible">
                          {flagsList.map((flag, i) => (
                            <motion.div key={i} variants={fadeUpVariants} custom={i}
                              className="bg-zinc-900/40 border border-zinc-900 p-3.5 rounded-xl space-y-2">
                              <div className="flex justify-between items-center">
                                <span className="text-[10px] bg-red-600/20 border border-red-500/20 text-red-400 px-1.5 py-0.5 rounded font-mono uppercase">{flag.type}</span>
                                <span className="text-[10px] text-zinc-600 capitalize">{flag.page}</span>
                              </div>
                              <p className="text-xs text-zinc-300 leading-relaxed">{flag.description}</p>
                            </motion.div>
                          ))}
                        </motion.div>
                      ) : (
                        <div className="flex flex-col items-center text-center py-10 text-zinc-700">
                          <AlertCircle size={26} className="mb-2 text-zinc-800" />
                          <p className="text-xs">No flags noted yet. Add observations in the Profiling tab.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* Floating Terminal Console Drawer */}
      <InteractiveConsole logs={consoleLogs} onClear={() => setConsoleLogs([])} />
    </div>
  );
}
