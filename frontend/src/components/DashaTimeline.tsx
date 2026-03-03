import React, { useState } from "react";

interface Antardasha {
    lord: string;
    start: string;
    end: string;
}

interface Mahadasha {
    mahadasha_lord: string;
    start: string;
    end: string;
    antardashas: Antardasha[];
}

interface DashaTimelineProps {
    dashas: Mahadasha[];
}

export default function DashaTimeline({ dashas }: DashaTimelineProps) {
    const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

    const formatDate = (isoString: string) => {
        return new Date(isoString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    return (
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 text-slate-100 mt-6">
            <h2 className="text-2xl font-semibold text-orange-400 mb-4">Vimshottari Dasha</h2>
            <div className="flex flex-col gap-2 relative">
                {/* Vertical Timeline Line */}
                <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-slate-700"></div>

                {dashas.map((md, idx) => (
                    <div key={`md-${idx}`} className="relative pl-10">
                        {/* Timeline Dot */}
                        <div className="absolute left-3 w-3 h-3 rounded-full bg-orange-500 top-3"></div>

                        <div
                            className="bg-slate-900 border border-slate-700 p-4 rounded cursor-pointer hover:border-orange-500/50 transition-colors"
                            onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
                        >
                            <div className="flex justify-between items-center">
                                <span className="font-bold text-lg text-orange-200">
                                    {md.mahadasha_lord} Mahadasha
                                </span>
                                <span className="text-sm text-slate-400">
                                    {formatDate(md.start)} - {formatDate(md.end)}
                                </span>
                            </div>

                            {/* Antardashas dropdown */}
                            {expandedIndex === idx && (
                                <div className="mt-4 flex flex-col gap-2 pl-4 border-l-2 border-slate-800">
                                    {md.antardashas.map((ad, i) => (
                                        <div key={`ad-${i}`} className="flex justify-between text-sm py-1 border-b border-slate-800/50 last:border-0">
                                            <span className="text-slate-300">{ad.lord} Antardasha</span>
                                            <span className="text-slate-500">
                                                {formatDate(ad.start)} - {formatDate(ad.end)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
