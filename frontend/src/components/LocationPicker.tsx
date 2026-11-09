import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import { Navigation, Loader2 } from 'lucide-react';

interface LocationPickerProps {
  locationText: string;
  onChange: (val: string) => void;
  onCoordinatesChange?: (lat: number, lng: number) => void;
}

const pinIcon = L.divIcon({
  className: 'custom-pin',
  html: `<div style="background-color: #dc2626; width: 26px; height: 26px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><div style="width: 8px; height: 8px; background: #ffffff; border-radius: 50%; margin: 7px auto;"></div></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

export const LocationPicker: React.FC<LocationPickerProps> = ({
  locationText,
  onChange,
  onCoordinatesChange,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  const [coords, setCoords] = useState<{ lat: number; lng: number }>({
    lat: 28.6139,
    lng: 77.2090, // Default coordinates (New Delhi)
  });
  const [detectingGps, setDetectingGps] = useState(false);
  const [locationNote, setLocationNote] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [coords.lat, coords.lng],
      zoom: 14,
      scrollWheelZoom: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    const marker = L.marker([coords.lat, coords.lng], {
      icon: pinIcon,
      draggable: true,
    }).addTo(map);

    marker.on('dragend', async () => {
      const position = marker.getLatLng();
      updateLocation(position.lat, position.lng);
    });

    map.on('click', (e: L.LeafletMouseEvent) => {
      marker.setLatLng(e.latlng);
      updateLocation(e.latlng.lat, e.latlng.lng);
    });

    mapInstanceRef.current = map;
    markerRef.current = marker;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const setMapPosition = (lat: number, lng: number) => {
    setCoords({ lat, lng });
    if (mapInstanceRef.current && markerRef.current) {
      mapInstanceRef.current.setView([lat, lng], 16);
      markerRef.current.setLatLng([lat, lng]);
    }
  };

  const updateLocation = async (lat: number, lng: number) => {
    setCoords({ lat, lng });
    onCoordinatesChange?.(lat, lng);

    let address = `${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`;
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`, {
        headers: { 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.display_name) {
          const parts = data.display_name.split(',');
          address = parts.slice(0, 3).join(',').trim() + ` [GPS: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E]`;
        }
      }
    } catch {
      // Fallback
    }

    onChange(address);
  };

  // Fallback to IP Geolocation if desktop has no hardware GPS
  const fallbackIpLocation = async () => {
    try {
      const res = await fetch('https://ipapi.co/json/');
      if (res.ok) {
        const data = await res.json();
        if (data.latitude && data.longitude) {
          setMapPosition(data.latitude, data.longitude);
          const cityAddr = `${data.city || 'City'}, ${data.region || ''} [Est. GPS: ${data.latitude.toFixed(4)}° N, ${data.longitude.toFixed(4)}° E]`;
          onChange(cityAddr);
          setLocationNote(`Detected approximate area via Network/Wi-Fi: ${data.city || 'City'}`);
          return;
        }
      }
    } catch {
      // Fallback
    }
    setLocationNote('Could not read hardware GPS. Please click on the map to set exact location.');
  };

  const handleGpsDetect = () => {
    setDetectingGps(true);
    setLocationNote(null);

    if (!navigator.geolocation) {
      fallbackIpLocation().finally(() => setDetectingGps(false));
      return;
    }

    // Try standard accuracy first (faster and works on laptops without satellite GPS)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setDetectingGps(false);
        setMapPosition(latitude, longitude);
        updateLocation(latitude, longitude);
        setLocationNote('Location fetched successfully from device sensors.');
      },
      () => {
        // If device GPS times out (e.g. desktop PC without satellite antenna), fallback to Network IP
        fallbackIpLocation().finally(() => setDetectingGps(false));
      },
      { 
        timeout: 6000, 
        enableHighAccuracy: false, // Standard mode prevents desktop PC satellite timeouts
        maximumAge: 60000 
      }
    );
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
          1. Incident Location & Landmark <span className="text-red-600">*</span>
        </label>
        <button
          type="button"
          onClick={handleGpsDetect}
          disabled={detectingGps}
          className="text-xs font-bold text-blue-700 dark:text-blue-400 hover:underline flex items-center gap-1.5 bg-blue-50 dark:bg-blue-950/40 px-3 py-1 border border-blue-200 dark:border-blue-800 rounded transition disabled:opacity-50"
        >
          {detectingGps ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Detecting Location...</span>
            </>
          ) : (
            <>
              <Navigation className="w-3.5 h-3.5" />
              <span>Auto-Detect GPS Location</span>
            </>
          )}
        </button>
      </div>

      <input
        type="text"
        value={locationText}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter landmark, road name, or municipal ward..."
        className="w-full bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 px-4 py-2.5 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-blue-700"
        required
      />

      {locationNote && (
        <p className="text-[11px] text-blue-700 dark:text-blue-400 font-medium">
          ℹ️ {locationNote}
        </p>
      )}

      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span>Click map or drag the pin 📍 to adjust exact spot</span>
          <span>{coords.lat.toFixed(4)}° N, {coords.lng.toFixed(4)}° E</span>
        </div>
        <div 
          ref={mapContainerRef} 
          className="w-full h-48 border border-slate-300 dark:border-slate-600 z-0 bg-slate-100 dark:bg-slate-800"
        />
      </div>
    </div>
  );
};
