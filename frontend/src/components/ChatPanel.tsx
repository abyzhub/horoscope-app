"use client";

import React, { useState, useRef, useEffect } from "react";

interface Message {
    role: "user" | "assistant";
    content: string;
    structured?: {
        domain: string;
        period: string;
        high_significance_windows: Array<{ period: string; intensity_index: number; themes: string[] }>;
        peak_score?: { period: string; major_event_index: number; opportunity_score: number; risk_score: number; dominant_theme: string };
    };
}

interface ChatPanelProps {
    birthId: string;
}

const SUGGESTIONS = [
    "What does this year look like for my career?",
    "When is a good time for marriage or relationships?",
    "What are the major financial themes in the next 12 months?",
    "Which months should I be cautious about health?",
    "What is the overall spiritual growth forecast?",
];

export default function ChatPanel({ birthId }: ChatPanelProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content:
                "Namaste 🙏 I'm your Vedic astrology guide. Ask me anything about your chart — career, relationships, finances, health, or a specific time period. All insights are based on your natal chart, Dasha cycles, and transit analysis.",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (question: string) => {
        if (!question.trim()) return;
        setInput("");
        setIsLoading(true);

        const userMsg: Message = { role: "user", content: question };
        setMessages((prev) => [...prev, userMsg]);

        try {
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const res = await fetch(`${API_BASE}/ask`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ birth_id: birthId, question }),
            });

            if (!res.ok) throw new Error("Failed to get response.");
            const data = await res.json();

            // Find peak event score
            const peak = data.event_scores?.reduce(
                (best: any, s: any) => (!best || s.major_event_index > best.major_event_index ? s : best),
                null
            );

            const assistantMsg: Message = {
                role: "assistant",
                content: data.llm_interpretation || "No interpretation available.",
                structured: {
                    domain: data.domain,
                    period: data.period,
                    high_significance_windows: data.high_significance_windows || [],
                    peak_score: peak || undefined,
                },
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (e: any) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: `⚠️ Error: ${e.message}` },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[680px] bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="px-5 py-4 border-b border-slate-700 bg-slate-800">
                <h2 className="text-lg font-semibold text-orange-400">Astrology Intelligence Agent</h2>
                <p className="text-xs text-slate-400 mt-0.5">Powered by your natal chart · Strict BPHS reasoning · No fatalistic claims</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div
                            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${msg.role === "user"
                                ? "bg-orange-600 text-white rounded-br-sm"
                                : "bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-sm"
                                }`}
                        >
                            {/* Main text */}
                            <p className="whitespace-pre-wrap">{msg.content}</p>

                            {/* Structured data card (assistant only) */}
                            {msg.role === "assistant" && msg.structured && (
                                <div className="mt-3 pt-3 border-t border-slate-700 space-y-2">
                                    <div className="flex flex-wrap gap-2 text-xs">
                                        <span className="bg-slate-900 text-orange-300 border border-orange-500/30 px-2 py-0.5 rounded-full capitalize">
                                            {msg.structured.domain} · {msg.structured.period}
                                        </span>
                                    </div>

                                    {msg.structured.high_significance_windows.length > 0 && (
                                        <div>
                                            <p className="text-xs text-slate-400 mb-1">High significance windows:</p>
                                            <div className="flex flex-wrap gap-1">
                                                {msg.structured.high_significance_windows.slice(0, 4).map((w) => (
                                                    <span key={w.period} className="text-xs bg-red-900/40 text-red-300 border border-red-700/30 px-2 py-0.5 rounded-full">
                                                        ★ {w.period}
                                                    </span>
                                                ))}
                                                {msg.structured.high_significance_windows.length > 4 && (
                                                    <span className="text-xs text-slate-500">+{msg.structured.high_significance_windows.length - 4} more</span>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {msg.structured.peak_score && (
                                        <div className="grid grid-cols-3 gap-2 text-xs">
                                            <div className="bg-slate-900 rounded p-2 text-center">
                                                <p className="text-slate-500">Event Index</p>
                                                <p className="text-orange-300 font-bold">{msg.structured.peak_score.major_event_index}/10</p>
                                            </div>
                                            <div className="bg-slate-900 rounded p-2 text-center">
                                                <p className="text-green-500">Opportunity</p>
                                                <p className="text-green-300 font-bold">{msg.structured.peak_score.opportunity_score}/10</p>
                                            </div>
                                            <div className="bg-slate-900 rounded p-2 text-center">
                                                <p className="text-red-500">Risk</p>
                                                <p className="text-red-300 font-bold">{msg.structured.peak_score.risk_score}/10</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3">
                            <div className="flex gap-1 items-center h-5">
                                <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Suggestion chips */}
            {messages.length <= 1 && (
                <div className="px-5 pb-3 flex flex-wrap gap-2">
                    {SUGGESTIONS.map((s) => (
                        <button
                            key={s}
                            onClick={() => sendMessage(s)}
                            className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-3 py-1.5 rounded-full transition-colors"
                        >
                            {s}
                        </button>
                    ))}
                </div>
            )}

            {/* Input */}
            <div className="px-4 py-3 border-t border-slate-700 bg-slate-800 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
                    placeholder="Ask about career, marriage, finance, health…"
                    disabled={isLoading}
                    className="flex-1 bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none placeholder-slate-500 disabled:opacity-50"
                />
                <button
                    onClick={() => sendMessage(input)}
                    disabled={isLoading || !input.trim()}
                    className="bg-orange-600 hover:bg-orange-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
                >
                    Ask
                </button>
            </div>
        </div>
    );
}
