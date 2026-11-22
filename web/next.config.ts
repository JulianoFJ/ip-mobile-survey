import type { NextConfig } from "next";

const config: NextConfig = {
  // Servidor Node enxuto para a imagem Docker (deploy/), como no Ignis.
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  allowedDevOrigins: ["127.0.0.1"],
  devIndicators: false,
  // Mesma convenção do Ignis: a raiz abre a ferramenta.
  async redirects() {
    return [{ source: "/", destination: "/inspecao", permanent: false }];
  },
};

export default config;
