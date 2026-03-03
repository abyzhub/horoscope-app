import React from "react";

interface Yoga {
    name: string;
    description: string;
}

interface YogaListProps {
    yogas: Yoga[];
}

export default function YogaList({ yogas }: YogaListProps) {
    if (!yogas || yogas.length === 0) {
        return (
            <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 text-slate-100 mt-6">
                <h2 className="text-2xl font-semibold text-orange-400 mb-2">Detected Yogas</h2>
                <p className="text-slate-400">No major classical yogas detected in this chart.</p>
            </div>
        );
    }

    return (
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 text-slate-100 mt-6 md:mt-0">
            <h2 className="text-2xl font-semibold text-orange-400 mb-4">Detected Yogas</h2>
            <div className="flex flex-col gap-4">
                {yogas.map((yoga, idx) => (
                    <div key={`yoga-${idx}`} className="bg-slate-900 border border-slate-700 p-4 rounded border-l-4 border-l-orange-500">
                        <h3 className="font-bold text-orange-200 text-lg">{yoga.name}</h3>
                        <p className="text-sm text-slate-300 mt-1">{yoga.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
