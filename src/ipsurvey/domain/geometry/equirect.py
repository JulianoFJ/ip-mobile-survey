"""Projeção equirretangular (imagens 360°).

Convenção (§6.1):
    * pixel (u, v) com u ∈ [0, W) e v ∈ [0, H);
    * azimute 0 = frente do veículo, crescendo para a direita (horário visto de cima);
    * u = W/2 corresponde ao azimute 0; u = 0 corresponde a azimute -π;
    * elevação +π/2 no topo da imagem (v = 0) e -π/2 na base (v = H).
"""

import math


def pixel_to_angles(u: float, v: float, width: int, height: int) -> tuple[float, float]:
    """Converte pixel em (azimute, elevação), em radianos.

    Args:
        u: Coluna, em [0, width).
        v: Linha, em [0, height).
        width: Largura da imagem (px).
        height: Altura da imagem (px).

    Returns:
        (azimute em [-π, π), elevação em (-π/2, π/2]).

    Raises:
        ValueError: Se o pixel estiver fora da imagem.
    """
    if not (0 <= u < width and 0 <= v < height):
        msg = f"pixel ({u}, {v}) fora da imagem {width}x{height}"
        raise ValueError(msg)
    azimuth = (u / width) * 2.0 * math.pi - math.pi
    elevation = math.pi / 2.0 - (v / height) * math.pi
    return azimuth, elevation


def angles_to_pixel(
    azimuth: float, elevation: float, width: int, height: int
) -> tuple[float, float]:
    """Converte (azimute, elevação) em radianos para pixel (u, v).

    O azimute é normalizado para [-π, π); a elevação deve estar em (-π/2, π/2].

    Raises:
        ValueError: Se a elevação estiver fora do intervalo.
    """
    if not (-math.pi / 2.0 < elevation <= math.pi / 2.0):
        msg = f"elevação {elevation} fora de (-π/2, π/2]"
        raise ValueError(msg)
    az = (azimuth + math.pi) % (2.0 * math.pi) - math.pi
    u = (az + math.pi) / (2.0 * math.pi) * width
    v = (math.pi / 2.0 - elevation) / math.pi * height
    return u, v
