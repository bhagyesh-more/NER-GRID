import React, { useEffect, useState } from 'react';
import { Shield, Clock, Database, AlertTriangle } from 'lucide-react';
import type { SystemHealth, DataOrigin } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  provenanceStatus: DataOrigin;
  isScenarioActive: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, provenanceStatus, isScenarioActive }) => {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const isOnline = health?.status === 'healthy';

  return (
    <header className="h-14 border-b border-gray-800 bg-[#0E1526] px-4 flex items-center justify-between z-30 shrink-0 select-none">
      {/* Brand & Mission Statement */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold tracking-wider text-base text-white font-mono">NER-GRID</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-mono font-semibold">
              SIH26002
            </span>
            {isScenarioActive && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono font-semibold animate-pulse flex items-center space-x-1">
                <AlertTriangle className="w-3 h-3" />
                <span>WHAT-IF SIMULATION ACTIVE</span>
              </span>
            )}
          </div>
          <p className="text-[11px] text-gray-400 font-medium tracking-tight">
            Predictive Logistics & Accessibility Intelligence Network · North Eastern Region
          </p>
        </div>
      </div>

      {/* Real-Time Operational Indicators */}
      <div className="flex items-center space-x-4 text-xs font-mono">
        {/* Backend Connection */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#0B0F19] border border-gray-800">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-gray-300 font-medium">BACKEND:</span>
          <span className={isOnline ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
            {isOnline ? 'ONLINE' : 'CONNECTING...'}
          </span>
        </div>

        {/* Data Provenance Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#0B0F19] border border-gray-800">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-gray-400 font-medium">PROVENANCE:</span>
          <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
            provenanceStatus === 'OBSERVED' ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700' :
            provenanceStatus === 'REPORTED' ? 'bg-purple-900/60 text-purple-300 border border-purple-700' :
            provenanceStatus === 'PREDICTED' ? 'bg-blue-900/60 text-blue-300 border border-blue-700' :
            'bg-amber-900/80 text-amber-200 border border-amber-600 font-extrabold animate-pulse'
          }`}>
            {provenanceStatus}
          </span>
        </div>

        {/* Live Clock */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#0B0F19] border border-gray-800 text-gray-300">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span className="font-semibold">{timeStr}</span>
        </div>
      </div>
    </header>
  );
};
