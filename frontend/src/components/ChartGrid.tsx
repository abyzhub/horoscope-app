import React from "react";

// Standard fixed polygons for North Indian Kundali SVG (400x400)
const HOUSES_POLYGONS = [
    { house: 1, points: "100,100 200,0 300,100 200,200", center: { x: 200, y: 100 } },
    { house: 2, points: "0,0 200,0 100,100", center: { x: 100, y: 50 } },
    { house: 3, points: "0,0 100,100 0,200", center: { x: 50, y: 100 } },
    { house: 4, points: "100,100 200,200 100,300 0,200", center: { x: 100, y: 200 } },
    { house: 5, points: "0,200 100,300 0,400", center: { x: 50, y: 300 } },
    { house: 6, points: "100,300 200,400 0,400", center: { x: 100, y: 350 } },
    { house: 7, points: "100,300 200,200 300,300 200,400", center: { x: 200, y: 300 } },
    { house: 8, points: "200,400 300,300 400,400", center: { x: 300, y: 350 } },
    { house: 9, points: "300,300 400,200 400,400", center: { x: 350, y: 300 } },
    { house: 10, points: "200,200 300,100 400,200 300,300", center: { x: 300, y: 200 } },
    { house: 11, points: "300,100 400,0 400,200", center: { x: 350, y: 100 } },
    { house: 12, points: "200,0 400,0 300,100", center: { x: 300, y: 50 } },
];

const SIGN_NAMES_TO_NUMBERS: Record<string, number> = {
    Aries: 1, Taurus: 2, Gemini: 3, Cancer: 4,
    Leo: 5, Virgo: 6, Libra: 7, Scorpio: 8,
    Sagittarius: 9, Capricorn: 10, Aquarius: 11, Pisces: 12
};

const PLANET_ABBREVIATIONS: Record<string, string> = {
    Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me",
    Jupiter: "Ju", Venus: "Ve", Saturn: "Sa",
    Rahu: "Ra", Ketu: "Ke", Ascendant: "Asc"
};

interface ChartGridProps {
    planets: any[];
    ascendant: any;
    divisionalMapping?: Record<string, string>; // e.g. {"Sun": "Aries", ...} (optional for D-charts)
}

export default function ChartGrid({ planets, ascendant, divisionalMapping }: ChartGridProps) {
    // If we have divisional mappings, we use them instead of the raw planet house
    // Otherwise default D1 logic: calculate sign numbers per house based on Ascendant
    const ascSignStr = divisionalMapping ? divisionalMapping["Ascendant"] : ascendant?.sign;
    const ascSignNum = ascSignStr ? SIGN_NAMES_TO_NUMBERS[ascSignStr] : 1;

    // Group planets by house (1 to 12)
    const planetsByHouse: Record<number, any[]> = {};
    for (let i = 1; i <= 12; i++) planetsByHouse[i] = [];

    if (divisionalMapping && ascSignNum) {
        // It's a divisional chart, compute house dynamically based on sign
        planets.forEach(p => {
            const pSign = divisionalMapping[p.name];
            if (pSign && p.name !== "Ascendant") {
                const pSignNum = SIGN_NAMES_TO_NUMBERS[pSign];
                // House = (PlanetSign - AscSign) % 12 + 1
                const house = (pSignNum - ascSignNum + 12) % 12 + 1;
                planetsByHouse[house].push(p);
            }
        });
    } else {
        // It's D1 chart, houses are directly available
        planets.forEach(p => {
            if (p.name !== "Ascendant") {
                planetsByHouse[p.house].push(p);
            }
        });
    }

    return (
        <div className="w-full max-w-[500px] aspect-square mx-auto bg-orange-50/5 p-4 rounded-xl border border-orange-500/20">
            <svg viewBox="0 0 400 400" className="w-full h-full drop-shadow-lg">
                {/* Background & Outer Border */}
                <rect x="0" y="0" width="400" height="400" fill="transparent" stroke="#f97316" strokeWidth="3" />

                {/* Diagonal X (TL to BR, TR to BL) */}
                <line x1="0" y1="0" x2="400" y2="400" stroke="#f97316" strokeWidth="1.5" />
                <line x1="400" y1="0" x2="0" y2="400" stroke="#f97316" strokeWidth="1.5" />

                {/* Inner Diamond (TM to ML to BM to MR to TM) */}
                <line x1="200" y1="0" x2="0" y2="200" stroke="#f97316" strokeWidth="1.5" />
                <line x1="0" y1="200" x2="200" y2="400" stroke="#f97316" strokeWidth="1.5" />
                <line x1="200" y1="400" x2="400" y2="200" stroke="#f97316" strokeWidth="1.5" />
                <line x1="400" y1="200" x2="200" y2="0" stroke="#f97316" strokeWidth="1.5" />

                {/* Render text inside each house */}
                {HOUSES_POLYGONS.map((hLabel) => {
                    const houseNum = hLabel.house;
                    // Number of the sign in this house
                    const signNum = (ascSignNum + houseNum - 2) % 12 + 1;
                    const occupants = planetsByHouse[houseNum] || [];

                    return (
                        <g key={`house-${houseNum}`}>
                            {/* Sign Number */}
                            <text
                                x={hLabel.center.x}
                                y={hLabel.center.y - (occupants.length > 0 ? 15 : 0)} // shift up if planets exist
                                textAnchor="middle"
                                fill="#fdba74"
                                fontSize="12"
                                opacity="0.8"
                                fontWeight="bold"
                            >
                                {signNum}
                            </text>

                            {/* Planets */}
                            <text
                                x={hLabel.center.x}
                                y={hLabel.center.y + 5}
                                textAnchor="middle"
                                fill="#f8fafc"
                                fontSize="14"
                                fontWeight="500"
                            >
                                {occupants.map(p => {
                                    let text = PLANET_ABBREVIATIONS[p.name];
                                    if (p.is_retrograde) text += "(R)";
                                    return text;
                                }).join(", ")}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}
