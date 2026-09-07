import React from 'react';
import { 
  Star, 
  Clock, 
  Route, 
  HelpCircle
} from 'lucide-react';
import type { RouteDisruptionAnalysis, RiskLevel, MissionSuitability } from '../types';

interface RouteAnalysisPanelProps {
  routes: RouteDisruptionAnalysis[];
  recommendedRouteId: string;
  selectedRouteId: string | null;
  recommendationReason: string;
  onSelectRoute: (id: string) => void;
}

const RISK_BADGES: Record<RiskLevel, { text: string; bg: string; border: string; color: string }> = {
  LOW: { text: 'LOW RISK', bg: 'bg-emerald-950/60', border: 'border-emerald-700/60', color: 'text-emerald-400' },
  MEDIUM: { text: 'MEDIUM RISK', bg: 'bg-amber-950/60', border: 'border-amber-700/60', color: 'text-amber-400' },
  HIGH: { text: 'HIGH RISK', bg: 'bg-orange-950/60', border: 'border-orange-700/60', color: 'text-orange-400' },
  CRITICAL: { text: 'CRITICAL', bg: 'bg-rose-950/80', border: 'border-rose-600', color: 'text-rose-400' },
};

const SUITABILITY_BADGES: Record<MissionSuitability, { text: string; bg: string; color: string }> = {
  HIGH: { text: 'HIGHLY SUITABLE', bg: 'bg-emerald-900/40', color: 'text-emerald-300' },
  MEDIUM: { text: 'PASSABLE / MODERATE', bg: 'bg-amber-900/40', color: 'text-amber-300' },
  LOW: { text: 'HIGH HAZARD / SLOW', bg: 'bg-orange-900/40', color: 'text-orange-300' },
  CRITICAL_AVOID: { text: 'UNSUITABLE / AVOID', bg: 'bg-rose-900/70', color: 'text-rose-200' },
};

export const RouteAnalysisPanel: React.FC<RouteAnalysisPanelProps> = ({
  routes,
  recommendedRouteId,
  selectedRouteId,
  recommendationReason,
  onSelectRoute,
}) => {
  const selectedRoute = routes.find((r) => r.route_id === selectedRouteId) || routes[0];

  return (
    <aside className="w-96 bg-[#0E1526] border-l border-gray-800 flex flex-col h-full overflow-y-auto shrink-0 select-none text-xs">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-gray-800 bg-[#0B0F19]/60 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Route className="w-4 h-4 text-blue-400" />
          <span className="font-bold text-white tracking-wide uppercase font-mono">Route Evaluation</span>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 font-mono">
          PARETO RANKED
        </span>
      </div>

      <div className="p-3.5 space-y-4 flex-1">
        {/* Route Cards */}
        <div className="space-y-2.5">
          {routes.map((r) => {
            const isRec = r.route_id === recommendedRouteId;
            const isSelected = r.route_id === selectedRoute?.route_id;
            const badge = RISK_BADGES[r.predicted_risk_level] || RISK_BADGES.MEDIUM;
            const suit = SUITABILITY_BADGES[r.mission_suitability] || SUITABILITY_BADGES.MEDIUM;

            return (
              <div
                key={r.route_id}
                onClick={() => onSelectRoute(r.route_id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-[#141E33] shadow-md ring-1 ring-blue-500/40'
                    : 'border-gray-800 bg-[#111827] hover:border-gray-700'
                }`}
              >
                {/* Header with Star Badge */}
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-gray-200 text-xs font-mono">
                    {r.route_name}
                  </span>
                  {isRec && (
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-600 font-mono font-bold text-[10px] flex items-center space-x-1">
                      <Star className="w-3 h-3 fill-current" />
                      <span>RECOMMENDED</span>
                    </span>
                  )}
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono mb-2 bg-[#0B0F19]/60 p-2 rounded border border-gray-800/80">
                  <div>
                    <span className="text-gray-500 block text-[9px] uppercase">ETA (Transit)</span>
                    <span className="font-bold text-gray-100 flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-blue-400" />
                      <span>{r.predicted_duration_minutes}m</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[9px] uppercase">Distance</span>
                    <span className="font-bold text-gray-100">{r.distance_km} km</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[9px] uppercase">Disruption P</span>
                    <span className={`font-bold ${badge.color}`}>{r.disruption_probability}%</span>
                  </div>
                </div>

                {/* Risk Level & Mission Suitability */}
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${badge.bg} ${badge.border} ${badge.color}`}>
                    {badge.text} ({r.predicted_risk_score}/100)
                  </span>
                  <span className={`px-2 py-0.5 rounded border border-gray-700 text-[10px] font-mono ${suit.bg} ${suit.color}`}>
                    {suit.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Route Explainability: "WHY THIS ROUTE?" */}
        {selectedRoute && (
          <div className="bg-[#111827] p-3.5 rounded-lg border border-gray-800 space-y-3">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <div className="flex items-center space-x-1.5">
                <HelpCircle className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-white text-xs font-mono uppercase">Why This Decision?</span>
              </div>
              <span className="text-[10px] font-mono text-gray-400">
                Confidence: <strong className="text-blue-400">{selectedRoute.confidence}%</strong>
              </span>
            </div>

            {/* Recommendation Reason Narrative */}
            <p className="text-[11px] text-gray-300 leading-relaxed font-sans bg-[#0B0F19]/60 p-2.5 rounded border border-gray-800">
              {recommendationReason}
            </p>

            {/* Contributing Factors Breakdown */}
            <div className="space-y-2">
              <span className="text-[10px] text-gray-400 font-semibold tracking-wider uppercase block font-mono">
                Contributing Hazard Signals:
              </span>
              <div className="space-y-1.5">
                {selectedRoute.contributing_factors.map((f, i) => (
                  <div key={i} className="text-[11px] p-2 rounded bg-[#0B0F19] border border-gray-800">
                    <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                      <span className="text-gray-300 font-semibold">{f.factor_name}</span>
                      <span className="text-blue-400 font-bold">Weight: {(f.impact_weight * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-[10px] text-gray-400">{f.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
