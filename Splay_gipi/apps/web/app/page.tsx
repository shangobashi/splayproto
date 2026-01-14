'use client';

import { useMemo, useState } from "react";

type BBox = { x:number; y:number; w:number; h:number };
type Product = { id:string; name:string; brand:string; category:string; price:number; affiliate_url:string };
type Match = { rank:number; is_budget:boolean; product:Product };
type Item = { id:string; category:string; bbox:BBox; confidence:number; matches:Match[] };
type Scan = { id:string; status:string; created_at:string; items:Item[] };

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function Page() {
  const [file, setFile] = useState<File | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const overlay = useMemo(() => {
    if (!scan?.items?.length) return null;
    return (
      <div className="overlay">
        {scan.items.map((it) => (
          <div
            key={it.id}
            className="overlay-box"
            title={`${it.category} (${Math.round(it.confidence * 100)}%)`}
            style={{
              left: `${it.bbox.x * 100}%`,
              top: `${it.bbox.y * 100}%`,
              width: `${it.bbox.w * 100}%`,
              height: `${it.bbox.h * 100}%`,
            }}
          />
        ))}
      </div>
    );
  }, [scan]);

  async function poll(scanId: string) {
    for (let i=0; i<60; i++) {
      const r = await fetch(`${API}/scans/${scanId}`);
      const s = await r.json();
      setScan(s);
      if (s.status === "done" || s.status === "failed") return;
      await new Promise(res => setTimeout(res, 600));
    }
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    setScan(null);

    const form = new FormData();
    form.append("image", file);

    const r = await fetch(`${API}/scans`, { method:"POST", body: form });
    if (!r.ok) {
      setBusy(false);
      alert(`Upload failed: ${r.status}`);
      return;
    }
    const { scan_id } = await r.json();
    await poll(scan_id);
    setBusy(false);
  }

  return (
    <main className="page">
      <div className="hero">
        <h1 className="title">Splay</h1>
        <p className="subtitle">Upload a room photo. Get detected items + shoppable matches.</p>
      </div>

      <div className="controls">
        <input
          className="file-input"
          type="file"
          accept="image/*"
          onChange={(e) => {
            const f = e.target.files?.[0] || null;
            setFile(f);
            if (f) setImageUrl(URL.createObjectURL(f));
          }}
        />
        <button onClick={submit} disabled={!file || busy} className="primary-btn">
          {busy ? "Scanning..." : "Scan"}
        </button>
      </div>

      {imageUrl && (
        <div className="preview">
          <img src={imageUrl} alt="Uploaded room" />
          {overlay}
        </div>
      )}

      {scan && (
        <section>
          <h2 className="status">Status: {scan.status}</h2>
          {scan.status === "done" &&
            scan.items.map((it) => (
              <div key={it.id} className="result-card">
                <div className="result-header">
                  <strong style={{ textTransform: "capitalize" }}>{it.category.replace("_", " ")}</strong>
                  <span style={{ color: "#555" }}>{Math.round(it.confidence * 100)}%</span>
                </div>
                <div className="matches">
                  {it.matches.map((m) => (
                    <a key={m.rank} href={m.product.affiliate_url} target="_blank" rel="noreferrer" className="match-card">
                      <div className="match-inner">
                        <div className="match-meta">
                          {m.is_budget ? "Budget pick" : "Top match"} · Rank {m.rank}
                        </div>
                        <div className="match-title">{m.product.name}</div>
                        <div className="match-brand">{m.product.brand}</div>
                        <div className="match-price">${m.product.price.toFixed(2)}</div>
                        <div className="match-link">Open retailer →</div>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            ))}
        </section>
      )}
    </main>
  );
}
