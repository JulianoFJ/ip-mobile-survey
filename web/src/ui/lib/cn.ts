// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Junta classes do Tailwind resolvendo conflitos (o `cn` do shadcn/ui). */
export function cn(...entradas: ClassValue[]): string {
  return twMerge(clsx(entradas));
}
