import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import "@/ui/base.css";
import { Provedores } from "./provedores";

// Mesmas fontes do Ignis, servidas localmente.
const inter = localFont({
  src: "./fontes/inter-latin-wght-normal.woff2",
  variable: "--pi-fonte-inter",
  weight: "100 900",
  display: "swap",
});
const sora = localFont({
  src: "./fontes/sora-latin-wght-normal.woff2",
  variable: "--pi-fonte-sora",
  weight: "100 800",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "Inspeção de campo", template: "%s · Ignis" },
  description: "Ignis — análise dos resultados da inspeção de campo de iluminação pública",
};

export const viewport: Viewport = { themeColor: "#F4F6FA" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${sora.variable}`}>
      <body>
        <Provedores>{children}</Provedores>
      </body>
    </html>
  );
}
