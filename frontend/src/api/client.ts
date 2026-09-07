import type { 
  SystemHealth, 
  LocationItem, 
  ScenarioAnalysisResponse, 
  IncidentReport,
  MissionType,
  ScenarioType
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  const resp = await fetch(`${API_BASE}/health`);
  if (!resp.ok) throw new Error(`Health check failed: ${resp.status}`);
  return resp.json();
}

export async function fetchLocations(): Promise<LocationItem[]> {
  const resp = await fetch(`${API_BASE}/api/v1/locations?limit=50`);
  if (!resp.ok) throw new Error(`Failed to load locations: ${resp.status}`);
  return resp.json();
}

export async function analyzeRouteScenario(params: {
  origin: { name: string; latitude: number; longitude: number };
  destination: { name: string; latitude: number; longitude: number };
  mission_type: MissionType;
  scenario_variables?: {
    scenario_type: ScenarioType;
    rainfall_increase_mm?: number;
    blocked_location_or_corridor?: string;
    speed_reduction_pct?: number;
  };
}): Promise<ScenarioAnalysisResponse> {
  const resp = await fetch(`${API_BASE}/api/v1/scenario/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: params.origin,
      destination: params.destination,
      mission_type: params.mission_type,
      scenario_variables: params.scenario_variables,
      alternatives: true,
    }),
  });
  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Scenario analysis failed (${resp.status}): ${errText}`);
  }
  return resp.json();
}

export async function fetchIncidents(): Promise<IncidentReport[]> {
  const resp = await fetch(`${API_BASE}/api/v1/incidents`);
  if (!resp.ok) throw new Error(`Failed to load incidents: ${resp.status}`);
  return resp.json();
}

export async function submitIncident(incident: {
  location_name: string;
  report_type: string;
  description?: string;
  latitude?: number;
  longitude?: number;
}): Promise<IncidentReport> {
  const resp = await fetch(`${API_BASE}/api/v1/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(incident),
  });
  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Failed to submit incident (${resp.status}): ${errText}`);
  }
  return resp.json();
}
