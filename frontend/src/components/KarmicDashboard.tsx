"use client";

import React, { useState, useEffect } from "react";

interface KarmicDashboardProps {
  birthId: string;
}

export default function KarmicDashboard({ birthId }: KarmicDashboardProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!birthId) return;
    
    const fetchCycles = async () => {
      try {
        setLoading(true);
        const res = await fetch("/api/karmic-cycles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ birth_id: birthId }),
        });
        
        if (!res.ok) throw new Error("Failed to load Karmic Cycles.");
        const result = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCycles();
  }, [birthId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin h-8 w-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-400 text-center py-4">{error}</div>;
  }

  if (!data) return null;

  const { sade_sati, saturn_return, jupiter_return, timeline, cycle_progress } = data;

  return (
    <div className="space-y-8 animate-in fade-in">
      <div className="flex items-center gap-3">
        <span className="text-3xl">🧿</span>
        <h3 className="text-2xl font-semibold text-orange-400">Karmic Cycles Dashboard</h3>
      </div>
      
      <p className="text-slate-400 text-sm">
        Tracking long-term maturity milestones, challenges, and growth periods deterministically calculated via Swiss Ephemeris.
      </p>

      {/* --- Current Status Summary --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Sade Sati Card */}
        <div className={`p-5 rounded-xl border ${
          sade_sati?.current_phase ? "bg-orange-950/20 border-orange-800" : "bg-slate-800/50 border-slate-700"
        }`}>
          <h4 className="font-semibold text-slate-200 mb-2">Sade Sati Status</h4>
          {sade_sati ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Current Phase:</span>
                <span className="capitalize font-medium text-orange-300">
                  {sade_sati.current_phase || "Upcoming"}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Start Date:</span>
                <span className="text-slate-200">{sade_sati.start_date}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">End Date:</span>
                <span className="text-slate-200">{sade_sati.end_date}</span>
              </div>
              
              {/* Progress Bar */}
              {cycle_progress?.sade_sati !== undefined && (
                <div className="pt-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">Progress</span>
                    <span className="text-slate-400">{Math.round(cycle_progress.sade_sati * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-orange-600 to-red-500 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${Math.max(0, Math.min(100, cycle_progress.sade_sati * 100))}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-400 text-sm">No upcoming Sade Sati cycle within the calculable range.</p>
          )}
        </div>

        {/* Returns Card */}
        <div className="p-5 rounded-xl bg-slate-800/50 border border-slate-700 space-y-4">
          <div>
            <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-2">
              <span>🪐</span> Upcoming Saturn Return
            </h4>
            {saturn_return?.length > 0 ? (
              <div className="text-sm bg-slate-800 p-3 rounded-lg flex justify-between">
                <span className="text-slate-400">Return #{saturn_return[0].number}</span>
                <span className="text-orange-300 font-medium">{saturn_return[0].start} to {saturn_return[0].end}</span>
              </div>
            ) : (
              <p className="text-slate-500 text-sm border border-slate-700 p-2 rounded">None tracked</p>
            )}
          </div>

          <div>
            <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-2">
              <span>🍀</span> Upcoming Jupiter Return
            </h4>
            {jupiter_return?.length > 0 ? (
              <div className="text-sm bg-slate-800 p-3 rounded-lg flex justify-between">
                <span className="text-slate-400">Return #{jupiter_return[0].number}</span>
                <span className="text-green-300 font-medium">Year {jupiter_return[0].year}</span>
              </div>
            ) : (
              <p className="text-slate-500 text-sm border border-slate-700 p-2 rounded">None tracked</p>
            )}
          </div>
        </div>
      </div>

      {/* --- Timeline Overlay --- */}
      <div className="mt-8">
        <h4 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Life Timeline (Active Years)</h4>
        
        {timeline && timeline.length > 0 ? (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
            {timeline.map((entry: any, i: number) => (
              <div key={i} className="flex gap-4 items-start bg-slate-800/30 p-3 rounded-lg hover:bg-slate-800/80 transition-colors">
                <div className="w-16 flex-shrink-0 text-slate-400 font-medium">
                  {entry.year}
                </div>
                <div className="flex-1 flex flex-wrap gap-2">
                  {entry.cycles.map((cycle: string, j: number) => {
                    let badgeColor = "bg-slate-700 text-slate-300";
                    let icon = "🗓";
                    let label = cycle;
                    
                    if (cycle.includes("sade_sati")) {
                      badgeColor = cycle.includes("peak") ? "bg-red-900/50 text-red-300 border border-red-800/50" : "bg-orange-900/40 text-orange-300 border border-orange-800/50";
                      icon = "⚖️";
                      label = cycle.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
                    } else if (cycle === "saturn_return") {
                      badgeColor = "bg-purple-900/40 text-purple-300 border border-purple-800/50";
                      icon = "🪐";
                      label = "Saturn Return";
                    } else if (cycle === "jupiter_return") {
                      badgeColor = "bg-green-900/40 text-green-300 border border-green-800/50";
                      icon = "🍀";
                      label = "Jupiter Return";
                    }
                    
                    return (
                      <span key={j} className={`text-xs px-2 py-1 rounded flex items-center gap-1.5 ${badgeColor}`}>
                        <span>{icon}</span> {label}
                      </span>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500">No major cycles aggregated.</p>
        )}
      </div>

    </div>
  );
}
