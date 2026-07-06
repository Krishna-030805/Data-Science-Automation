const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function uploadDataset(files: File[], strategy: string, keyCol?: string, how?: string) {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));
  formData.append("merge_strategy", strategy);
  if (keyCol) formData.append("key_col", keyCol);
  if (how) formData.append("how", how);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail?.message || errorData.detail || "Upload failed");
  }
  return res.json();
}

export async function getPreview(rows: number = 100) {
  const res = await fetch(`${API_BASE}/preview?rows=${rows}`);
  if (!res.ok) throw new Error("Failed to load dataset preview");
  return res.json();
}

export async function runProfile() {
  const res = await fetch(`${API_BASE}/profile`, { method: "POST" });
  if (!res.ok) throw new Error("Profiling failed");
  return res.json();
}

export async function runOutliers(method: "IQR" | "Z-Score") {
  const res = await fetch(`${API_BASE}/outliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method }),
  });
  if (!res.ok) throw new Error("Outlier detection failed");
  return res.json();
}

export async function getCorrelation() {
  const res = await fetch(`${API_BASE}/correlation`);
  if (!res.ok) throw new Error("Failed to compute correlations");
  return res.json();
}

export async function trainModel(targetCol: string) {
  const res = await fetch(`${API_BASE}/train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_col: targetCol }),
  });
  if (!res.ok) throw new Error("Model training failed");
  return res.json();
}

export async function addFlag(page: string, type: string, description: string) {
  const res = await fetch(`${API_BASE}/flags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page, type, description }),
  });
  if (!res.ok) throw new Error("Failed to add flag");
  return res.json();
}

export async function getInsights() {
  const res = await fetch(`${API_BASE}/insights`);
  if (!res.ok) throw new Error("Failed to load insights");
  return res.json();
}
