"use client";

import React, { useState } from "react";
import { Search, Filter, X, Eye, Wifi, Smartphone, MapPin as MapPinIcon } from "lucide-react";
import { useTransactions } from "@/hooks/useTransactions";
import type { TransactionRead } from "@/lib/types";
import { formatCurrency, formatDateTime, cn, getChannelColor, getRiskBg } from "@/lib/utils";

// -----------------------------------------------------------------------------
// Slide-Over Transaction Inspector
// -----------------------------------------------------------------------------
function TransactionInspector({
  tx,
  onClose,
}: {
  tx: TransactionRead;
  onClose: () => void;
}) {
  return (
    <>
      <div className="slide-over-backdrop" onClick={onClose} />
      <div className="slide-over-panel overflow-y-auto">
        <div className="border-b border-navy-700/80 bg-navy-900/90 p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-mono text-xs uppercase tracking-wider font-semibold text-white">Transaction Telemetry</h3>
            <button
              onClick={onClose}
              className="rounded-[3px] border border-navy-700/60 p-1 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1 font-mono text-xs text-indigo-400">{tx.transaction_ref}</p>
        </div>

        <div className="space-y-4 p-4">
          {/* Amount & Channel */}
          <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3.5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Transaction Amount</p>
                <p className="font-mono text-xl font-bold text-white mt-0.5">{formatCurrency(tx.amount)}</p>
              </div>
              <span className={cn("badge font-mono text-xs", getChannelColor(tx.channel))}>{tx.channel}</span>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3.5">
            <h4 className="mb-2 text-[10px] font-mono uppercase tracking-wider text-slate-400">Risk Assessment</h4>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="h-2 w-full overflow-hidden rounded-[2px] bg-navy-800 border border-navy-700/50">
                  <div
                    className="h-full transition-all duration-300"
                    style={{
                      width: `${tx.risk_score}%`,
                      backgroundColor: tx.risk_score >= 80 ? "#ef4444" : tx.risk_score >= 60 ? "#f59e0b" : tx.risk_score >= 40 ? "#3b82f6" : "#10b981",
                    }}
                  />
                </div>
              </div>
              <span className="font-mono text-sm font-bold text-white">{tx.risk_score} / 100</span>
            </div>
            {tx.flagged_pattern && (
              <div className="mt-2.5">
                <span className={cn("badge", getRiskBg("HIGH"))}>
                  {tx.flagged_pattern.replace(/_/g, " ")}
                </span>
              </div>
            )}
          </div>

          {/* Accounts */}
          <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3.5">
            <h4 className="mb-2.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">Entities</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Origin</span>
                <span className="font-mono text-xs text-slate-200">{tx.sender_account_id}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-mono text-[11px] uppercase">Destination</span>
                <span className="font-mono text-xs text-slate-200">{tx.receiver_account_id}</span>
              </div>
            </div>
          </div>

          {/* Device & Network */}
          <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3.5">
            <h4 className="mb-2.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">Device & Telemetry</h4>
            <div className="space-y-2.5 text-xs">
              {tx.device_fingerprint && (
                <div className="flex items-center gap-2">
                  <Smartphone className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="text-slate-400 font-mono text-[11px] uppercase">Device:</span>
                  <span className="font-mono text-xs text-slate-300 truncate">{tx.device_fingerprint}</span>
                </div>
              )}
              {tx.ip_address_str && (
                <div className="flex items-center gap-2">
                  <Wifi className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="text-slate-400 font-mono text-[11px] uppercase">IP:</span>
                  <span className="font-mono text-xs text-slate-300">{tx.ip_address_str}</span>
                </div>
              )}
              {tx.location_city && (
                <div className="flex items-center gap-2">
                  <MapPinIcon className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="text-slate-400 font-mono text-[11px] uppercase">Location:</span>
                  <span className="text-xs text-slate-200">{tx.location_city}, {tx.location_state}</span>
                </div>
              )}
            </div>
          </div>

          {/* Timestamp */}
          <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3.5">
            <h4 className="mb-1 text-[10px] font-mono uppercase tracking-wider text-slate-400">Execution Timeline</h4>
            <p className="font-mono text-xs text-slate-200">{formatDateTime(tx.timestamp)}</p>
            <p className="mt-1 font-mono text-[11px] text-slate-500 uppercase">Status: {tx.status}</p>
          </div>
        </div>
      </div>
    </>
  );
}

// -----------------------------------------------------------------------------
// Transactions Page
// -----------------------------------------------------------------------------
export default function TransactionsPage() {
  const [selectedTx, setSelectedTx] = useState<TransactionRead | null>(null);
  const [channelFilter, setChannelFilter] = useState("");
  const [searchRef, setSearchRef] = useState("");

  const { transactions, pagination, loading, isLive } = useTransactions({
    page: 1,
    page_size: 50,
    channel: channelFilter || undefined,
  });

  const filtered = searchRef
    ? transactions.filter((t) => t.transaction_ref.toLowerCase().includes(searchRef.toLowerCase()))
    : transactions;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-navy-700/60 pb-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">Transaction Intelligence Ledger</h1>
          <p className="mt-0.5 text-xs text-slate-400">Search, filter, and inspect cross-channel transactions with forensic risk telemetry</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[10px] font-mono border",
            isLive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-slate-800/80 text-slate-400 border-slate-700"
          )}>
            <span className={cn("h-1.5 w-1.5 rounded-full", isLive ? "bg-emerald-400" : "bg-slate-400")} />
            {isLive ? "STREAMING" : "OFFLINE / MOCK"}
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-card flex flex-wrap items-center justify-between gap-3 p-3">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by UTR / Reference ID..."
            value={searchRef}
            onChange={(e) => setSearchRef(e.target.value)}
            className="w-full rounded-[4px] border border-navy-700 bg-navy-950/80 py-1.5 pl-8 pr-3 text-xs font-mono text-white placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter className="h-3.5 w-3.5 text-slate-500 mr-1" />
          {["", "UPI", "NEFT", "IMPS", "RTGS"].map((ch) => (
            <button
              key={ch}
              onClick={() => setChannelFilter(ch)}
              className={cn(
                "rounded-[3px] px-2.5 py-1 text-[11px] font-mono font-medium transition-colors",
                channelFilter === ch
                  ? "bg-indigo-600 text-white border border-indigo-500"
                  : "border border-navy-700 bg-navy-800/60 text-slate-400 hover:text-slate-200 hover:bg-navy-800"
              )}
            >
              {ch || "ALL"}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="space-y-2 p-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="skeleton h-9 rounded" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>UTR / REFERENCE</th>
                  <th>CHANNEL</th>
                  <th>AMOUNT (INR)</th>
                  <th>LOCATION</th>
                  <th>RISK SCORE</th>
                  <th>PATTERN</th>
                  <th>TIMESTAMP</th>
                  <th className="text-right">INSPECT</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tx) => (
                  <tr key={tx.id} className="cursor-pointer" onClick={() => setSelectedTx(tx)}>
                    <td className="font-mono text-xs font-medium text-indigo-400">{tx.transaction_ref}</td>
                    <td>
                      <span className={cn("badge font-mono text-[10px]", getChannelColor(tx.channel))}>{tx.channel}</span>
                    </td>
                    <td className="font-mono text-xs font-semibold text-slate-100">{formatCurrency(tx.amount)}</td>
                    <td className="text-xs text-slate-300">{tx.location_city || "—"}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-[2px] bg-navy-800 border border-navy-700/50">
                          <div
                            className="h-full transition-all duration-300"
                            style={{
                              width: `${tx.risk_score}%`,
                              backgroundColor:
                                tx.risk_score >= 80 ? "#ef4444" : tx.risk_score >= 60 ? "#f59e0b" : tx.risk_score >= 40 ? "#3b82f6" : "#10b981",
                            }}
                          />
                        </div>
                        <span className="font-mono text-[11px] font-medium text-slate-300">{tx.risk_score}</span>
                      </div>
                    </td>
                    <td>
                      {tx.flagged_pattern ? (
                        <span className={cn("badge", getRiskBg("HIGH"))}>
                          {tx.flagged_pattern.replace(/_/g, " ")}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-600 font-mono">—</span>
                      )}
                    </td>
                    <td className="font-mono text-[11px] text-slate-400">{formatDateTime(tx.timestamp)}</td>
                    <td className="text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTx(tx);
                        }}
                        className="rounded-[3px] border border-navy-700/60 p-1 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
                        title="Inspect Transaction"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {pagination && (
          <div className="flex items-center justify-between border-t border-navy-700/60 px-4 py-2.5 bg-navy-900/40">
            <p className="font-mono text-[11px] text-slate-400">
              SHOWING {filtered.length} OF {pagination.total_items} RECORDS
            </p>
            <div className="flex gap-1.5">
              <button
                disabled={!pagination.has_prev}
                className="rounded-[3px] border border-navy-700 bg-navy-800/80 px-2.5 py-1 font-mono text-[11px] text-slate-300 disabled:opacity-40 hover:bg-navy-700 hover:text-white transition-colors"
              >
                PREVIOUS
              </button>
              <button
                disabled={!pagination.has_next}
                className="rounded-[3px] border border-navy-700 bg-navy-800/80 px-2.5 py-1 font-mono text-[11px] text-slate-300 disabled:opacity-40 hover:bg-navy-700 hover:text-white transition-colors"
              >
                NEXT
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Slide-over Inspector */}
      {selectedTx && <TransactionInspector tx={selectedTx} onClose={() => setSelectedTx(null)} />}
    </div>
  );
}
