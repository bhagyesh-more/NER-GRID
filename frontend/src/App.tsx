import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { MissionControl } from './components/MissionControl';
import { LiveGisMap } from './components/LiveGisMap';
import { RouteAnalysisPanel } from './components/RouteAnalysisPanel';
import { BottomPanel } from './components/BottomPanel';
import { FieldReportModal } from './components/FieldReportModal';
import { 
  fetchHealth, 
  fetchLocations, 
  analyzeRouteScenario, 
  fetchIncidents,
  submitIncident
} from './api/client';
import type { 
  SystemHealth, 
  LocationItem, 
  ScenarioAnalysisResponse, 
  MissionType, 
  ScenarioType,
  IncidentReport,
  DataOrigin
} from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [locations, setLocations] = useState<LocationItem[]>([]);
  const [origin, setOrigin] = useState<LocationItem | null>(null);
  const [destination, setDestination] = useState<LocationItem | null>(null);
  const [missionType, setMissionType] = useState<MissionType>('medical_emergency');
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>('baseline');
  
  const [analysis, setAnalysis] = useState<ScenarioAnalysisResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [incidents, setIncidents] = useState<IncidentReport[]>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Initial Data Loading (Health, Locations, Incidents)
  useEffect(() => {
    async function init() {
      try {
        const [hData, locsData, incsData] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchLocations().catch(() => []),
          fetchIncidents().catch(() => []),
        ]);

        if (hData) setHealth(hData);
        if (locsData && locsData.length > 0) {
          setLocations(locsData);
          // Default to Siliguri -> Gangtok (NH-10 corridor)
          const siliguri = locsData.find((l) => l.name === 'Siliguri') || locsData[1] || locsData[0];
          const gangtok = locsData.find((l) => l.name === 'Gangtok') || locsData[0];
          setOrigin(siliguri);
          setDestination(gangtok);
        }
        if (incsData) setIncidents(incsData);
      } catch (err: any) {
        console.error('Initialization error:', err);
      }
    }
    init();
  }, []);

  // 2. Route Scenario Analysis Runner
  const runAnalysis = useCallback(
    async (
      overrideOrigin?: LocationItem,
      overrideDest?: LocationItem,
      overrideMission?: MissionType,
      overrideScenario?: ScenarioType,
    ) => {
      const orig = overrideOrigin || origin;
      const dest = overrideDest || destination;
      const mType = overrideMission || missionType;
      const scType = overrideScenario || selectedScenario;

      if (!orig || !dest) return;

      if (orig.name === dest.name || (orig.latitude === dest.latitude && orig.longitude === dest.longitude)) {
        setErrorMsg('Origin and Destination cannot be identical. Please select distinct endpoints.');
        return;
      }

      setIsLoading(true);
      setErrorMsg(null);

      try {
        // Construct scenario parameters if not baseline
        let scVars = undefined;
        if (scType !== 'baseline') {
          if (scType === 'heavy_rainfall') {
            scVars = { scenario_type: scType, rainfall_increase_mm: 65.0 };
          } else if (scType === 'cloudburst') {
            scVars = { scenario_type: scType, rainfall_increase_mm: 95.0 };
          } else if (scType === 'landslide_event') {
            scVars = { 
              scenario_type: scType, 
              rainfall_increase_mm: 50.0,
              blocked_location_or_corridor: 'NH-10 (Sevoke-Teesta Gorge)' 
            };
          } else if (scType === 'road_blockage') {
            scVars = { 
              scenario_type: scType, 
              blocked_location_or_corridor: 'Rangpo Border Checkpoint' 
            };
          }
        }

        const res = await analyzeRouteScenario({
          origin: { name: orig.name, latitude: orig.latitude, longitude: orig.longitude },
          destination: { name: dest.name, latitude: dest.latitude, longitude: dest.longitude },
          mission_type: mType,
          scenario_variables: scVars,
        });

        setAnalysis(res);
        setSelectedRouteId(res.recommended_route_id);
      } catch (err: any) {
        console.error('Analysis error:', err);
        setErrorMsg(err.message || 'Route analysis failed. Verify backend connectivity.');
      } finally {
        setIsLoading(false);
      }
    },
    [origin, destination, missionType, selectedScenario]
  );

  // Trigger analysis when origin and destination are ready initially
  useEffect(() => {
    if (origin && destination && !analysis) {
      runAnalysis(origin, destination, missionType, selectedScenario);
    }
  }, [origin, destination, analysis, runAnalysis, missionType, selectedScenario]);

  // Handle Swapping Origin / Destination
  const handleSwap = () => {
    if (origin && destination) {
      const temp = origin;
      setOrigin(destination);
      setDestination(temp);
      runAnalysis(destination, temp, missionType, selectedScenario);
    }
  };

  // Handle Scenario Change
  const handleScenarioChange = (s: ScenarioType) => {
    setSelectedScenario(s);
    runAnalysis(origin || undefined, destination || undefined, missionType, s);
  };

  // Handle Mission Type Change
  const handleMissionChange = (m: MissionType) => {
    setMissionType(m);
    runAnalysis(origin || undefined, destination || undefined, m, selectedScenario);
  };

  // Handle Field Report Submission
  const handleReportSubmit = async (report: { location_name: string; report_type: string; description?: string }) => {
    await submitIncident({
      location_name: report.location_name,
      report_type: report.report_type,
      description: report.description,
      latitude: destination?.latitude,
      longitude: destination?.longitude,
    });
    const updatedIncidents = await fetchIncidents().catch(() => []);
    setIncidents(updatedIncidents);
    // Re-evaluate routes with the new field report
    runAnalysis(origin || undefined, destination || undefined, missionType, selectedScenario);
  };

  // Handle Preload Demo Mode (Siliguri -> STNM Hospital Gangtok, Medical Emergency)
  const handlePreloadDemo = () => {
    const siliguri = locations.find((l) => l.name === 'Siliguri') || locations[0];
    const stnm = locations.find((l) => l.name.includes('STNM Hospital')) || locations.find((l) => l.name === 'Gangtok') || locations[1];
    if (siliguri && stnm) {
      setOrigin(siliguri);
      setDestination(stnm);
      setMissionType('medical_emergency');
      setSelectedScenario('baseline');
      runAnalysis(siliguri, stnm, 'medical_emergency', 'baseline');
    }
  };

  // Handle Reset Scenario to Real Data Baseline
  const handleResetScenario = () => {
    setSelectedScenario('baseline');
    runAnalysis(origin || undefined, destination || undefined, missionType, 'baseline');
  };

  // Active routes list (scenario routes if scenario active, otherwise baseline)
  const isScenarioActive = selectedScenario !== 'baseline';
  const activeRoutes = (isScenarioActive && analysis?.scenario_route_analysis)
    ? analysis.scenario_route_analysis
    : (analysis?.baseline_route_analysis || []);

  const provenanceStatus: DataOrigin = isScenarioActive
    ? 'SIMULATED'
    : (analysis?.provenance_status || 'PREDICTED');

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0B0F19] text-gray-100 overflow-hidden select-none">
      {/* 1. Header */}
      <Header 
        health={health} 
        provenanceStatus={provenanceStatus}
        isScenarioActive={isScenarioActive}
      />

      {/* 2. Main Operational Workspace */}
      <main className="flex flex-1 overflow-hidden relative">
        {/* Left: Mission Control */}
        <MissionControl
          locations={locations}
          origin={origin}
          destination={destination}
          missionType={missionType}
          selectedScenario={selectedScenario}
          isLoading={isLoading}
          onSelectOrigin={(loc) => {
            setOrigin(loc);
            runAnalysis(loc, destination || undefined, missionType, selectedScenario);
          }}
          onSelectDestination={(loc) => {
            setDestination(loc);
            runAnalysis(origin || undefined, loc, missionType, selectedScenario);
          }}
          onSwap={handleSwap}
          onChangeMissionType={handleMissionChange}
          onChangeScenario={handleScenarioChange}
          onAnalyze={() => runAnalysis()}
          onOpenReportModal={() => setIsReportModalOpen(true)}
          onPreloadDemo={handlePreloadDemo}
          onResetScenario={handleResetScenario}
        />

        {/* Center: Live GIS Map */}
        <div className="flex-1 flex flex-col relative h-full">
          {errorMsg && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 bg-rose-950/90 border border-rose-600 text-rose-200 px-4 py-2 rounded-lg text-xs font-mono shadow-xl flex items-center space-x-2">
              <span>[SYSTEM ERROR] {errorMsg}</span>
            </div>
          )}
          
          <LiveGisMap
            routes={activeRoutes}
            selectedRouteId={selectedRouteId}
            origin={origin}
            destination={destination}
            incidents={incidents}
            onSelectRoute={(id) => setSelectedRouteId(id)}
          />
        </div>

        {/* Right: Route Analysis & Explainability */}
        {activeRoutes.length > 0 && (
          <RouteAnalysisPanel
            routes={activeRoutes}
            recommendedRouteId={analysis?.recommended_route_id || activeRoutes[0].route_id}
            selectedRouteId={selectedRouteId}
            recommendationReason={analysis?.recommendation_reason || 'Evaluating optimal trade-offs.'}
            onSelectRoute={(id) => setSelectedRouteId(id)}
          />
        )}
      </main>

      {/* 3. Bottom Panel: Early Warnings & Before/After Comparison */}
      <BottomPanel
        alerts={analysis?.early_warnings || []}
        isScenarioActive={isScenarioActive}
        baselineRoutes={analysis?.baseline_route_analysis || []}
        scenarioRoutes={analysis?.scenario_route_analysis}
        changedRisksSummary={analysis?.changed_risks_summary}
        changedEtaSummary={analysis?.changed_eta_summary}
      />

      {/* 4. Field Report Modal */}
      <FieldReportModal
        isOpen={isReportModalOpen}
        locations={locations}
        onClose={() => setIsReportModalOpen(false)}
        onSubmit={handleReportSubmit}
      />
    </div>
  );
};

export default App;
