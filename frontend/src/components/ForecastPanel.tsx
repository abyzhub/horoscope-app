"use client";

import React, { useState, useEffect } from "react";

interface MonthData {
    period: string;
    year: number;
    month: number;
    active_dasha: string;
    mahadasha_lord: string;
    antardasha_lord: string;
    activated_houses: number[];
    major_transits: Array<{ planet: string; sign: string; house: number; is_retrograde: boolean }>;
    intensity_index: number;
    themes: string[];
    is_high_significance: boolean;
}

interface EventScore {
    period: string;
    major_event_index: number;
    opportunity_score: number;
    risk_score: number;
    dominant_theme: string;
    is_high_significance: boolean;
}

interface ForecastData {
    monthly_breakdown: MonthData[];
    event_scores: EventScore[];
    high_significance_windows: MonthData[];
    summary: {
        avg_intensity: number;
        peak_month: string;
        high_significance_count: number;
    };
}

interface ForecastPanelProps {
    birthId: string;
}

const DOMAINS = ["general", "career", "marriage", "finance", "health", "spiritual"];

export default function ForecastPanel({ birthId }: ForecastPanelProps) {
    const currentYear = new Date().getFullYear();
    const [selectedYear, setSelectedYear] = useState(currentYear);
    const [selectedDomain, setSelectedDomain] = useState("general");
    const [forecast, setForecast] = useState<ForecastData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const fetchForecast = async () => {
        setIsLoading(true);
        setError("");
        try {
            const res = await fetch("http://localhost:8000/analyze-period", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    birth_id: birthId,
                    start_date: `${selectedYear}-01-01`,
                    end_date: `${selectedYear}-12-31`,
                    domain: selectedDomain,
                }),
            });
            if (!res.ok) throw new Error("Failed to fetch forecast.");
            const data = await res.json();
            setForecast(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchForecast();
    }, [selectedYear, selectedDomain]);

    const intensityColor = (val: number) => {
        if (val >= 7.5) return "bg-red-500";
        if (val >= 5.0) return "bg-orange-400";
        if (val >= 3.0) return "bg-yellow-400";
        return "bg-green-500";
    };

    const scoreBarColor = (val: number, maxVal = 10) => {
        const pct = (val / maxVal) * 100;
        return pct;
    };

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex flex-wrap gap-3 items-center">
                <div className="flex items-center gap-2">
                    <label className="text-sm text-slate-400">Year</label>
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(Number(e.target.value))}
                        className="bg-slate-900 border border-slate-700 text-slate-100 rounded px-3 py-1.5 text-sm focus:border-orange-500 outline-none"
                    >
                        {Array.from({ length: 10 }, (_, i) => currentYear - 1 + i).map((yr) => (
                            <option key={yr} value={yr}>{yr}</option>
                        ))}
                    </select>
                </div>
                <div className="flex items-center gap-2">
                    <label className="text-sm text-slate-400">Domain</label>
                    <select
                        value={selectedDomain}
                        onChange={(e) => setSelectedDomain(e.target.value)}
                        className="bg-slate-900 border border-slate-700 text-slate-100 rounded px-3 py-1.5 text-sm focus:border-orange-500 outline-none capitalize"
                    >
                        {DOMAINS.map((d) => (
                            <option key={d} value={d} className="capitalize">{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                        ))}
                    </select>
                </div>
                <button
                    onClick={fetchForecast}
                    disabled={isLoading}
                    className="ml-auto bg-orange-600 hover:bg-orange-500 text-white text-sm px-4 py-1.5 rounded transition-colors disabled:opacity-50"
                >
                    {isLoading ? "Analysing…" : "Refresh"}
                </button>
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            {forecast && (
                <>
                    {/* Summary Banner */}
                    <div className="grid grid-cols-3 gap-4">
                        {[
                            { label: "Avg Intensity", value: `${forecast.summary.avg_intensity}/10` },
                            { label: "Peak Month", value: forecast.summary.peak_month || "—" },
                            { label: "High Significance", value: `${forecast.summary.high_significance_count} months` },
                        ].map(({ label, value }) => (
                            <div key={label} className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
                                <p className="text-xs text-slate-400 mb-1">{label}</p>
                                <p className="text-lg font-bold text-orange-300">{value}</p>
                            </div>
                        ))}
                    </div>

                    {/* High Significance Alert */}
                    {forecast.high_significance_windows.length > 0 && (
                        <div className="bg-red-950/40 border border-red-700/50 rounded-lg p-4">
                            <h3 className="text-red-400 font-semibold mb-2">⚡ High Significance Windows</h3>
                            <div className="flex flex-wrap gap-2">
                                {forecast.high_significance_windows.map((w) => (
                                    <span key={w.period} className="bg-red-900/50 text-red-200 text-xs px-3 py-1 rounded-full border border-red-700/30">
                                        {w.period} · {w.intensity_index}/10
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Monthly Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {forecast.monthly_breakdown.map((m, idx) => {
                            const score = forecast.event_scores[idx];
                            return (
                                <div
                                    key={m.period}
                                    className={`bg-slate-900 rounded-lg border p-4 space-y-3 transition-colors ${m.is_high_significance
                                            ? "border-red-600/60 shadow-md shadow-red-900/20"
                                            : "border-slate-700"
                                        }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-semibold text-slate-100">{m.period}</h4>
                                            <p className="text-xs text-orange-300 mt-0.5">{m.active_dasha}</p>
                                        </div>
                                        {m.is_high_significance && (
                                            <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full">★ High</span>
                                        )}
                                    </div>

                                    {/* Intensity Bar */}
                                    <div>
                                        <div className="flex justify-between text-xs text-slate-500 mb-1">
                                            <span>Intensity</span>
                                            <span className="text-slate-300">{m.intensity_index}/10</span>
                                        </div>
                                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all ${intensityColor(m.intensity_index)}`}
                                                style={{ width: `${(m.intensity_index / 10) * 100}%` }}
                                            />
                                        </div>
                                    </div>

                                    {/* Opportunity / Risk */}
                                    {score && (
                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div>
                                                <p className="text-green-400 mb-1">Opportunity {score.opportunity_score}/10</p>
                                                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div className="h-full bg-green-500 rounded-full" style={{ width: `${scoreBarColor(score.opportunity_score)}%` }} />
                                                </div>
                                            </div>
                                            <div>
                                                <p className="text-red-400 mb-1">Risk {score.risk_score}/10</p>
                                                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div className="h-full bg-red-500 rounded-full" style={{ width: `${scoreBarColor(score.risk_score)}%` }} />
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Houses activated */}
                                    {m.activated_houses.length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                            {m.activated_houses.map((h) => (
                                                <span key={h} className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-1.5 py-0.5 rounded">
                                                    H{h}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Themes */}
                                    {m.themes.length > 0 && (
                                        <p className="text-xs text-slate-500 italic">{m.themes[0]}</p>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </>
            )}
        </div>
    );
}
