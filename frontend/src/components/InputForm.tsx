"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import tzlookup from "tz-lookup";
import { toDate } from "date-fns-tz";

// Dynamically import the Leaflet map so Leaflet only runs client-side (no SSR)
const LeafletMap = dynamic(() => import("@/components/LeafletMap"), {
    ssr: false,
    loading: () => (
        <div className="h-full w-full flex items-center justify-center bg-slate-800 text-slate-400 text-sm">
            Loading map…
        </div>
    ),
});

interface LatLng {
    lat: number;
    lng: number;
}

interface InputFormProps {
    onSubmit: (data: {
        name: string;
        gender: string;
        datetime_utc: string;
        latitude: number;
        longitude: number;
    }) => void;
    isLoading: boolean;
}

export default function InputForm({ onSubmit, isLoading }: InputFormProps) {
    const [name, setName] = useState("");
    const [gender, setGender] = useState("Male");
    const [date, setDate] = useState("");
    const [time, setTime] = useState("");
    const [position, setPosition] = useState<LatLng | null>(null);
    const [timezone, setTimezone] = useState<string>("");

    useEffect(() => {
        if (position) {
            try {
                const tz = tzlookup(position.lat, position.lng);
                setTimezone(tz);
            } catch {
                setTimezone("UTC");
            }
        }
    }, [position]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!position) {
            alert("Please click on the map to pick a birth location.");
            return;
        }
        if (!date || !time) {
            alert("Please fill in the date and time of birth.");
            return;
        }

        const localDateTimeStr = `${date}T${time}:00`;
        const dateInTz = toDate(localDateTimeStr, { timeZone: timezone || "UTC" });
        const utcString = dateInTz.toISOString();

        onSubmit({
            name,
            gender,
            datetime_utc: utcString,
            latitude: position.lat,
            longitude: position.lng,
        });
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-5 text-slate-100"
        >
            <h2 className="text-2xl font-semibold text-orange-400 mb-2">Birth Details</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex flex-col gap-1">
                    <span className="text-sm text-slate-400">Full Name</span>
                    <input
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="p-2 rounded bg-slate-900 border border-slate-700 focus:border-orange-500 outline-none"
                        placeholder="e.g. Ram"
                    />
                </label>

                <label className="flex flex-col gap-1">
                    <span className="text-sm text-slate-400">Gender</span>
                    <select
                        value={gender}
                        onChange={(e) => setGender(e.target.value)}
                        className="p-2 rounded bg-slate-900 border border-slate-700 focus:border-orange-500 outline-none"
                    >
                        <option>Male</option>
                        <option>Female</option>
                        <option>Other</option>
                    </select>
                </label>

                <label className="flex flex-col gap-1">
                    <span className="text-sm text-slate-400">Date of Birth</span>
                    <input
                        type="date"
                        required
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        className="p-2 rounded bg-slate-900 border border-slate-700 focus:border-orange-500 outline-none"
                    />
                </label>

                <label className="flex flex-col gap-1">
                    <span className="text-sm text-slate-400">Time of Birth (24h)</span>
                    <input
                        type="time"
                        required
                        value={time}
                        onChange={(e) => setTime(e.target.value)}
                        className="p-2 rounded bg-slate-900 border border-slate-700 focus:border-orange-500 outline-none"
                    />
                </label>
            </div>

            {/* Map Picker */}
            <div className="flex flex-col gap-2 mt-2">
                <span className="text-sm text-slate-400 flex justify-between items-center">
                    <span>Place of Birth — click the map to select</span>
                    {timezone && (
                        <span className="text-orange-400 border border-orange-400/30 bg-orange-400/10 px-2 rounded-full text-xs">
                            {timezone}
                        </span>
                    )}
                </span>

                {position && (
                    <p className="text-xs text-slate-400">
                        📍 Lat: <span className="text-orange-300">{position.lat.toFixed(4)}</span> &nbsp; Lng:{" "}
                        <span className="text-orange-300">{position.lng.toFixed(4)}</span>
                    </p>
                )}

                {/* Map container — must have an explicit height */}
                <div className="h-[260px] w-full rounded overflow-hidden border border-slate-700" style={{ zIndex: 0 }}>
                    <LeafletMap position={position} onLocationSelect={setPosition} />
                </div>

                <p className="text-xs text-slate-500">
                    * Manual lat/lon entry is disabled. Pin the exact birthplace on the map.
                </p>
            </div>

            <button
                type="submit"
                disabled={isLoading}
                className="mt-2 bg-orange-600 hover:bg-orange-500 text-white font-medium py-3 px-4 rounded transition-colors disabled:opacity-50"
            >
                {isLoading ? "Generating Chart…" : "Generate Kundali"}
            </button>
        </form>
    );
}
