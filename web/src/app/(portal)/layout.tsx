import type { ReactNode } from "react";
import { Casca } from "@/componentes/Casca";

export default function LayoutPortal({ children }: { children: ReactNode }) {
  return <Casca>{children}</Casca>;
}
