"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Upload, BarChart3, Binary, Settings, AlertCircle, CheckCircle2, 
  HelpCircle, Database, FileSpreadsheet, Play, Layers, RefreshCw, 
  Trash2, Copy, FileText, ChevronRight, RefreshRight, Info
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import * as api from "../lib/api";

// ─────────────────────────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

// 1. Animated Count Up Number Ticker
interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
}
function AnimatedCounter({ value, prefix = "", suffix = "", duration = 1000 }: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTimestamp: number | null = null;
    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setDisplayValue(eased * value);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        setDisplayValue(value);
      }
    };
    window.requestAnimationFrame(step);
  }, [value, duration]);

  const formatted = value % 1 === 0 ? Math.floor(displayValue).toLocaleString() : displayValue.toFixed(2);
  return (
    <span>
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
}

// 2. Neon SVG Circular Quality Gauge
interface QualityGaugeProps {
  score: number;
  label?: string;
}
function QualityGauge({ score, label = "Quality Score" }: QualityGaugeProps) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let color = "stroke-red-500";
  if (score >= 50 && score < 80) color = "stroke-amber-500";
  else if (score >= 80) color = "stroke-emerald-500";

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-40 h-40 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          {/* Background circle */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            className="stroke-zinc-800 fill-none"
            strokeWidth="10"
          />
          {/* Progress circle */}
          <motion.circle
            cx="80"
            cy="80"
            r={radius}
            className={`fill-none ${color} transition-all duration-1000 ease-out`}
            strokeWidth="10"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-4xl font-semibold tracking-tight text-white">
            <AnimatedCounter value={score} />
          </span>
          <span className="text-xs text-zinc-500 mt-0.5">/ 100</span>
        </div>
      </div>
      <span className="mt-4 text-sm font-medium uppercase tracking-wider text-zinc-400">{label}</span>
    </div>
  );
}

// 3. Force-Directed Physics Network Diagram (Canvas)
interface PhysicsUniverseProps {
  nodes: { label: string }[];
  edges: { source: number; target: number; strength: number }[];
}
function PhysicsUniverse({ nodes: initialNodes, edges: initialEdges }: PhysicsUniverseProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = container.clientWidth || 600;
    const height = 450;
    canvas.width = width;
    canvas.height = height;

    // Node state wrapper
    const nodes = initialNodes.map((n, i) => ({
      id: i,
      label: n.label,
      x: width / 2 + (Math.random() - 0.5) * width * 0.4,
      y: height / 2 + (Math.random() - 0.5) * height * 0.4,
      vx: 0,
      vy: 0,
      r: 6,
    }));

    const REPULSION = 2500;
    const SPRING = 0.03;
    const DAMPING = 0.8;
    const CENTER_PULL = 0.005;

    let dragNode: typeof nodes[0] | null = null;
    let ox = 0, oy = 0;

    const handleResize = () => {
      width = container.clientWidth || 600;
      canvas.width = width;
    };
    window.addEventListener("resize", handleResize);

    let animationFrameId: number;

    const updatePhysics = () => {
      const cx = width / 2;
      const cy = height / 2;

      // Center Pull
      nodes.forEach(n => {
        n.vx += (cx - n.x) * CENTER_PULL;
        n.vy += (cy - n.y) * CENTER_PULL;
      });

      // Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const d2 = dx * dx + dy * dy + 1;
          const d = Math.sqrt(d2);
          const f = REPULSION / d2;
          nodes[i].vx -= (dx / d) * f;
          nodes[i].vy -= (dy / d) * f;
          nodes[j].vx += (dx / d) * f;
          nodes[j].vy += (dy / d) * f;
        }
      }

      // Spring forces for edges
      initialEdges.forEach(e => {
        const a = nodes[e.source];
        const b = nodes[e.target];
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) + 1;
        const ideal = 160 - Math.abs(e.strength) * 90;
        const f = SPRING * (d - ideal) * Math.abs(e.strength);
        a.vx += (dx / d) * f;
        a.vy += (dy / d) * f;
        b.vx -= (dx / d) * f;
        b.vy -= (dy / d) * f;
      });

      // Update positions
      nodes.forEach(n => {
        if (n === dragNode) return;
        n.vx *= DAMPING;
        n.vy *= DAMPING;
        n.x += n.vx;
        n.y += n.vy;

        // Keep inside bounds
        n.x = Math.max(n.r + 5, Math.min(width - n.r - 5, n.x));
        n.y = Math.max(n.r + 5, Math.min(height - n.r - 5, n.y));
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw Edges
      initialEdges.forEach(e => {
        const a = nodes[e.source];
        const b = nodes[e.target];
        if (!a || !b) return;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);

        const alpha = 0.15 + Math.abs(e.strength) * 0.45;
        ctx.strokeStyle = e.strength > 0 
          ? `rgba(59, 130, 246, ${alpha})` // Blue for positive
          : `rgba(239, 68, 68, ${alpha})`; // Red for negative
        ctx.lineWidth = 1 + Math.abs(e.strength) * 2;
        ctx.stroke();
      });

      // Draw Nodes
      nodes.forEach(n => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n === dragNode ? "#3B82F6" : "#EDEDED";
        
        if (n === dragNode) {
          ctx.shadowColor = "#3B82F6";
          ctx.shadowBlur = 12;
        } else {
          ctx.shadowBlur = 0;
        }
        
        ctx.fill();
        ctx.shadowBlur = 0;

        // Node Label
        ctx.fillStyle = "#A1A1AA";
        ctx.font = "500 11px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(n.label, n.x, n.y + 10);
      });
    };

    const tick = () => {
      updatePhysics();
      draw();
      animationFrameId = requestAnimationFrame(tick);
    };
    tick();

    // Drag handlers
    const getPos = (e: MouseEvent | TouchEvent) => {
      const rect = canvas.getBoundingClientRect();
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      return {
        x: clientX - rect.left,
        y: clientY - rect.top,
      };
    };

    const onStart = (pos: { x: number; y: number }) => {
      dragNode = nodes.find(n => Math.hypot(n.x - pos.x, n.y - pos.y) < 18) || null;
      if (dragNode) {
        ox = dragNode.x - pos.x;
        oy = dragNode.y - pos.y;
      }
    };

    const onMove = (pos: { x: number; y: number }) => {
      if (dragNode) {
        dragNode.x = pos.x + ox;
        dragNode.y = pos.y + oy;
      }
    };

    const onEnd = () => {
      dragNode = null;
    };

    const mdown = (e: MouseEvent) => onStart(getPos(e));
    const mmove = (e: MouseEvent) => onMove(getPos(e));
    const mup = () => onEnd();
    
    const tstart = (e: TouchEvent) => onStart(getPos(e));
    const tmove = (e: TouchEvent) => onMove(getPos(e));
    const tend = () => onEnd();

    canvas.addEventListener("mousedown", mdown);
    window.addEventListener("mousemove", mmove);
    window.addEventListener("mouseup", mup);

    canvas.addEventListener("touchstart", tstart);
    window.addEventListener("touchmove", tmove);
    window.addEventListener("touchend", tend);

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener("mousedown", mdown);
      window.removeEventListener("mousemove", mmove);
      window.removeEventListener("mouseup", mup);
      canvas.removeEventListener("touchstart", tstart);
      window.removeEventListener("touchmove", tmove);
      window.removeEventListener("touchend", tend);
    };
  }, [initialNodes, initialEdges]);

  return (
    <div ref={containerRef} className="relative w-full h-[450px] bg-zinc-950 border border-zinc-900 rounded-lg overflow-hidden flex items-center justify-center">
      <canvas ref={canvasRef} className="cursor-grab active:cursor-grabbing w-full h-full" />
      <div className="absolute bottom-4 left-4 font-sans text-xs text-zinc-500 flex gap-4">
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>Positive</div>
        <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>Negative</div>
        <div className="flex items-center gap-1.5 text-zinc-400">Draggable Nodes</div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
  const [activeTab, setActiveTab] = useState<"upload" | "profiling" | "correlation" | "ml" | "insights">("upload");
  
  // App states
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [mergeStrategy, setMergeStrategy] = useState("Stack (Union)");
  const [keyCol, setKeyCol] = useState("");
  const [how, setHow] = useState("inner");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [datasetOverview, setDatasetOverview] = useState<any>(null);
  const [columnRoles, setColumnRoles] = useState<any>(null);
  const [autoNarrative, setAutoNarrative] = useState("");
  const [previewData, setPreviewData] = useState<any>(null);

  // Profiling page states
  const [profilingLoading, setProfilingLoading] = useState(false);
  const [qualityScore, setQualityScore] = useState<any>(null);
  const [profilingRows, setProfilingRows] = useState<any[]>([]);
  const [profilingNarration, setProfilingNarration] = useState("");
  const [aiSummary, setAiSummary] = useState("");
  
  // Outliers
  const [outlierMethod, setOutlierMethod] = useState<"IQR" | "Z-Score">("IQR");
  const [outliersSummary, setOutliersSummary] = useState<any>(null);
  const [outliersNarration, setOutliersNarration] = useState("");
  const [outlierDetails, setOutlierDetails] = useState<any>(null);
  const [selectedOutlierCol, setSelectedOutlierCol] = useState("");
  
  // Outlier Flag
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

  // Insights Page
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsList, setInsightsList] = useState<string[]>([]);
  const [insightsNarrative, setInsightsNarrative] = useState("");
  const [flagsList, setFlagsList] = useState<any[]>([]);
  
  // Load preview once uploaded
  useEffect(() => {
    if (datasetOverview) {
      api.getPreview(50).then(res => setPreviewData(res)).catch(console.error);
    }
  }, [datasetOverview]);

  // Handle file drop/select
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const executeUpload = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);
    setUploadError("");
    try {
      const res = await api.uploadDataset(selectedFiles, mergeStrategy, keyCol || undefined, how);
      setDatasetOverview(res.overview);
      setColumnRoles(res.roles);
      setAutoNarrative(res.narrative);
      // Reset subsequent states
      setQualityScore(null);
      setProfilingRows([]);
      setCorrMatrix(null);
      setMlResults(null);
    } catch (err: any) {
      setUploadError(err.message || "Something went wrong.");
    } finally {
      setIsUploading(false);
    }
  };

  // Run profiling
  const executeProfiling = async () => {
    setProfilingLoading(true);
    try {
      const res = await api.runProfile();
      setQualityScore(res.quality_score);
      setProfilingRows(res.profiling);
      setProfilingNarration(res.narration);
      setAiSummary(res.ai_summary);

      // Pre-fetch outliers
      const outRes = await api.runOutliers(outlierMethod);
      setOutliersSummary(outRes.summary);
      setOutliersNarration(outRes.narration);
      setOutlierDetails(outRes.details);
      const cols = Object.keys(outRes.summary);
      if (cols.length > 0) {
        setSelectedOutlierCol(cols[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setProfilingLoading(false);
    }
  };

  const handleOutlierMethodChange = async (method: "IQR" | "Z-Score") => {
    setOutlierMethod(method);
    try {
      const outRes = await api.runOutliers(method);
      setOutliersSummary(outRes.summary);
      setOutliersNarration(outRes.narration);
      setOutlierDetails(outRes.details);
      const cols = Object.keys(outRes.summary);
      if (cols.length > 0 && !cols.includes(selectedOutlierCol)) {
        setSelectedOutlierCol(cols[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Run correlation
  const executeCorrelation = async () => {
    setCorrLoading(true);
    try {
      const res = await api.getCorrelation();
      if (res.error) {
        alert(res.error);
        return;
      }
      setCorrCols(res.columns);
      setCorrMatrix(res.matrix);
      setPhysicsData(res.physics);
    } catch (err) {
      console.error(err);
    } finally {
      setCorrLoading(false);
    }
  };

  // Run ML
  const executeTrain = async () => {
    if (!targetCol) return;
    setMlLoading(true);
    try {
      const res = await api.trainModel(targetCol);
      setMlTask(res.ml_task);
      setMlResults(res.results);
      setMlOpinion(res.opinion);
      setBestModel(res.best_model);
      setFeatureImportance(res.feature_importance || []);
    } catch (err) {
      console.error(err);
    } finally {
      setMlLoading(false);
    }
  };

  // Add Flag
  const executeAddFlag = async () => {
    if (!flagDesc) return;
    try {
      await api.addFlag(activeTab, flagType, flagDesc);
      setFlagDesc("");
      // Refresh insights if loaded
      if (insightsList.length > 0) {
        executeInsights();
      }
      alert("Flag added successfully!");
    } catch (err) {
      console.error(err);
    }
  };

  // Run Insights
  const executeInsights = async () => {
    setInsightsLoading(true);
    try {
      const res = await api.getInsights();
      setInsightsList(res.insights);
      setInsightsNarrative(res.narrative);
      setFlagsList(res.flags || []);
    } catch (err) {
      console.error(err);
    } finally {
      setInsightsLoading(false);
    }
  };

  // Intersection columns for merge strategy
  const commonColumns = datasetOverview?.numeric_col_names || [];

  return (
    <div className="flex h-screen bg-black overflow-hidden font-sans">
      {/* ── Left Navigation Sidebar ── */}
      <aside className="w-64 border-r border-zinc-900 bg-zinc-950 flex flex-col justify-between">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center font-bold text-white text-base">
              D
            </div>
            <span className="font-bold text-lg tracking-tight text-white">DataSense AI</span>
          </div>

          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab("upload")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === "upload" 
                  ? "bg-zinc-900 text-white border-l-2 border-blue-500 pl-[14px]" 
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200"
              }`}
            >
              <Upload size={16} />
              <span>Data Loader</span>
            </button>
            <button
              onClick={() => { setActiveTab("profiling"); if (!qualityScore && datasetOverview) executeProfiling(); }}
              disabled={!datasetOverview}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                !datasetOverview ? "opacity-40 cursor-not-allowed" : ""
              } ${
                activeTab === "profiling" 
                  ? "bg-zinc-900 text-white border-l-2 border-blue-500 pl-[14px]" 
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200"
              }`}
            >
              <BarChart3 size={16} />
              <span>Profiling & Outliers</span>
            </button>
            <button
              onClick={() => { setActiveTab("correlation"); if (!corrMatrix && datasetOverview) executeCorrelation(); }}
              disabled={!datasetOverview}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                !datasetOverview ? "opacity-40 cursor-not-allowed" : ""
              } ${
                activeTab === "correlation" 
                  ? "bg-zinc-900 text-white border-l-2 border-blue-500 pl-[14px]" 
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200"
              }`}
            >
              <Binary size={16} />
              <span>Correlation Map</span>
            </button>
            <button
              onClick={() => setActiveTab("ml")}
              disabled={!datasetOverview}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                !datasetOverview ? "opacity-40 cursor-not-allowed" : ""
              } ${
                activeTab === "ml" 
                  ? "bg-zinc-900 text-white border-l-2 border-blue-500 pl-[14px]" 
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200"
              }`}
            >
              <Settings size={16} />
              <span>ML Engine</span>
            </button>
            <button
              onClick={() => { setActiveTab("insights"); executeInsights(); }}
              disabled={!datasetOverview}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                !datasetOverview ? "opacity-40 cursor-not-allowed" : ""
              } ${
                activeTab === "insights" 
                  ? "bg-zinc-900 text-white border-l-2 border-blue-500 pl-[14px]" 
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200"
              }`}
            >
              <FileText size={16} />
              <span>Executive Summary</span>
            </button>
          </nav>
        </div>

        <div className="p-6 border-t border-zinc-900 text-xs text-zinc-600">
          SaaS Engine v2.0
        </div>
      </aside>

      {/* ── Main Work Area ── */}
      <main className="flex-1 overflow-y-auto bg-black p-8 relative">
        <AnimatePresence mode="wait">
          {/* TAB 1: UPLOAD */}
          {activeTab === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="space-y-8"
            >
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">📂 Data Loader</h1>
                <p className="text-zinc-400 mt-1">Upload single or multiple files to start your data intelligence pipeline.</p>
              </div>

              <div className="grid grid-cols-3 gap-8">
                {/* Loader control card */}
                <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                  <div className="border border-dashed border-zinc-800 rounded-xl p-8 flex flex-col items-center justify-center bg-zinc-900/20 hover:bg-zinc-900/40 transition-colors">
                    <Upload size={36} className="text-zinc-500 mb-3" />
                    <span className="text-sm font-medium text-zinc-300">Drag files here, or click to browse</span>
                    <span className="text-xs text-zinc-600 mt-1">CSV, Excel, JSON, Parquet supported</span>
                    <input 
                      type="file" 
                      multiple 
                      onChange={handleFileChange}
                      className="mt-4 text-xs file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-300 hover:file:bg-zinc-700 cursor-pointer"
                    />
                  </div>

                  {selectedFiles.length > 1 && (
                    <div className="space-y-4 pt-4 border-t border-zinc-900">
                      <h3 className="text-sm font-medium text-white flex items-center gap-2"><Layers size={16}/> Merge Settings</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs text-zinc-400 mb-2">Merge Strategy</label>
                          <select 
                            value={mergeStrategy} 
                            onChange={(e) => setMergeStrategy(e.target.value)}
                            className="w-full bg-zinc-900 border border-zinc-800 text-sm rounded-lg p-2.5 text-zinc-300 focus:border-blue-500 focus:outline-none"
                          >
                            <option>Stack (Union)</option>
                            <option>Join on Key</option>
                          </select>
                        </div>
                        {mergeStrategy === "Join on Key" && (
                          <div>
                            <label className="block text-xs text-zinc-400 mb-2">Join Type</label>
                            <select 
                              value={how} 
                              onChange={(e) => setHow(e.target.value)}
                              className="w-full bg-zinc-900 border border-zinc-800 text-sm rounded-lg p-2.5 text-zinc-300 focus:border-blue-500 focus:outline-none"
                            >
                              <option value="inner">Inner Join</option>
                              <option value="left">Left Join</option>
                              <option value="outer">Outer Join</option>
                            </select>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {selectedFiles.length > 0 && (
                    <div className="flex justify-between items-center pt-4 border-t border-zinc-900">
                      <div className="text-xs text-zinc-400">
                        {selectedFiles.length} file(s) selected: {selectedFiles.map(f => f.name).join(", ")}
                      </div>
                      <button
                        onClick={executeUpload}
                        disabled={isUploading}
                        className="bg-blue-600 text-white font-medium text-sm px-5 py-2.5 rounded-lg hover:bg-blue-500 transition-colors flex items-center gap-2"
                      >
                        {isUploading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                        <span>Analyze Dataset</span>
                      </button>
                    </div>
                  )}

                  {uploadError && (
                    <div className="bg-red-950/20 border border-red-900/50 text-red-400 text-sm p-4 rounded-lg">
                      {uploadError}
                    </div>
                  )}
                </div>

                {/* KPI Sidebar */}
                <div className="space-y-6">
                  {datasetOverview ? (
                    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                      <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Auto-Analysis Summary</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-zinc-900/50 border border-zinc-900 rounded-lg p-4">
                          <span className="block text-xs text-zinc-500 font-medium">Rows</span>
                          <span className="text-2xl font-semibold text-white tracking-tight">
                            <AnimatedCounter value={datasetOverview.rows} />
                          </span>
                        </div>
                        <div className="bg-zinc-900/50 border border-zinc-900 rounded-lg p-4">
                          <span className="block text-xs text-zinc-500 font-medium">Columns</span>
                          <span className="text-2xl font-semibold text-white tracking-tight">
                            <AnimatedCounter value={datasetOverview.columns} />
                          </span>
                        </div>
                        <div className="bg-zinc-900/50 border border-zinc-900 rounded-lg p-4">
                          <span className="block text-xs text-zinc-500 font-medium">Missing Cells %</span>
                          <span className="text-2xl font-semibold text-white tracking-tight">
                            <AnimatedCounter value={datasetOverview.missing_pct} suffix="%" />
                          </span>
                        </div>
                        <div className="bg-zinc-900/50 border border-zinc-900 rounded-lg p-4">
                          <span className="block text-xs text-zinc-500 font-medium">Duplicates</span>
                          <span className="text-2xl font-semibold text-white tracking-tight">
                            <AnimatedCounter value={datasetOverview.duplicate_rows} />
                          </span>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-zinc-900">
                        <span className="block text-xs text-zinc-500 font-semibold mb-2">AutoNarrate Insights:</span>
                        <div className="text-sm text-zinc-300 leading-relaxed italic bg-zinc-900/30 border border-zinc-900 p-4 rounded-lg">
                          "{autoNarrative}"
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 flex flex-col items-center justify-center text-center h-full min-h-[300px]">
                      <Database className="text-zinc-700 mb-2" size={32} />
                      <span className="text-sm text-zinc-500">Upload data to view properties and auto-narration overview.</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Data Preview Table */}
              {previewData && (
                <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Dataset Preview (First 50 Rows)</h3>
                  <div className="overflow-x-auto border border-zinc-900 rounded-lg">
                    <table className="w-full text-left text-xs text-zinc-400 border-collapse">
                      <thead className="bg-zinc-900 text-zinc-300 uppercase font-semibold border-b border-zinc-800">
                        <tr>
                          {previewData.columns.map((col: string) => (
                            <th key={col} className="p-3 border-r border-zinc-800 font-mono">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900 font-mono">
                        {previewData.preview.map((row: any, i: number) => (
                          <tr key={i} className="hover:bg-zinc-900/40">
                            {previewData.columns.map((col: string) => (
                              <td key={col} className="p-3 border-r border-zinc-900 max-w-[200px] truncate">{String(row[col])}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* TAB 2: PROFILING & OUTLIERS */}
          {activeTab === "profiling" && (
            <motion.div
              key="profiling"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="space-y-8"
            >
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">📊 Profiling & Outliers</h1>
                <p className="text-zinc-400 mt-1">Deep analysis of data quality, null rates, and outlier distribution.</p>
              </div>

              {profilingLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-zinc-500">
                  <RefreshCw size={36} className="animate-spin text-blue-500" />
                  <span>Computing profile matrices & parsing outliers...</span>
                </div>
              ) : (
                <>
                  {qualityScore && (
                    <div className="grid grid-cols-3 gap-8">
                      {/* Radial Gauge */}
                      <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 flex flex-col items-center justify-center">
                        <QualityGauge score={qualityScore.score} />
                      </div>

                      {/* Deductions List */}
                      <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Quality Deductions & Warnings</h3>
                        <div className="space-y-2">
                          {qualityScore.details && qualityScore.details.length > 0 ? (
                            qualityScore.details.map((d: string, idx: number) => (
                              <div key={idx} className="flex items-start gap-2 text-sm text-zinc-300 bg-zinc-900/30 border border-zinc-900 p-3 rounded-lg">
                                <AlertCircle size={16} className="text-amber-500 mt-0.5 shrink-0" />
                                <span>{d}</span>
                              </div>
                            ))
                          ) : (
                            <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-950/10 border border-emerald-900/50 p-4 rounded-lg">
                              <CheckCircle2 size={16} />
                              <span>No quality deductions — dataset is in pristine shape!</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* AI Summary / Column Profiling */}
                  {profilingRows.length > 0 && (
                    <div className="grid grid-cols-3 gap-8">
                      <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Column Profiling Matrix</h3>
                        <div className="overflow-x-auto border border-zinc-900 rounded-lg">
                          <table className="w-full text-left text-xs text-zinc-400 border-collapse">
                            <thead className="bg-zinc-900 text-zinc-300 uppercase font-semibold border-b border-zinc-800">
                              <tr>
                                <th className="p-3 border-r border-zinc-800">Column</th>
                                <th className="p-3 border-r border-zinc-800">Type</th>
                                <th className="p-3 border-r border-zinc-800">Unique</th>
                                <th className="p-3 border-r border-zinc-800">Nulls</th>
                                <th className="p-3 border-r border-zinc-800">Null %</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-900 font-mono">
                              {profilingRows.map((row: any, i: number) => (
                                <tr key={i} className="hover:bg-zinc-900/40">
                                  <td className="p-3 border-r border-zinc-900 text-zinc-200 font-medium">{row.Column}</td>
                                  <td className="p-3 border-r border-zinc-900 text-zinc-500">{row.Type}</td>
                                  <td className="p-3 border-r border-zinc-900">{row.Unique}</td>
                                  <td className="p-3 border-r border-zinc-900">{row.Nulls}</td>
                                  <td className="p-3 border-r border-zinc-900">{row["Null %"]}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <div className="space-y-6">
                        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                          <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Column Summary</h3>
                          <div className="text-xs text-zinc-400 leading-relaxed bg-zinc-900/40 p-4 rounded-lg border border-zinc-900">
                            {profilingNarration}
                          </div>
                        </div>

                        {aiSummary && (
                          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                            <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase flex items-center gap-1.5">
                              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                              AI Auto-Summary
                            </h3>
                            <div className="text-xs text-zinc-300 leading-relaxed bg-zinc-900/50 p-4 rounded-lg border border-zinc-900 border-l-2 border-l-blue-500">
                              {aiSummary}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Outliers */}
                  {outliersSummary && (
                    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">🚨 Outlier Detection Analysis</h3>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleOutlierMethodChange("IQR")}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                              outlierMethod === "IQR"
                                ? "bg-zinc-900 text-white border-zinc-800"
                                : "text-zinc-500 border-transparent hover:text-zinc-300"
                            }`}
                          >
                            IQR Method
                          </button>
                          <button
                            onClick={() => handleOutlierMethodChange("Z-Score")}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                              outlierMethod === "Z-Score"
                                ? "bg-zinc-900 text-white border-zinc-800"
                                : "text-zinc-500 border-transparent hover:text-zinc-300"
                            }`}
                          >
                            Z-Score Method
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-8">
                        <div className="col-span-2 space-y-4">
                          <div className="flex gap-4 items-center">
                            <label className="text-xs text-zinc-400 uppercase font-semibold tracking-wider">Inspect Outliers for:</label>
                            <select
                              value={selectedOutlierCol}
                              onChange={(e) => setSelectedOutlierCol(e.target.value)}
                              className="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-300 focus:outline-none"
                            >
                              {Object.keys(outliersSummary).map((col) => (
                                <option key={col} value={col}>{col} ({outliersSummary[col]} outliers)</option>
                              ))}
                            </select>
                          </div>

                          {selectedOutlierCol && outlierDetails?.[selectedOutlierCol]?.length > 0 ? (
                            <div className="overflow-x-auto border border-zinc-900 rounded-lg max-h-[300px]">
                              <table className="w-full text-left text-xs text-zinc-400 border-collapse">
                                <thead className="bg-zinc-900 text-zinc-300 uppercase font-semibold border-b border-zinc-800 sticky top-0">
                                  <tr>
                                    {datasetOverview.numeric_col_names.map((col: string) => (
                                      <th key={col} className="p-3 border-r border-zinc-800 font-mono bg-zinc-900">{col}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-zinc-900 font-mono">
                                  {outlierDetails[selectedOutlierCol].slice(0, 10).map((row: any, i: number) => (
                                    <tr key={i} className="hover:bg-zinc-900/40">
                                      {datasetOverview.numeric_col_names.map((col: string) => (
                                        <td key={col} className="p-3 border-r border-zinc-900 max-w-[150px] truncate">{String(row[col])}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <div className="text-sm text-zinc-500 italic py-8">No outlier values detected in this column.</div>
                          )}
                        </div>

                        {/* Outlier flags / Narration */}
                        <div className="space-y-4">
                          <div className="bg-zinc-900/40 border border-zinc-900 p-4 rounded-lg">
                            <span className="block text-xs text-zinc-500 font-semibold mb-2">Outlier Narration:</span>
                            <p className="text-xs text-zinc-400 leading-relaxed">{outliersNarration}</p>
                          </div>

                          <div className="border border-zinc-900 p-4 rounded-lg bg-zinc-950 space-y-4">
                            <h4 className="text-xs font-semibold tracking-wider text-zinc-400 uppercase flex items-center gap-1.5">
                              Flag Observations
                            </h4>
                            <div>
                              <label className="block text-[10px] text-zinc-500 mb-1.5">Describe what you observe:</label>
                              <input
                                type="text"
                                value={flagDesc}
                                onChange={(e) => setFlagDesc(e.target.value)}
                                placeholder="E.g., High transaction values detected in outlier check"
                                className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-xs text-zinc-300 focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[10px] text-zinc-500 mb-1.5">Flag Type:</label>
                              <select
                                value={flagType}
                                onChange={(e) => setFlagType(e.target.value)}
                                className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-xs text-zinc-300 focus:outline-none"
                              >
                                <option value="anomaly">Anomaly</option>
                                <option value="pattern">Pattern</option>
                                <option value="question">Question</option>
                                <option value="domain knowledge">Domain Knowledge</option>
                              </select>
                            </div>
                            <button
                              onClick={executeAddFlag}
                              className="w-full bg-zinc-900 border border-zinc-800 hover:bg-zinc-800/80 text-zinc-300 font-semibold text-xs py-2 rounded transition-colors flex items-center justify-center gap-1.5"
                            >
                              Add Flag Note
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {/* TAB 3: CORRELATION MAP */}
          {activeTab === "correlation" && (
            <motion.div
              key="correlation"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="space-y-8"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight text-white">🌌 Correlation Map</h1>
                  <p className="text-zinc-400 mt-1">Draggable, force-directed graph illustrating relational strengths between variables.</p>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => setCorrTab("universe")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      corrTab === "universe"
                        ? "bg-zinc-900 text-white border-zinc-800"
                        : "text-zinc-500 border-transparent hover:text-zinc-300"
                    }`}
                  >
                    🌌 Physics Universe
                  </button>
                  <button
                    onClick={() => setCorrTab("heatmap")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      corrTab === "heatmap"
                        ? "bg-zinc-900 text-white border-zinc-800"
                        : "text-zinc-500 border-transparent hover:text-zinc-300"
                    }`}
                  >
                    📊 Matrix View
                  </button>
                </div>
              </div>

              {corrLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-zinc-500">
                  <RefreshCw size={36} className="animate-spin text-blue-500" />
                  <span>Loading physics simulator nodes and weights...</span>
                </div>
              ) : (
                <>
                  {physicsData && corrTab === "universe" && (
                    <PhysicsUniverse nodes={physicsData.nodes} edges={physicsData.edges} />
                  )}

                  {corrMatrix && corrTab === "heatmap" && (
                    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                      <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Correlation Coefficients Matrix</h3>
                      <div className="overflow-x-auto border border-zinc-900 rounded-lg">
                        <table className="w-full text-center text-xs text-zinc-400 border-collapse">
                          <thead className="bg-zinc-900 text-zinc-300 uppercase font-semibold border-b border-zinc-800">
                            <tr>
                              <th className="p-3 border-r border-zinc-800 text-left">Variable</th>
                              {corrCols.map((c) => (
                                <th key={c} className="p-3 border-r border-zinc-800 font-mono text-[10px] truncate max-w-[80px]">{c}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-900 font-mono">
                            {corrCols.map((colName) => (
                              <tr key={colName} className="hover:bg-zinc-900/40">
                                <td className="p-3 border-r border-zinc-900 text-left text-zinc-200 font-medium">{colName}</td>
                                {corrCols.map((colNameInner) => {
                                  const val = corrMatrix[colName]?.[colNameInner] ?? 0;
                                  let cellColor = "";
                                  if (val > 0.5) cellColor = "bg-blue-950/40 text-blue-300";
                                  else if (val < -0.5) cellColor = "bg-red-950/40 text-red-300";
                                  return (
                                    <td key={colNameInner} className={`p-3 border-r border-zinc-900 ${cellColor}`}>
                                      {val.toFixed(2)}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {/* TAB 4: ML ENGINE */}
          {activeTab === "ml" && (
            <motion.div
              key="ml"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="space-y-8"
            >
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">⚙️ Machine Learning Engine</h1>
                <p className="text-zinc-400 mt-1">Automatic task formulation, pipeline tuning, and metric narratives.</p>
              </div>

              <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                <div className="flex gap-4 items-center">
                  <label className="text-xs text-zinc-400 uppercase font-semibold tracking-wider">Select Target Variable:</label>
                  <select
                    value={targetCol}
                    onChange={(e) => setTargetCol(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 text-xs rounded-lg px-3 py-2.5 text-zinc-300 focus:outline-none"
                  >
                    <option value="">-- Choose target column --</option>
                    {columnRoles && Object.keys(columnRoles).map((col) => (
                      <option key={col} value={col}>{col} ({columnRoles[col]})</option>
                    ))}
                  </select>
                  <button
                    onClick={executeTrain}
                    disabled={!targetCol || mlLoading}
                    className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
                  >
                    {mlLoading ? <RefreshCw size={12} className="animate-spin" /> : <Play size={12} />}
                    <span>Initialize Training</span>
                  </button>
                </div>
              </div>

              {mlLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-zinc-500">
                  <RefreshCw size={36} className="animate-spin text-blue-500" />
                  <span>Scaffolding pipelines, cross-validating models...</span>
                </div>
              ) : (
                <>
                  {mlResults && (
                    <div className="grid grid-cols-3 gap-8">
                      {/* Model stats */}
                      <div className="col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                        <div className="flex justify-between items-center border-b border-zinc-900 pb-4">
                          <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Model Evaluation Matrix</h3>
                          <span className="text-xs text-blue-500 font-mono tracking-wider font-semibold uppercase">{mlTask} task detected</span>
                        </div>

                        <div className="overflow-x-auto border border-zinc-900 rounded-lg">
                          <table className="w-full text-left text-xs text-zinc-400 border-collapse">
                            <thead className="bg-zinc-900 text-zinc-300 uppercase font-semibold border-b border-zinc-800">
                              <tr>
                                <th className="p-3 border-r border-zinc-800">Model Name</th>
                                {mlTask === "clustering" ? (
                                  <>
                                    <th className="p-3 border-r border-zinc-800">Silhouette Score</th>
                                    <th className="p-3 border-r border-zinc-800">Clusters (k)</th>
                                  </>
                                ) : mlTask === "classification" ? (
                                  <>
                                    <th className="p-3 border-r border-zinc-800">Accuracy</th>
                                    <th className="p-3 border-r border-zinc-800">F1 Score</th>
                                    <th className="p-3 border-r border-zinc-800">Precision</th>
                                  </>
                                ) : (
                                  <>
                                    <th className="p-3 border-r border-zinc-800">R² Score</th>
                                    <th className="p-3 border-r border-zinc-800">MAE</th>
                                    <th className="p-3 border-r border-zinc-800">RMSE</th>
                                  </>
                                )}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-900 font-mono">
                              {Object.keys(mlResults).map((name) => {
                                const metrics = mlResults[name];
                                const isBest = name === bestModel;
                                return (
                                  <tr key={name} className={`hover:bg-zinc-900/40 ${isBest ? "bg-blue-950/10" : ""}`}>
                                    <td className="p-3 border-r border-zinc-900 text-zinc-200 font-medium">
                                      {name} {isBest && <span className="text-[10px] bg-blue-600/20 text-blue-400 border border-blue-500/30 px-1.5 py-0.5 rounded ml-2">BEST</span>}
                                    </td>
                                    {mlTask === "clustering" ? (
                                      <>
                                        <td className="p-3 border-r border-zinc-900">{metrics.silhouette?.toFixed(4) || "N/A"}</td>
                                        <td className="p-3 border-r border-zinc-900">{metrics.k || "N/A"}</td>
                                      </>
                                    ) : mlTask === "classification" ? (
                                      <>
                                        <td className="p-3 border-r border-zinc-900">{metrics.accuracy?.toFixed(4) || "N/A"}</td>
                                        <td className="p-3 border-r border-zinc-900">{metrics.f1?.toFixed(4) || "N/A"}</td>
                                        <td className="p-3 border-r border-zinc-900">{metrics.precision?.toFixed(4) || "N/A"}</td>
                                      </>
                                    ) : (
                                      <>
                                        <td className="p-3 border-r border-zinc-900">{metrics.r2?.toFixed(4) || "N/A"}</td>
                                        <td className="p-3 border-r border-zinc-900">{metrics.mae?.toFixed(4) || "N/A"}</td>
                                        <td className="p-3 border-r border-zinc-900">{metrics.rmse?.toFixed(4) || "N/A"}</td>
                                      </>
                                    )}
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Feature Importance / Opinion */}
                      <div className="space-y-6">
                        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                          <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">ML Strategy Agent Opinion</h3>
                          <div className="text-xs text-zinc-300 leading-relaxed bg-zinc-900/50 p-4 border border-zinc-900 border-l-2 border-l-blue-500 rounded-lg">
                            {mlOpinion}
                          </div>
                        </div>

                        {featureImportance.length > 0 && (
                          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                            <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Variable Importance</h3>
                            <div className="space-y-3 font-mono text-xs">
                              {featureImportance.slice(0, 6).map((item, idx) => (
                                <div key={idx} className="space-y-1">
                                  <div className="flex justify-between text-[11px]">
                                    <span className="text-zinc-300 truncate max-w-[150px]">{item.Feature}</span>
                                    <span className="text-zinc-500">{(item.Importance * 100).toFixed(1)}%</span>
                                  </div>
                                  <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                                    <div 
                                      className="bg-blue-500 h-full rounded-full" 
                                      style={{ width: `${item.Importance * 100}%` }}
                                    ></div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {/* TAB 5: EXECUTIVE SUMMARY */}
          {activeTab === "insights" && (
            <motion.div
              key="insights"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="space-y-8"
            >
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">💡 Executive Summary</h1>
                <p className="text-zinc-400 mt-1">Unified analytics matrix compiling anomalies, core insights, and annotated flags.</p>
              </div>

              {insightsLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-zinc-500">
                  <RefreshCw size={36} className="animate-spin text-blue-500" />
                  <span>Synthesizing observations...</span>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-8">
                  {/* Executive dashboard / narrative */}
                  <div className="col-span-2 space-y-8">
                    {insightsNarrative && (
                      <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Boardroom Summary Narrative</h3>
                        <div className="text-sm text-zinc-300 leading-relaxed bg-zinc-900/50 p-4 border border-zinc-900 border-l-2 border-l-blue-500 rounded-lg">
                          {insightsNarrative}
                        </div>
                      </div>
                    )}

                    {insightsList.length > 0 && (
                      <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">Core Data Observations</h3>
                        <div className="space-y-3">
                          {insightsList.map((ins, idx) => (
                            <div key={idx} className="flex items-start gap-2.5 text-xs text-zinc-400 leading-relaxed bg-zinc-900/20 p-3 rounded-lg border border-zinc-900">
                              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full shrink-0 mt-1.5"></span>
                              <span>{ins}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Flag list sidebar */}
                  <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 space-y-6">
                    <h3 className="text-sm font-semibold tracking-wider text-zinc-400 uppercase">🚩 Saved Pipeline Flags</h3>
                    {flagsList.length > 0 ? (
                      <div className="space-y-4">
                        {flagsList.map((flag, idx) => (
                          <div key={idx} className="bg-zinc-900/30 border border-zinc-900 p-4 rounded-lg space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] bg-red-600/20 text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded font-mono uppercase tracking-wider">
                                {flag.type}
                              </span>
                              <span className="text-[10px] text-zinc-500 font-mono capitalize">
                                {flag.page} tab
                              </span>
                            </div>
                            <p className="text-xs text-zinc-300 leading-relaxed">
                              {flag.description}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-center py-12 text-zinc-600">
                        <AlertCircle size={28} className="mb-2 text-zinc-700" />
                        <span className="text-xs">No pipeline flags have been noted yet. Flags added during outlier detection will show here.</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
