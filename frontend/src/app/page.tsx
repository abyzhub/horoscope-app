"use client";

import React, { useState } from "react";
import InputForm from "@/components/InputForm";
import ChartGrid from "@/components/ChartGrid";
import DashaTimeline from "@/components/DashaTimeline";
import YogaList from "@/components/YogaList";
import ForecastPanel from "@/components/ForecastPanel";
import ChatPanel from "@/components/ChatPanel";

type MainTab = "chart" | "forecast" | "ask";
type ChartTab = "D1" | "D9" | "D10";

export default function Home() {
  const [chartData, setChartData] = useState<any>(null);
  const [birthId, setBirthId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [mainTab, setMainTab] = useState<MainTab>("chart");
  const [chartTab, setChartTab] = useState<ChartTab>("D1");

  const handleGenerateChart = async (formData: any) => {
    setIsLoading(true);
    setError("");
    setChartData(null);
    setBirthId("");

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE}/generate-chart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error("Failed to generate chart.");
      const data = await response.json();
      setChartData(data);
      setBirthId(data.birth_id);
      setMainTab("chart");
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const TAB_ITEMS: { id: MainTab; label: string; icon: string }[] = [
    { id: "chart", label: "Birth Chart", icon: "⬡" },
    { id: "forecast", label: "Forecast", icon: "📅" },
    { id: "ask", label: "Ask Agent", icon: "✦" },
  ];

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 pb-24 font-sans">
      {/* Hero Header */}
      <div className="text-center pt-10 pb-6 px-4 border-b border-slate-800">
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-orange-400 via-red-400 to-pink-500 bg-clip-text text-transparent tracking-tight">
          Vedic Horoscope
        </h1>
        <p className="text-slate-400 mt-2 text-sm">
          Strictly follows Brihad Parashara Hora Shastra · Swiss Ephemeris precision · Temporal Intelligence
        </p>
      </div>

      <div className="max-w-6xl mx-auto px-4 md:px-8 mt-8 space-y-8">

        {/* ── Input Form (before chart) ── */}
        {!chartData && (
          <div className="max-w-3xl mx-auto">
            <InputForm onSubmit={handleGenerateChart} isLoading={isLoading} />
            {error && <p className="text-red-400 mt-4 text-center text-sm">{error}</p>}
          </div>
        )}

        {/* ── Post-generation view ── */}
        {chartData && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Top bar */}
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-slate-100">
                  {chartData.name}'s Chart
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Ascendant: <span className="text-orange-300">{chartData.ascendant.sign}</span>
                  &nbsp;·&nbsp; birth_id: <span className="font-mono text-slate-500 text-[10px]">{birthId.slice(0, 8)}…</span>
                </p>
              </div>
              <button
                onClick={() => { setChartData(null); setBirthId(""); }}
                className="text-sm text-slate-400 hover:text-orange-400 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors"
              >
                ← New Chart
              </button>
            </div>

            {/* Main Tab Bar */}
            <div className="flex bg-slate-800/60 backdrop-blur p-1 rounded-xl w-full border border-slate-700/50">
              {TAB_ITEMS.map(({ id, label, icon }) => (
                <button
                  key={id}
                  onClick={() => setMainTab(id)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${mainTab === id
                    ? "bg-orange-600 text-white shadow-lg shadow-orange-900/30"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <span>{icon}</span>
                  <span>{label}</span>
                </button>
              ))}
            </div>

            {/* ── Chart Tab ── */}
            {mainTab === "chart" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Left: Chart */}
                <div className="lg:col-span-7 space-y-5">
                  <div className="flex bg-slate-800 p-1 rounded-lg w-fit border border-slate-700">
                    {(["D1", "D9", "D10"] as ChartTab[]).map((ct) => (
                      <button
                        key={ct}
                        onClick={() => setChartTab(ct)}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${chartTab === ct ? "bg-orange-500 text-white" : "text-slate-400 hover:text-slate-200"
                          }`}
                      >
                        {ct === "D1" ? "D1 (Lagna)" : ct === "D9" ? "D9 (Navamsa)" : "D10 (Dashamsa)"}
                      </button>
                    ))}
                  </div>

                  <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-semibold text-orange-400 mb-4 text-center">
                      {chartTab === "D1" ? "Lagna Chart (D1)" : chartTab === "D9" ? "Navamsa (D9)" : "Dashamsa (D10)"}
                    </h3>
                    <ChartGrid
                      planets={chartData.planets}
                      ascendant={chartData.ascendant}
                      divisionalMapping={chartTab !== "D1" ? chartData.divisional_charts[chartTab] : undefined}
                    />
                  </div>

                  <DashaTimeline dashas={chartData.dashas} />
                </div>

                {/* Right: Details */}
                <div className="lg:col-span-5 space-y-5">
                  <div className="bg-slate-800 p-5 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-semibold text-orange-400 mb-4">Planetary Positions</h3>
                    <div className="space-y-1 text-sm">
                      <div className="grid grid-cols-4 font-medium border-b border-slate-700 pb-2 mb-2 text-slate-400 text-xs">
                        <span>Planet</span><span>Sign</span><span>Deg°</span><span>House</span>
                      </div>
                      <div className="grid grid-cols-4 border-b border-slate-700/50 pb-1.5 text-xs">
                        <span className="text-orange-200">Ascendant</span>
                        <span>{chartData.ascendant.sign}</span>
                        <span>{chartData.ascendant.sign_degree.toFixed(1)}°</span>
                        <span>1</span>
                      </div>
                      {chartData.planets.map((p: any) => (
                        <div key={p.name} className="grid grid-cols-4 border-b border-slate-700/30 pb-1.5 last:border-0 text-xs">
                          <span className="text-orange-200">
                            {p.name}{p.is_retrograde ? " ®" : ""}
                          </span>
                          <span>{p.sign}</span>
                          <span>{p.sign_degree.toFixed(1)}°</span>
                          <span>{p.house}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <YogaList yogas={chartData.yogas} />
                </div>
              </div>
            )}

            {/* ── Forecast Tab ── */}
            {mainTab === "forecast" && (
              <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <h3 className="text-xl font-semibold text-orange-400 mb-6">Temporal Forecast</h3>
                <ForecastPanel birthId={birthId} />
              </div>
            )}

            {/* ── Ask Tab ── */}
            {mainTab === "ask" && (
              <ChatPanel birthId={birthId} />
            )}
          </div>
        )}
      </div>
    </main>
  );
}
