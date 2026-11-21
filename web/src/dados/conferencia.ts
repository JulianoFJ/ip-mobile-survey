/**
 * Conferência dos arquivos no navegador, antes do envio: formato 360° (2:1) e GPS no EXIF.
 * Pega no escritório o que costuma voltar do campo errado (câmera em modo foto comum,
 * GPS desligado), sem precisar subir gigabytes para descobrir.
 */

export interface ResultadoImagem {
  nome: string;
  bytes: number;
  largura?: number;
  altura?: number;
  equirretangular?: boolean;
  temGps?: boolean;
  erro?: string;
}

/** Procura a tag GPSInfo (0x8825) no IFD0 do EXIF. Lê só o começo do arquivo. */
export async function temGpsNoExif(arquivo: Blob): Promise<boolean> {
  const buf = new DataView(await arquivo.slice(0, 256 * 1024).arrayBuffer());
  if (buf.byteLength < 4 || buf.getUint16(0) !== 0xffd8) return false; // não é JPEG
  let p = 2;
  while (p + 4 < buf.byteLength) {
    if (buf.getUint8(p) !== 0xff) return false;
    const marcador = buf.getUint8(p + 1);
    const tam = buf.getUint16(p + 2);
    if (marcador === 0xe1 && p + 10 < buf.byteLength && buf.getUint32(p + 4) === 0x45786966) {
      const tiff = p + 10; // depois de "Exif\0\0"
      const le = buf.getUint16(tiff) === 0x4949;
      const ifd0 = tiff + buf.getUint32(tiff + 4, le);
      if (ifd0 + 2 > buf.byteLength) return false;
      const n = buf.getUint16(ifd0, le);
      for (let i = 0; i < n; i++) {
        const e = ifd0 + 2 + i * 12;
        if (e + 2 > buf.byteLength) break;
        if (buf.getUint16(e, le) === 0x8825) return true;
      }
      return false;
    }
    if (marcador === 0xda) return false; // começou a imagem sem EXIF
    p += 2 + tam;
  }
  return false;
}

export async function conferirImagem(arquivo: File): Promise<ResultadoImagem> {
  const r: ResultadoImagem = { nome: arquivo.name, bytes: arquivo.size };
  try {
    const bmp = await createImageBitmap(arquivo);
    r.largura = bmp.width;
    r.altura = bmp.height;
    bmp.close();
    r.equirretangular = Math.abs(r.largura / r.altura - 2) < 0.02;
  } catch {
    r.erro = "Não consegui abrir a imagem";
  }
  try {
    r.temGps = await temGpsNoExif(arquivo);
  } catch {
    r.temGps = false;
  }
  return r;
}

export function tamanhoLegivel(bytes: number): string {
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}
