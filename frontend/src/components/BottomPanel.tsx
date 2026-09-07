import React from 'react';
import { AlertOctagon, CheckCircle2 } from 'lucide-react';
import type { EarlyWarningAlert, RouteDisruptionAnalysis } from '../types';

interface BottomPanelProps {
  alerts: EarlyWarningAlert[];
  isScenarioActive: boolean;
  baselineRoutes: RouteDisruptionAnalysis[];
  scenarioRoutes?: RouteDisruptionAnalysis[];
  changedRisksSummary?: string;
  changedEtaSummary?: string;
}

export const BottomPanel: React.FC<BottomPanelProps> = ({
  alerts,
  isScenarioActive,
  scenarioRoutes,
  changedRisksSummary,
  changedEtaSummary,
}) => {
  if (alerts.length === 0 && !isScenarioActive) {
    return (
      <footer className="h-10 bg-[#0E1526] border-t border-gray-800 px-4 flex items-center justify-between text-xs text-gray-400 select-none font-mono">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>ALL MONITORED CORRIDORS NOMINAL · ZERO UNCONTAINED ACTIVE BLOCKAGES</span>
        </div>
        <span>SYSTEM DISPATCH CLEARANCE: ACTIVE</span>
      </footer>
    );
  }

  return (
    <footer className="border-t border-gray-800 bg-[#0A0E1A] p-3 text-xs select-none z-20 shrink-0 space-y-2">
      {/* Before / After Comparison Bar when Scenario Active */}
      {isScenarioActive && scenarioRoutes && (
        <div className="bg-[#111827] border border-amber-500/50 rounded-lg p-2.5 flex items-center justify-between font-mono shadow-md">
          <div className="flex items-center space-x-3">
            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 font-bold border border-amber-600 text-[10px] animate-pulse">
              WHAT-IF IMPACT
            </span>
            <div className="text-[11px] text-gray-200">
              <span className="text-gray-400">Risk Escalation: </span>
              <strong>{changedRisksSummary || 'Severe risk detected along primary corridor.'}</strong>
            </div>
            <div className="text-[11px] text-gray-200">
              <span className="text-gray-400">ETA Delta: </span>
              <strong>{changedEtaSummary || 'Significant travel slowdown.'}</strong>
            </div>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>CONTINGENCY ROUTE RE-EVALUATED</span>
          </span>
        </div>
      )}

      {/* Early Warning Alerts */}
      {alerts.length > 0 && (
        <div className="flex items-center space-x-2 overflow-x-auto">
          {alerts.map((alert) => (
            <div
              key={alert.alert_id}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded border text-[11px] font-mono shrink-0 ${
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/80 border-rose-600 text-rose-200'
                  : 'bg-amber-950/80 border-amber-600 text-amber-200'
              }`}
            >
              <AlertOctagon className="w-4 h-4 shrink-0" />
              <div className="flex items-center space-x-2">
                <span className="font-bold uppercase tracking-wider">[{alert.severity}]</span>
                <span className="font-semibold">{alert.affected_route}:</span>
                <span className="text-gray-300">{alert.reason}</span>
                <span className="text-gray-400">→ Action: {alert.recommended_action}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </footer>
  );
};
