export type DataOrigin = 'OBSERVED' | 'REPORTED' | 'PREDICTED' | 'SIMULATED';

export type MissionType = 'medical_emergency' | 'relief_convoy' | 'heavy_freight' | 'general_logistics';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type MissionSuitability = 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL_AVOID';

export type ScenarioType = 
  | 'baseline'
  | 'heavy_rainfall'
  | 'cloudburst'
  | 'road_blockage'
  | 'landslide_event'
  | 'flood_inundation';

export interface LocationItem {
  id: string;
  name: string;
  state: string;
  district?: string;
  latitude: number;
  longitude: number;
  elevation_m?: number;
  location_type: string;
  provenance_status: DataOrigin;
  geometry?: {
    type: string;
    coordinates: [number, number];
  };
}

export interface ContributingFactor {
  factor_name: string;
  impact_weight: number;
  description: string;
  signal_type: string;
}

export interface RouteDisruptionAnalysis {
  route_id: string;
  route_name: string;
  distance_km: number;
  baseline_duration_minutes: number;
  predicted_duration_minutes: number;
  current_risk_score: number;
  predicted_risk_score: number;
  predicted_risk_level: RiskLevel;
  disruption_probability: number;
  confidence: number;
  mission_score?: number;
  is_fastest?: boolean;
  is_lowest_risk?: boolean;
  is_recommended?: boolean;
  contributing_factors: ContributingFactor[];
  mission_suitability: MissionSuitability;
  expected_impact: string;
  geometry: {
    type: string;
    coordinates: [number, number][];
  };
}

export interface EarlyWarningAlert {
  alert_id: string;
  severity: 'INFO' | 'WARNING' | 'ALERT' | 'CRITICAL';
  affected_route: string;
  reason: string;
  confidence: number;
  timestamp: string;
  recommended_action: string;
}

export interface ScenarioAnalysisResponse {
  prediction_id: string;
  timestamp: string;
  provenance_status: DataOrigin;
  mission_type: MissionType;
  input_sources: string[];
  features_used: string[];
  baseline_route_analysis: RouteDisruptionAnalysis[];
  scenario_route_analysis?: RouteDisruptionAnalysis[];
  recommended_route_id: string;
  recommendation_reason: string;
  changed_risks_summary?: string;
  changed_eta_summary?: string;
  early_warnings: EarlyWarningAlert[];
}

export interface IncidentReport {
  id: string;
  location_name: string;
  report_type: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  provenance_status: DataOrigin;
  is_verified: boolean;
  reported_at: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  problem_statement: string;
  timestamp: string;
  geographic_scope: string;
  provenance_enforced: boolean;
}
