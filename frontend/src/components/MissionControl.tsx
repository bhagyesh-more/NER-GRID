import React from 'react';
import { 
  Navigation, 
  MapPin, 
  ArrowRightLeft, 
  Flame, 
  HeartPulse, 
  Truck, 
  Package, 
  Play, 
  RefreshCw, 
  FileText,
  Sliders
} from 'lucide-react';
import type { LocationItem, MissionType, ScenarioType } from '../types';

interface MissionControlProps {
  locations: LocationItem[];
  origin: LocationItem | null;
  destination: LocationItem | null;
  missionType: MissionType;
  selectedScenario: ScenarioType;
  isLoading: boolean;
  onSelectOrigin: (loc: LocationItem) => void;
  onSelectDestination: (loc: LocationItem) => void;
  onSwap: () => void;
  onChangeMissionType: (m: MissionType) => void;
  onChangeScenario: (s: ScenarioType) => void;
  onAnalyze: () => void;
  onOpenReportModal: () => void;
}

export const MissionControl: React.FC<MissionControlProps> = ({
  locations,
  origin,
  destination,
  missionType,
  selectedScenario,
  isLoading,
  onSelectOrigin,
  onSelectDestination,
  onSwap,
  onChangeMissionType,
  onChangeScenario,
  onAnalyze,
  onOpenReportModal,
}) => {
  return (
    <aside className="w-80 bg-[#0E1526] border-r border-gray-800 flex flex-col h-full overflow-y-auto shrink-0 select-none text-xs">
      {/* Panel Title */}
      <div className="p-3.5 border-b border-gray-800 bg-[#0B0F19]/60 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Navigation className="w-4 h-4 text-blue-400" />
          <span className="font-bold text-white tracking-wide uppercase font-mono">Mission Control</span>
        </div>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 font-mono">
          STAGE: DISPATCH
        </span>
      </div>

      <div className="p-3.5 space-y-4 flex-1">
        {/* Origin & Destination Selectors */}
        <div className="space-y-2 bg-[#111827] p-3 rounded-lg border border-gray-800">
          <label className="text-gray-400 font-semibold tracking-wider uppercase text-[10px] flex items-center space-x-1.5">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>Origin Point</span>
          </label>
          <select
            className="w-full bg-[#0B0F19] text-gray-100 border border-gray-700 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-blue-500 font-medium"
            value={origin?.name || ''}
            onChange={(e) => {
              const found = locations.find((l) => l.name === e.target.value);
              if (found) onSelectOrigin(found);
            }}
          >
            {locations.map((loc) => (
              <option key={`orig-${loc.id}`} value={loc.name}>
                {loc.name} ({loc.state})
              </option>
            ))}
          </select>

          {/* Quick Swap */}
          <div className="flex justify-center -my-1">
            <button
              onClick={onSwap}
              title="Swap Origin & Destination"
              className="p-1 rounded-full bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors border border-gray-700"
            >
              <ArrowRightLeft className="w-3 h-3" />
            </button>
          </div>

          <label className="text-gray-400 font-semibold tracking-wider uppercase text-[10px] flex items-center space-x-1.5">
            <MapPin className="w-3.5 h-3.5 text-rose-400" />
            <span>Destination Node</span>
          </label>
          <select
            className="w-full bg-[#0B0F19] text-gray-100 border border-gray-700 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-blue-500 font-medium"
            value={destination?.name || ''}
            onChange={(e) => {
              const found = locations.find((l) => l.name === e.target.value);
              if (found) onSelectDestination(found);
            }}
          >
            {locations.map((loc) => (
              <option key={`dest-${loc.id}`} value={loc.name}>
                {loc.name} ({loc.state})
              </option>
            ))}
          </select>
        </div>

        {/* Mission Type Selection */}
        <div className="space-y-2">
          <label className="text-gray-400 font-semibold tracking-wider uppercase text-[10px] flex items-center space-x-1.5">
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            <span>Operational Mission Type</span>
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { id: 'medical_emergency', label: 'Medical Transit', icon: HeartPulse, color: 'text-rose-400 border-rose-900/40 bg-rose-950/20' },
              { id: 'relief_convoy', label: 'Relief Convoy', icon: Truck, color: 'text-amber-400 border-amber-900/40 bg-amber-950/20' },
              { id: 'heavy_freight', label: 'Heavy Freight', icon: Package, color: 'text-blue-400 border-blue-900/40 bg-blue-950/20' },
              { id: 'general_logistics', label: 'General Transit', icon: Navigation, color: 'text-gray-400 border-gray-800 bg-gray-900/40' },
            ].map((m) => {
              const Icon = m.icon;
              const isSelected = missionType === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => onChangeMissionType(m.id as MissionType)}
                  className={`p-2 rounded border text-left flex items-center space-x-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-950/50 text-blue-300 font-semibold ring-1 ring-blue-500/50'
                      : 'border-gray-800 bg-[#111827] text-gray-400 hover:border-gray-700'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isSelected ? 'text-blue-400' : 'text-gray-400'}`} />
                  <span className="text-[11px] leading-tight">{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Primary Action Button */}
        <button
          onClick={onAnalyze}
          disabled={isLoading || !origin || !destination}
          className={`w-full py-2.5 px-4 rounded-lg font-bold font-mono text-xs flex items-center justify-center space-x-2 shadow-lg transition-all ${
            isLoading
              ? 'bg-blue-800 cursor-not-allowed text-gray-300'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/30 active:scale-[0.98]'
          }`}
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>EVALUATING SENSORS & ROUTES...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>ANALYZE MULTI-HAZARD ROUTE</span>
            </>
          )}
        </button>

        {/* What-If Scenario Section */}
        <div className="pt-2 border-t border-gray-800 space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-gray-400 font-semibold tracking-wider uppercase text-[10px] flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              <span>What-If Scenario Simulation</span>
            </label>
            {selectedScenario !== 'baseline' && (
              <span className="text-[9px] px-1 rounded bg-amber-900/60 text-amber-300 font-mono">
                ACTIVE
              </span>
            )}
          </div>
          <div className="space-y-1.5">
            {[
              { id: 'baseline', label: '1. Normal / Observed Conditions' },
              { id: 'heavy_rainfall', label: '2. Monsoonal Surge (+65mm Rain)' },
              { id: 'cloudburst', label: '3. Severe Cloudburst (+95mm Deluge)' },
              { id: 'landslide_event', label: '4. Teesta Gorge Landslide (NH-10 Block)' },
              { id: 'road_blockage', label: '5. Rangpo Border Chokepoint Blockage' },
            ].map((sc) => {
              const isSelected = selectedScenario === sc.id;
              return (
                <button
                  key={sc.id}
                  onClick={() => onChangeScenario(sc.id as ScenarioType)}
                  className={`w-full text-left p-2 rounded text-[11px] border transition-all flex items-center justify-between ${
                    isSelected
                      ? 'border-amber-500/80 bg-amber-950/40 text-amber-200 font-medium'
                      : 'border-gray-800 bg-[#111827] text-gray-400 hover:border-gray-700'
                  }`}
                >
                  <span>{sc.label}</span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 ml-1" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Field Reporting Interface Trigger */}
        <div className="pt-2 border-t border-gray-800">
          <button
            onClick={onOpenReportModal}
            className="w-full py-2 px-3 rounded border border-purple-800/60 bg-purple-950/30 hover:bg-purple-950/50 text-purple-300 font-medium flex items-center justify-center space-x-2 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>SUBMIT FIELD DISRUPTION REPORT</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
