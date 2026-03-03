"use client";

// This file is intentionally kept separate so it can be dynamically imported
// with ssr:false. All react-leaflet hooks and Leaflet imports MUST live here.

import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix broken default marker icons (Webpack / Next.js asset path issue)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
    iconRetinaUrl:
        "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
    shadowUrl:
        "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

interface LatLng {
    lat: number;
    lng: number;
}

function ClickHandler({ onLocationSelect }: { onLocationSelect: (ll: LatLng) => void }) {
    useMapEvents({
        click(e) {
            onLocationSelect({ lat: e.latlng.lat, lng: e.latlng.lng });
        },
    });
    return null;
}

interface LeafletMapProps {
    position: LatLng | null;
    onLocationSelect: (ll: LatLng) => void;
}

export default function LeafletMap({ position, onLocationSelect }: LeafletMapProps) {
    return (
        <MapContainer
            center={[20.5937, 78.9629]}
            zoom={4}
            style={{ height: "100%", width: "100%" }}
            scrollWheelZoom={true}
        >
            <TileLayer
                attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickHandler onLocationSelect={onLocationSelect} />
            {position && <Marker position={[position.lat, position.lng]} />}
        </MapContainer>
    );
}
