import React, { useState } from 'react';
import { X, Send, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react';
import type { LocationItem } from '../types';

interface FieldReportModalProps {
  isOpen: boolean;
  locations: LocationItem[];
  onClose: () => void;
  onSubmit: (report: { location_name: string; report_type: string; description?: string }) => Promise<void>;
}

export const FieldReportModal: React.FC<FieldReportModalProps> = ({
  isOpen,
  locations,
  onClose,
  onSubmit,
}) => {
  const [locationName, setLocationName] = useState(locations[0]?.name || 'Rangpo');
  const [reportType, setReportType] = useState('Landslide');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit({
        location_name: locationName,
        report_type: reportType,
        description: description || undefined,
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1200);
    } catch (err) {
      alert('Failed to submit report. Ensure backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-md bg-[#111827] border border-gray-700 rounded-xl shadow-2xl overflow-hidden font-sans text-xs">
        {/* Modal Header */}
        <div className="px-4 py-3 border-b border-gray-800 bg-[#0E1526] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-purple-400" />
            <span className="font-bold text-white uppercase tracking-wider font-mono">
              Submit Field Disruption Report
            </span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provenance Notice */}
        <div className="bg-purple-950/40 border-b border-purple-900/60 p-2.5 px-4 flex items-center space-x-2 text-[11px] text-purple-300">
          <AlertTriangle className="w-4 h-4 shrink-0 text-purple-400" />
          <span>
            This submission is tagged strictly as <strong>REPORTED</strong> (unverified ground observation).
          </span>
        </div>

        {success ? (
          <div className="p-8 text-center space-y-2">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto animate-bounce" />
            <p className="font-bold text-sm text-gray-100">Field Report Ingested!</p>
            <p className="text-gray-400 text-xs">Triggering automatic route risk recalculation...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 space-y-3.5">
            <div>
              <label className="text-gray-300 font-semibold block mb-1">Corridor Location / Junction</label>
              <input
                type="text"
                className="w-full bg-[#0B0F19] text-gray-100 border border-gray-700 rounded p-2 focus:outline-none focus:border-blue-500 font-mono"
                placeholder="e.g. Rangpo, Teesta Bazaar, Silchar Bypass"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="text-gray-300 font-semibold block mb-1">Disruption Classification</label>
              <select
                className="w-full bg-[#0B0F19] text-gray-100 border border-gray-700 rounded p-2 focus:outline-none focus:border-blue-500"
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
              >
                <option value="Landslide">Landslide / Mud Slip</option>
                <option value="Road Blocked">Road Blocked / Washout</option>
                <option value="Flooding">Flash Flooding / Submergence</option>
                <option value="Severe Traffic">Severe Chokepoint Congestion</option>
                <option value="Accessibility Issue">Bridge Weight / Clearance Restriction</option>
                <option value="Other Disruption">Other Environmental Hazard</option>
              </select>
            </div>

            <div>
              <label className="text-gray-300 font-semibold block mb-1">Incident Description (Optional)</label>
              <textarea
                className="w-full bg-[#0B0F19] text-gray-100 border border-gray-700 rounded p-2 focus:outline-none focus:border-blue-500 h-20 resize-none"
                placeholder="Details: approximate blockage length, single-lane alternating traffic, active rockfall..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="pt-2 flex justify-end space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-1.5 rounded bg-purple-600 hover:bg-purple-500 text-white font-bold flex items-center space-x-1.5 transition-all shadow-md shadow-purple-900/40"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'SUBMITTING...' : 'TRANSMIT REPORT'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
