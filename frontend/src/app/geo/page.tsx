"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { AlertTriangle, MapPin as MapPinIcon, Clock, Navigation } from "lucide-react";
import { fetchGeo } from "@/lib/api";
import type { GeoIntelligenceResponse } from "@/lib/types";

// Dynamic import for Leaflet (SSR incompatible)
const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const CircleMarker = dynamic(() => import("react-leaflet").then((m) => m.CircleMarker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });
const Polyline = dynamic(() => import("react-leaflet").then((m) => m.Polyline), { ssr: false });

// City coordinates for impossible travel arcs
const cityCoords: Record<string, [number, number]> = {
  Mumbai: [19.076, 72.8777],
  Delhi: [28.7041, 77.1025],
  Bengaluru: [12.9716, 77.5946],
  Hyderabad: [17.385, 78.4867],
  Chennai: [13.0827, 80.2707],
  Kolkata: [22.5726, 88.3639],
  Pune: [18.5204, 73.8567],
  Jaipur: [26.9124, 75.7873],
};

export default function GeoPage() {
  const [data, setData] = useState<GeoIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [leafletReady, setLeafletReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    // Load leaflet CSS — only inject if not already present
    let link: HTMLLinkElement | null = document.querySelector(
      'link[href*="leaflet"]'
    );
    let didInject = false;
    if (!link) {
      link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
      didInject = true;
    }
    setLeafletReady(true);

    fetchGeo().then((res) => {
      if (!isMounted) return;
      setData(res.data);
      setLoading(false);
    });

    return () => {
      isMounted = false;
      if (didInject && link && link.parentNode) {
        link.parentNode.removeChild(link);
      }
    };
  }, []);

  if (loading || !data || !leafletReady) {
    return (
      <div className="space-y-5 animate-fade-in">
        <div className="skeleton h-10 rounded" />
        <div className="skeleton h-[560px] rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-navy-700/60 pb-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">Geospatial Intelligence Map</h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Geographic fraud density heatmaps and impossible travel velocity vectors across Indian financial corridors
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[10px] font-mono border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          GEO-INTEL ACTIVE
        </div>
      </div>

      {/* Map + Sidebar */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_360px]">
        {/* Map */}
        <div className="glass-card overflow-hidden border border-navy-700/80 rounded-md" style={{ height: 580 }}>
          <MapContainer
            center={[20.5937, 78.9629]}
            zoom={5}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
            className="rounded-none"
          >
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            {/* Regional Clusters */}
            {data.regional_clusters.map((cluster) => (
              <CircleMarker
                key={cluster.city}
                center={[cluster.lat, cluster.lng]}
                radius={Math.max(12, cluster.mule_count * 0.8)}
                pathOptions={{
                  color: cluster.mule_count >= 25 ? "#ef4444" : cluster.mule_count >= 15 ? "#f59e0b" : "#3b82f6",
                  fillColor: cluster.mule_count >= 25 ? "#ef4444" : cluster.mule_count >= 15 ? "#f59e0b" : "#3b82f6",
                  fillOpacity: 0.35,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="p-1 text-center font-mono">
                    <p className="text-xs font-bold text-slate-900">{cluster.city}</p>
                    <p className="text-[11px] text-slate-700">{cluster.mule_count} Active Mule Accounts</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {/* Impossible Travel Arcs */}
            {data.impossible_travel_alerts.map((alert, i) => {
              const origin = cityCoords[alert.origin];
              const dest = cityCoords[alert.destination];
              if (!origin || !dest) return null;
              return (
                <Polyline
                  key={i}
                  positions={[origin, dest]}
                  pathOptions={{
                    color: "#ef4444",
                    weight: 2,
                    dashArray: "6, 6",
                    opacity: 0.8,
                  }}
                />
              );
            })}
          </MapContainer>
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Legend */}
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 border-b border-navy-700/60 pb-2">
              Corridor Legend
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-[2px] bg-red-500" />
                <span className="text-slate-300">Critical Density (25+ Mules)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-[2px] bg-amber-500" />
                <span className="text-slate-300">High Risk Hub (15–24 Mules)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-[2px] bg-blue-500" />
                <span className="text-slate-300">Monitored Zone (&lt;15 Mules)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-3 w-5 border-t-2 border-dashed border-red-500 inline-block" />
                <span className="text-slate-300">Impossible Velocity Arc</span>
              </div>
            </div>
          </div>

          {/* Impossible Travel Alerts */}
          <div className="glass-card p-4">
            <h3 className="mb-3 flex items-center gap-2 text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 border-b border-navy-700/60 pb-2">
              <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
              Impossible Travel Vectors
            </h3>
            <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
              {data.impossible_travel_alerts.map((alert, i) => (
                <div key={i} className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-medium text-indigo-400">{alert.account_number}</span>
                    <span className="rounded-[3px] border border-red-500/30 bg-red-500/10 px-1.5 py-0.5 text-[9px] font-mono font-semibold text-red-400">
                      FLAGGED
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2 text-xs text-slate-200 font-mono">
                    <MapPinIcon className="h-3 w-3 text-blue-400 shrink-0" />
                    <span>{alert.origin}</span>
                    <Navigation className="h-3 w-3 text-red-400 shrink-0" />
                    <span>{alert.destination}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-[10px] font-mono text-slate-400">
                    <span className="flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      {alert.time_gap_minutes}m delta
                    </span>
                    <span>{alert.distance_km.toLocaleString()} km</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Regional Summary */}
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-mono uppercase tracking-wider font-semibold text-slate-200 border-b border-navy-700/60 pb-2">
              Regional Concentration
            </h3>
            <div className="space-y-2">
              {data.regional_clusters
                .sort((a, b) => b.mule_count - a.mule_count)
                .map((cluster) => (
                  <div key={cluster.city} className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300">{cluster.city}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-[2px] bg-navy-800 border border-navy-700/50">
                        <div
                          className="h-full transition-all duration-300"
                          style={{
                            width: `${(cluster.mule_count / 34) * 100}%`,
                            backgroundColor: cluster.mule_count >= 25 ? "#ef4444" : cluster.mule_count >= 15 ? "#f59e0b" : "#3b82f6",
                          }}
                        />
                      </div>
                      <span className="w-5 text-right font-mono font-semibold text-slate-200">{cluster.mule_count}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
