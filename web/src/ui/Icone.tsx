// Cópia de @apphouer/ui (HouerIgnis, packages/ui). Na integração ao Ignis, importar do pacote.
import { cn } from "./lib/cn";

/**
 * Ícone Material Symbols (Rounded), decorativo por padrão. Nome cru do catálogo
 * (https://fonts.google.com/icons) — a tabela de ícones por conceito está em tema/ui.py.
 * Com `rotulo`, vira imagem com nome acessível.
 */
export function Icone({ nome, className, cheio, rotulo, tamanho = 20 }: {
  nome: string; className?: string; cheio?: boolean; rotulo?: string; tamanho?: number;
}) {
  return (
    <span
      className={cn("ms shrink-0", cheio && "ms-cheio", className)}
      style={{ fontSize: tamanho, width: tamanho, height: tamanho }}
      aria-hidden={rotulo ? undefined : true}
      role={rotulo ? "img" : undefined}
      aria-label={rotulo}
    >
      {nome}
    </span>
  );
}
