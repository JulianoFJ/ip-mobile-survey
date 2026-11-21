"use client";

import type { FeatureCollection } from "geojson";
import type { StyleSpecification } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";
import Map, { Layer, NavigationControl, ScaleControl, Source, type MapLayerMouseEvent, type MapRef } from "react-map-gl/maplibre";
import type { Captura, PosteCadastro, Revisao } from "@/dados/tipos";
import { Icone } from "@/ui/Icone";
import { cn } from "@/ui/lib/cn";

/** Mesmos fundos do MapView do Ignis (packages/ui/src/mapa/fundos.ts), sem chave. */
const CARTO = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const ESRI: StyleSpecification = {
  version: 8,
  sources: {
    esri: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      attribution: "Imagens: Esri, Maxar, Earthstar Geographics e a comunidade GIS",
      maxzoom: 19,
    },
  },
  layers: [{ id: "esri", type: "raster", source: "esri" }],
};

export interface MapaResultadosProps {
  capturas: Captura[];
  revisoes: Record<string, Revisao>;
  /** Postes do cadastro (BDGD) para comparar com o levantamento. */
  cadastro?: PosteCadastro[];
  selecionada?: string | null;
  aoSelecionar?: (capturaId: string) => void;
  altura?: number | string;
}

export default function MapaResultados({ capturas, revisoes, cadastro = [], selecionada, aoSelecionar, altura = 520 }: MapaResultadosProps) {
  const mapa = useRef<MapRef>(null);
  const [fundo, setFundo] = useState<"mapa" | "satelite">("mapa");
  const [verCadastro, setVerCadastro] = useState(true);
  const geoCadastro = useMemo<FeatureCollection>(
    () => ({
      type: "FeatureCollection",
      features: cadastro.map((p) => ({
        type: "Feature",
        properties: { id: p.id, n: p.luminarias },
        geometry: { type: "Point", coordinates: [p.lon, p.lat] },
      })),
    }),
    [cadastro],
  );

  const { pontos, postes, raios, limites } = useMemo(() => {
    const pontos: FeatureCollection = { type: "FeatureCollection", features: [] };
    const postes: FeatureCollection = { type: "FeatureCollection", features: [] };
    const raios: FeatureCollection = { type: "FeatureCollection", features: [] };
    let [w, s, e, n] = [180, 90, -180, -90];
    for (const c of capturas) {
      [w, s, e, n] = [Math.min(w, c.lon), Math.min(s, c.lat), Math.max(e, c.lon), Math.max(n, c.lat)];
      const nPostes = c.deteccoes.filter((d) => d.classe === "poste").length;
      pontos.features.push({
        type: "Feature",
        properties: { id: c.id, cidade: c.cidade, postes: nPostes, sel: c.id === selecionada },
        geometry: { type: "Point", coordinates: [c.lon, c.lat] },
      });
      for (const d of c.deteccoes) {
        if (d.classe !== "poste" || d.lat == null || d.lon == null) continue;
        const rev = revisoes[d.id] ?? "pendente";
        postes.features.push({
          type: "Feature",
          properties: { id: d.id, captura: c.id, altura: d.alturaM ?? 0, score: d.score, rev },
          geometry: { type: "Point", coordinates: [d.lon, d.lat] },
        });
        raios.features.push({
          type: "Feature",
          properties: { captura: c.id, rev },
          geometry: { type: "LineString", coordinates: [[c.lon, c.lat], [d.lon, d.lat]] },
        });
      }
    }
    return { pontos, postes, raios, limites: [w, s, e, n] as [number, number, number, number] };
  }, [capturas, revisoes, selecionada]);

  // Quando o conjunto muda (filtro de cidade), reenquadra.
  const chaveLimites = limites.join(",");
  useEffect(() => {
    mapa.current?.fitBounds(limites, { padding: 40, maxZoom: 16, duration: 700 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveLimites]);

  // Ao escolher uma captura, aproxima nela.
  useEffect(() => {
    const c = capturas.find((x) => x.id === selecionada);
    if (c) mapa.current?.flyTo({ center: [c.lon, c.lat], zoom: Math.max(mapa.current.getZoom(), 17.5), duration: 900 });
  }, [selecionada, capturas]);

  const clicar = (e: MapLayerMouseEvent) => {
    const f = e.features?.[0];
    const id = (f?.properties?.captura ?? f?.properties?.id) as string | undefined;
    if (id && aoSelecionar) aoSelecionar(id);
  };

  return (
    <div className="relative overflow-hidden rounded-card border border-borda" style={{ height: altura }}>
      <Map
        ref={mapa}
        initialViewState={{ bounds: limites, fitBoundsOptions: { padding: 40, maxZoom: 16 } }}
        mapStyle={fundo === "mapa" ? CARTO : ESRI}
        interactiveLayerIds={["capturas", "postes"]}
        onClick={clicar}
        cursor="auto"
        style={{ width: "100%", height: "100%" }}
        attributionControl={{ compact: true }}
      >
        <NavigationControl position="top-right" showCompass={false} />
        <ScaleControl position="bottom-left" unit="metric" />
        {verCadastro && (
          <Source id="cadastro" type="geojson" data={geoCadastro}>
            <Layer
              id="cadastro"
              type="circle"
              minzoom={13}
              paint={{
                "circle-radius": ["interpolate", ["linear"], ["zoom"], 13, 2, 17, 4.5, 19, 7],
                "circle-color": "#FFFFFF",
                "circle-stroke-color": "#0F7A53",
                "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 13, 1, 17, 2],
              }}
            />
          </Source>
        )}
        <Source id="raios" type="geojson" data={raios}>
          <Layer
            id="raios"
            type="line"
            minzoom={15}
            paint={{ "line-color": "#E8A24D", "line-width": 1, "line-opacity": 0.55, "line-dasharray": [2, 2] }}
          />
        </Source>
        <Source id="postes" type="geojson" data={postes}>
          <Layer
            id="postes"
            type="circle"
            paint={{
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 2, 16, 4, 19, 8],
              "circle-color": ["match", ["get", "rev"], "confirmada", "#17A672", "rejeitada", "#DC5B52", "#E8A24D"],
              "circle-stroke-color": "#1B3664",
              "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 12, 0, 16, 1],
              "circle-opacity": ["match", ["get", "rev"], "rejeitada", 0.45, 0.95],
            }}
          />
        </Source>
        <Source id="capturas" type="geojson" data={pontos}>
          <Layer
            id="capturas"
            type="circle"
            paint={{
              // O MapLibre só aceita ["zoom"] no interpolate de nível mais alto.
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 4, ["case", ["get", "sel"], 8, 4], 16, ["case", ["get", "sel"], 10, 6]],
              "circle-color": "#1B3664",
              "circle-stroke-color": ["case", ["get", "sel"], "#E8A24D", "#FFFFFF"],
              "circle-stroke-width": ["case", ["get", "sel"], 3, 1.5],
            }}
          />
        </Source>
      </Map>
      <div className="absolute left-3 top-3 flex overflow-hidden rounded-pi border border-borda bg-superficie text-[0.8rem] shadow-card">
        {(["mapa", "satelite"] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFundo(f)}
            aria-pressed={fundo === f}
            className={cn("flex items-center gap-1 px-2.5 py-1.5 font-medium", fundo === f ? "bg-acao-suave text-navy" : "text-texto-fraco hover:bg-superficie-alt")}
          >
            <Icone nome={f === "mapa" ? "map" : "satellite_alt"} tamanho={16} />
            {f === "mapa" ? "Mapa" : "Satélite"}
          </button>
        ))}
        {cadastro.length > 0 && (
          <button
            type="button"
            onClick={() => setVerCadastro((v) => !v)}
            aria-pressed={verCadastro}
            className={cn("flex items-center gap-1 border-l border-borda px-2.5 py-1.5 font-medium", verCadastro ? "bg-sucesso-suave text-sucesso-texto" : "text-texto-fraco hover:bg-superficie-alt")}
          >
            <Icone nome="table_view" tamanho={16} /> Cadastro BDGD
          </button>
        )}
      </div>
      <Legenda comCadastro={cadastro.length > 0 && verCadastro} />
    </div>
  );
}

function Legenda({ comCadastro }: { comCadastro: boolean }) {
  const item = (cor: string, texto: string, borda = "#1B3664") => (
    <li className="flex items-center gap-1.5">
      <span className="h-2.5 w-2.5 rounded-full border" style={{ background: cor, borderColor: borda }} /> {texto}
    </li>
  );
  return (
    <ul className="absolute bottom-8 right-3 space-y-1 rounded-pi border border-borda bg-superficie/95 px-3 py-2 text-[0.75rem] text-texto-fraco shadow-card">
      {item("#1B3664", "Ponto de captura 360°", "#FFFFFF")}
      {item("#E8A24D", "Poste detectado (a revisar)")}
      {item("#17A672", "Poste confirmado")}
      {item("#DC5B52", "Poste rejeitado")}
      {comCadastro && item("#FFFFFF", "Poste do cadastro (BDGD)", "#0F7A53")}
    </ul>
  );
}
