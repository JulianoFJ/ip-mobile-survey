"""Vistas planas (perspectiva) recortadas de um panorama equirretangular.

Detectores treinados em fotos comuns erram com a distorção da projeção equirretangular,
principalmente perto do topo da imagem, onde ficam braços e luminárias. Por isso cada
panorama é fatiado em vistas planas, a detecção roda em cada vista e os resultados voltam
para ângulos (azimute, elevação), que é a moeda comum do pipeline.

Convenções (as mesmas de `equirect.py`):
    * eixos do veículo: x à direita, y à frente, z para cima;
    * azimute = atan2(x, y): 0 à frente, positivo para a direita, em [-π, π);
    * elevação = atan2(z, √(x² + y²)): positiva para cima;
    * pixel contínuo: o pixel inteiro i cobre [i, i + 1) e seu centro é i + 0,5;
    * na vista, x cresce para a direita e y para baixo; pixels quadrados.
"""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


# ---------------------------------------------------------------- equirretangular (vetorizado)
def equirect_angles_to_pixel(
    azimuth: ArrayLike, elevation: ArrayLike, width: int, height: int
) -> tuple[FloatArray, FloatArray]:
    """Versão vetorizada de `equirect.angles_to_pixel`, sem validação (uso interno em lote).

    Returns:
        (u, v) contínuos; u em [0, width), v em [0, height].
    """
    az = np.asarray(azimuth, dtype=np.float64)
    el = np.asarray(elevation, dtype=np.float64)
    az = np.mod(az + math.pi, 2.0 * math.pi) - math.pi
    u = (az + math.pi) / (2.0 * math.pi) * width
    v = (math.pi / 2.0 - el) / math.pi * height
    return u, v


def equirect_pixel_to_angles(
    u: ArrayLike, v: ArrayLike, width: int, height: int
) -> tuple[FloatArray, FloatArray]:
    """Versão vetorizada de `equirect.pixel_to_angles`, sem validação."""
    uu = np.asarray(u, dtype=np.float64)
    vv = np.asarray(v, dtype=np.float64)
    return uu / width * 2.0 * math.pi - math.pi, math.pi / 2.0 - vv / height * math.pi


def angles_to_unit(azimuth: ArrayLike, elevation: ArrayLike) -> FloatArray:
    """Vetores unitários (…, 3) a partir de azimute e elevação."""
    az = np.asarray(azimuth, dtype=np.float64)
    el = np.asarray(elevation, dtype=np.float64)
    c = np.cos(el)
    return np.stack([c * np.sin(az), c * np.cos(az), np.sin(el)], axis=-1)


def unit_to_angles(d: ArrayLike) -> tuple[FloatArray, FloatArray]:
    """Azimute e elevação de vetores (…, 3), não necessariamente unitários."""
    v = np.asarray(d, dtype=np.float64)
    x, y, z = v[..., 0], v[..., 1], v[..., 2]
    return np.arctan2(x, y), np.arctan2(z, np.hypot(x, y))


# ---------------------------------------------------------------- vista plana
@dataclass(frozen=True)
class PerspectiveView:
    """Câmera virtual plana apontada para (yaw, pitch) dentro do panorama.

    Attributes:
        yaw: Azimute do eixo óptico (rad).
        pitch: Elevação do eixo óptico (rad), em (-π/2, π/2).
        hfov: Campo de visão horizontal (rad), em (0, π).
        width: Largura da vista (px).
        height: Altura da vista (px).
    """

    yaw: float
    pitch: float
    hfov: float
    width: int
    height: int

    def __post_init__(self) -> None:
        """Valida os parâmetros."""
        if not 0 < self.hfov < math.pi:
            msg = f"hfov deve estar em (0, π), recebido {self.hfov}"
            raise ValueError(msg)
        if not -math.pi / 2 < self.pitch < math.pi / 2:
            msg = f"pitch deve estar em (-π/2, π/2), recebido {self.pitch}"
            raise ValueError(msg)
        if self.width <= 0 or self.height <= 0:
            msg = "dimensões da vista devem ser positivas"
            raise ValueError(msg)

    @property
    def focal_px(self) -> float:
        """Distância focal em pixels."""
        return (self.width / 2.0) / math.tan(self.hfov / 2.0)

    @property
    def vfov(self) -> float:
        """Campo de visão vertical (rad)."""
        return 2.0 * math.atan((self.height / 2.0) / self.focal_px)

    def _basis(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        """(frente, direita, cima) da câmera, nos eixos do veículo."""
        sy, cy = math.sin(self.yaw), math.cos(self.yaw)
        sp, cp = math.sin(self.pitch), math.cos(self.pitch)
        forward = np.array([cp * sy, cp * cy, sp])
        right = np.array([cy, -sy, 0.0])
        up = np.array([-sp * sy, -sp * cy, cp])
        return forward, right, up

    def pixel_to_angles(self, x: ArrayLike, y: ArrayLike) -> tuple[FloatArray, FloatArray]:
        """Ângulos (azimute, elevação) de pixels contínuos da vista.

        Args:
            x: Coluna contínua (centro do pixel i em i + 0,5).
            y: Linha contínua, crescendo para baixo.
        """
        f, r, u = self._basis()
        xc = (np.asarray(x, dtype=np.float64) - self.width / 2.0) / self.focal_px
        yc = (self.height / 2.0 - np.asarray(y, dtype=np.float64)) / self.focal_px
        d = f + xc[..., None] * r + yc[..., None] * u
        return unit_to_angles(d)

    def angles_to_pixel(
        self, azimuth: ArrayLike, elevation: ArrayLike
    ) -> tuple[FloatArray, FloatArray, NDArray[np.bool_]]:
        """Projeta ângulos na vista.

        Returns:
            (x, y, na_frente). `na_frente` é False para direções atrás da câmera, onde (x, y)
            não tem significado. Pontos na frente podem cair fora dos limites da vista.
        """
        f, r, u = self._basis()
        d = angles_to_unit(azimuth, elevation)
        zf = d @ f
        in_front = zf > 1e-9
        safe = np.where(in_front, zf, 1.0)
        x = (d @ r) / safe * self.focal_px + self.width / 2.0
        y = self.height / 2.0 - (d @ u) / safe * self.focal_px
        return x, y, in_front

    def equirect_coords(self, pano_width: int, pano_height: int) -> tuple[FloatArray, FloatArray]:
        """Coordenadas (u, v) no panorama a amostrar para cada pixel da vista (h × w)."""
        xs = np.arange(self.width, dtype=np.float64) + 0.5
        ys = np.arange(self.height, dtype=np.float64) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        az, el = self.pixel_to_angles(gx, gy)
        return equirect_angles_to_pixel(az, el, pano_width, pano_height)


def render_view(panorama: NDArray[np.uint8], view: PerspectiveView) -> NDArray[np.uint8]:
    """Recorta uma vista plana do panorama, com interpolação bilinear.

    A costura horizontal (azimute ±π) é contínua; no topo e na base, a borda é repetida.

    Args:
        panorama: Imagem equirretangular (H × W) ou (H × W × C), uint8.
        view: Vista a recortar.

    Returns:
        Imagem (h × w) ou (h × w × C), uint8.
    """
    ph, pw = panorama.shape[:2]
    u, v = view.equirect_coords(pw, ph)
    # Centros de pixel em i + 0,5 → índice contínuo i.
    fu, fv = u - 0.5, np.clip(v - 0.5, 0.0, ph - 1.0)
    u0 = np.floor(fu).astype(np.int64)
    v0 = np.floor(fv).astype(np.int64)
    du, dv = fu - u0, fv - v0
    u0m, u1m = np.mod(u0, pw), np.mod(u0 + 1, pw)
    v1 = np.minimum(v0 + 1, ph - 1)
    img: FloatArray = panorama.astype(np.float64)
    if img.ndim == 3:
        du, dv = du[..., None], dv[..., None]
    out: FloatArray = (
        img[v0, u0m] * (1 - du) * (1 - dv)
        + img[v0, u1m] * du * (1 - dv)
        + img[v1, u0m] * (1 - du) * dv
        + img[v1, u1m] * du * dv
    )
    result: NDArray[np.uint8] = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    return result


def view_ring(
    *,
    n_yaw: int = 8,
    pitches_deg: tuple[float, ...] = (0.0, 35.0),
    hfov_deg: float = 75.0,
    size: int = 1024,
) -> list[PerspectiveView]:
    """Conjunto padrão de vistas quadradas cobrindo o panorama.

    O padrão (8 azimutes × pitch 0° e 35°, FOV 75°) tem sobreposição entre vistas vizinhas,
    para que um poste cortado na borda de uma vista apareça inteiro na outra. A fileira
    inclinada para cima pega braços e luminárias de perto, que ficam acima de 40° de elevação.

    Args:
        n_yaw: Número de azimutes, igualmente espaçados a partir da frente.
        pitches_deg: Elevações do eixo óptico de cada fileira (graus).
        hfov_deg: Campo de visão horizontal (graus).
        size: Lado da vista (px).
    """
    step = 2.0 * math.pi / n_yaw
    return [
        PerspectiveView(
            yaw=math.remainder(k * step, 2.0 * math.pi),
            pitch=math.radians(p),
            hfov=math.radians(hfov_deg),
            width=size,
            height=size,
        )
        for p in pitches_deg
        for k in range(n_yaw)
    ]
