import React, { useEffect, useRef } from 'react';
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

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
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

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // 2. Render Routes & GeoJSON Layers
  useEffect(() => {
    if (!map.current) return;

    const m = map.current;
    if (!m.isStyleLoaded()) {
      m.once('load', () => renderLayers());
    } else {
      renderLayers();
    }

    function renderLayers() {
      if (!m) return;

      // Remove existing route layers
      routes.forEach((r) => {
        const sourceId = `route-source-${r.route_id}`;
        const layerId = `route-layer-${r.route_id}`;
        const casingId = `route-casing-${r.route_id}`;

        if (m.getLayer(layerId)) m.removeLayer(layerId);
        if (m.getLayer(casingId)) m.removeLayer(casingId);
        if (m.getSource(sourceId)) m.removeSource(sourceId);
      });

      // Clear existing markers
      markers.current.forEach((mk) => mk.remove());
      markers.current = [];

      if (!routes || routes.length === 0) return;

      const bounds = new maplibregl.LngLatBounds();

      routes.forEach((r) => {
        const sourceId = `route-source-${r.route_id}`;
        const layerId = `route-layer-${r.route_id}`;
        const casingId = `route-casing-${r.route_id}`;
        const isSelected = r.route_id === selectedRouteId;
        const color = RISK_COLORS[r.predicted_risk_level] || '#3B82F6';

        // Register Source
        m.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: { id: r.route_id, name: r.route_name },
            geometry: r.geometry as any,
          },
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
            'line-width': isSelected ? 8 : 6,
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
            'line-width': isSelected ? 5 : 3.5,
            'line-opacity': isSelected ? 1.0 : 0.65,
            'line-dasharray': r.route_id.includes('alternative') ? [2, 1.5] : [1, 0],
          },
        });

        // Click handler for route
        m.on('click', layerId, () => {
          onSelectRoute(r.route_id);
        });

        // Extend bounds
        r.geometry.coordinates.forEach((coord) => {
          bounds.extend(coord as [number, number]);
        });
      });

      // Fit map bounds to show route
      if (!bounds.isEmpty()) {
        m.fitBounds(bounds, { padding: 60, maxZoom: 12, duration: 1000 });
      }

      // Add Origin Marker (Green)
      if (origin) {
        const elOrig = document.createElement('div');
        elOrig.className = 'w-5 h-5 rounded-full bg-emerald-500 border-2 border-white shadow-lg flex items-center justify-center font-bold text-[9px] text-white';
        elOrig.title = `Origin: ${origin.name}`;
        const markerOrig = new maplibregl.Marker({ element: elOrig })
          .setLngLat([origin.longitude, origin.latitude])
          .addTo(m);
        markers.current.push(markerOrig);
      }

      // Add Destination Marker (Red)
      if (destination) {
        const elDest = document.createElement('div');
        elDest.className = 'w-5 h-5 rounded-full bg-rose-600 border-2 border-white shadow-lg flex items-center justify-center font-bold text-[9px] text-white';
        elDest.title = `Destination: ${destination.name}`;
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
    }
  }, [routes, selectedRouteId, origin, destination, incidents, onSelectRoute]);

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
