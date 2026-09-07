import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { RouteDisruptionAnalysis, LocationItem, IncidentReport } from '../types';
import { Layers } from 'lucide-react';

interface LiveGisMapProps {
  routes: RouteDisruptionAnalysis[];
  selectedRouteId: string | null;
  origin: LocationItem | null;
  destination: LocationItem | null;
  incidents: IncidentReport[];
  onSelectRoute: (id: string) => void;
}

const RISK_COLORS: Record<string, string> = {
  LOW: '#10B981',      // Emerald
  MEDIUM: '#F59E0B',   // Amber
  HIGH: '#F97316',     // Orange-Red
  CRITICAL: '#EF4444', // Crimson
};

export const LiveGisMap: React.FC<LiveGisMapProps> = ({
  routes,
  selectedRouteId,
  origin,
  destination,
  incidents,
  onSelectRoute,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const prevRouteIds = useRef<string[]>([]);
  const [isMapReady, setIsMapReady] = useState(false);

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: [
              'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors | NER-GRID Decision System',
          },
        },
        layers: [
          {
            id: 'osm-layer',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [88.5, 27.0], // Siliguri-Gangtok-Assam default center
      zoom: 8.5,
    });

    map.current = m;
    m.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    m.on('load', () => {
      setIsMapReady(true);
    });

    return () => {
      m.remove();
      map.current = null;
      setIsMapReady(false);
    };
  }, []);

  // 2. Render Routes & GeoJSON Layers & Markers
  useEffect(() => {
    if (!isMapReady || !map.current) return;

    const m = map.current;
    renderAll();

    function renderAll() {
      if (!m) return;

      // --- A. Render Markers (Origin, Destination, Incidents) ---
      // Clear previous markers
      markers.current.forEach((mk) => mk.remove());
      markers.current = [];

      // Add Origin Marker (Green Pin)
      if (origin && typeof origin.latitude === 'number' && typeof origin.longitude === 'number') {
        const elOrig = document.createElement('div');
        elOrig.className = 'w-6 h-6 rounded-full bg-emerald-500 border-2 border-white shadow-xl flex items-center justify-center font-bold text-[10px] text-white ring-2 ring-emerald-400/50 cursor-pointer transition-transform hover:scale-110';
        elOrig.innerHTML = 'A';
        elOrig.title = `Origin: ${origin.name} (${origin.state})`;
        const markerOrig = new maplibregl.Marker({ element: elOrig })
          .setLngLat([origin.longitude, origin.latitude])
          .addTo(m);
        markers.current.push(markerOrig);
      }

      // Add Destination Marker (Red Pin)
      if (destination && typeof destination.latitude === 'number' && typeof destination.longitude === 'number') {
        const elDest = document.createElement('div');
        elDest.className = 'w-6 h-6 rounded-full bg-rose-600 border-2 border-white shadow-xl flex items-center justify-center font-bold text-[10px] text-white ring-2 ring-rose-400/50 cursor-pointer transition-transform hover:scale-110';
        elDest.innerHTML = 'B';
        elDest.title = `Destination: ${destination.name} (${destination.state})`;
        const markerDest = new maplibregl.Marker({ element: elDest })
          .setLngLat([destination.longitude, destination.latitude])
          .addTo(m);
        markers.current.push(markerDest);
      }

      // Add Active Field Incidents
      incidents.forEach((inc) => {
        if (inc.latitude && inc.longitude) {
          const elInc = document.createElement('div');
          elInc.className = 'w-4 h-4 rounded bg-amber-500 border border-black shadow-md flex items-center justify-center font-bold text-[8px] text-black animate-pulse';
          elInc.title = `${inc.report_type}: ${inc.location_name}`;
          const mInc = new maplibregl.Marker({ element: elInc })
            .setLngLat([inc.longitude, inc.latitude])
            .addTo(m);
          markers.current.push(mInc);
        }
      });

      // --- B. Remove layers & sources that are no longer in the active routes ---
      const activeRouteList = routes || [];
      const currentRouteIds = new Set(activeRouteList.map((r) => r.route_id));

      prevRouteIds.current.forEach((oldId) => {
        if (!currentRouteIds.has(oldId)) {
          const layerId = `route-layer-${oldId}`;
          const casingId = `route-casing-${oldId}`;
          const sourceId = `route-source-${oldId}`;
          try {
            if (m.getLayer(layerId)) m.removeLayer(layerId);
            if (m.getLayer(casingId)) m.removeLayer(casingId);
            if (m.getSource(sourceId)) m.removeSource(sourceId);
          } catch (e) {
            console.warn(`Error removing layer/source for ${oldId}:`, e);
          }
        }
      });

      // --- C. Add or Update GeoJSON Sources and Layers ---
      activeRouteList.forEach((r) => {
        const sourceId = `route-source-${r.route_id}`;
        const layerId = `route-layer-${r.route_id}`;
        const casingId = `route-casing-${r.route_id}`;
        const isSelected = r.route_id === selectedRouteId;
        const color = RISK_COLORS[r.predicted_risk_level] || '#3B82F6';

        const featureData: any = {
          type: 'Feature',
          properties: { id: r.route_id, name: r.route_name },
          geometry: r.geometry,
        };

        const existingSource = m.getSource(sourceId) as maplibregl.GeoJSONSource | undefined;
        if (existingSource) {
          // Source exists: safely update data without destroying layers
          existingSource.setData(featureData);
          if (m.getLayer(layerId)) {
            m.setPaintProperty(layerId, 'line-color', color);
            m.setPaintProperty(layerId, 'line-width', isSelected ? 5.5 : 3.5);
            m.setPaintProperty(layerId, 'line-opacity', isSelected ? 1.0 : 0.65);
          }
          if (m.getLayer(casingId)) {
            m.setPaintProperty(casingId, 'line-width', isSelected ? 8.5 : 6);
          }
        } else {
          // Create new source
          m.addSource(sourceId, {
            type: 'geojson',
            data: featureData,
          });

          // Dark Outline Casing
          m.addLayer({
            id: casingId,
            type: 'line',
            source: sourceId,
            layout: {
              'line-cap': 'round',
              'line-join': 'round',
            },
            paint: {
              'line-color': '#0B0F19',
              'line-width': isSelected ? 8.5 : 6,
              'line-opacity': 0.8,
            },
          });

          // Main colored route line
          m.addLayer({
            id: layerId,
            type: 'line',
            source: sourceId,
            layout: {
              'line-cap': 'round',
              'line-join': 'round',
            },
            paint: {
              'line-color': color,
              'line-width': isSelected ? 5.5 : 3.5,
              'line-opacity': isSelected ? 1.0 : 0.65,
              'line-dasharray': r.route_id.includes('alternative') ? [2, 1.5] : [1, 0],
            },
          });

          // Click handler for route selection
          m.on('click', layerId, () => {
            onSelectRoute(r.route_id);
          });
          m.on('mouseenter', layerId, () => {
            m.getCanvas().style.cursor = 'pointer';
          });
          m.on('mouseleave', layerId, () => {
            m.getCanvas().style.cursor = '';
          });
        }
      });

      prevRouteIds.current = activeRouteList.map((r) => r.route_id);

      // --- D. Camera Fit Bounds (Include Origin, Destination, & Route Polylines) ---
      const bounds = new maplibregl.LngLatBounds();
      let hasCoords = false;

      if (origin && typeof origin.latitude === 'number' && typeof origin.longitude === 'number') {
        bounds.extend([origin.longitude, origin.latitude]);
        hasCoords = true;
      }
      if (destination && typeof destination.latitude === 'number' && typeof destination.longitude === 'number') {
        bounds.extend([destination.longitude, destination.latitude]);
        hasCoords = true;
      }

      activeRouteList.forEach((r) => {
        if (r.geometry && Array.isArray(r.geometry.coordinates)) {
          r.geometry.coordinates.forEach((coord: any) => {
            if (Array.isArray(coord) && coord.length >= 2) {
              bounds.extend([coord[0], coord[1]]);
              hasCoords = true;
            }
          });
        }
      });

      if (hasCoords && !bounds.isEmpty()) {
        try {
          m.fitBounds(bounds, {
            padding: { top: 70, bottom: 70, left: 70, right: 70 },
            maxZoom: 12,
            duration: 900,
          });
        } catch (err) {
          console.warn('fitBounds error:', err);
        }
      }
    }
  }, [isMapReady, routes, selectedRouteId, origin, destination, incidents, onSelectRoute]);

  return (
    <div className="relative flex-1 h-full w-full bg-[#0B0F19] overflow-hidden">
      {/* Map Container */}
      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />

      {/* Real-Time Geospatial Map Legend */}
      <div className="absolute top-3 left-3 z-10 bg-[#0E1526]/90 backdrop-blur-sm p-2.5 rounded-lg border border-gray-800 shadow-xl text-xs select-none">
        <div className="flex items-center space-x-1.5 font-bold font-mono text-[10px] text-gray-300 uppercase tracking-wider mb-2">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>Disruption Risk Index</span>
        </div>
        <div className="space-y-1 text-[11px] font-mono">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-1.5 rounded-full bg-[#10B981]" />
            <span className="text-gray-300">LOW (0 – 25%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-1.5 rounded-full bg-[#F59E0B]" />
            <span className="text-gray-300">MEDIUM (26 – 50%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-1.5 rounded-full bg-[#F97316]" />
            <span className="text-gray-300">HIGH (51 – 75%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-1.5 rounded-full bg-[#EF4444]" />
            <span className="text-gray-300">CRITICAL (76 – 100%)</span>
          </div>
        </div>
        <div className="mt-2.5 pt-2 border-t border-gray-800 text-[10px] text-gray-400 flex items-center justify-between">
          <span>Source: OSRM + OSM</span>
          <span className="font-mono text-emerald-400">REAL GEOMETRY</span>
        </div>
      </div>
    </div>
  );
};
