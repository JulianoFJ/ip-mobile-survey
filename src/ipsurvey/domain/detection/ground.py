"""Distância e altura de um poste a partir de um único panorama (hipótese de chão plano).

Com a câmera a uma altura conhecida `h_cam` sobre um chão plano, o pé do poste visto na
elevação `el_min < 0` está à distância horizontal

    d = h_cam / tan(-el_min)

e o topo, visto em `el_max`, está à altura

    H = h_cam + d · tan(el_max).

É uma primeira estimativa, de um quadro só. Erra quando o chão não é plano (rampa,
meio-fio alto, poste na calçada elevada) ou quando o pé está escondido atrás de um carro.
A triangulação entre quadros (Sprint de geometria) substitui esta estimativa; ela serve
para descartar o que não é poste de IP (placas, hastes, semáforos baixos) e para a
avaliação qualitativa.
"""

import math
from dataclasses import dataclass

from ipsurvey.domain.detection.models import AngularDetection

#: Elevação mínima do pé abaixo do horizonte para a estimativa valer. Perto do horizonte,
#: um erro de 1° no pé vira dezenas de metros de distância.
MIN_FOOT_DEPRESSION = math.radians(2.0)


@dataclass(frozen=True, slots=True)
class GroundEstimate:
    """Estimativa de um quadro só.

    Attributes:
        distance_m: Distância horizontal da câmera ao pé (m).
        height_m: Altura do topo sobre o chão (m). Se o topo foi cortado pela vista, é um
            limite inferior.
        height_is_lower_bound: O topo estava cortado.
    """

    distance_m: float
    height_m: float
    height_is_lower_bound: bool


def ground_estimate(det: AngularDetection, camera_height_m: float) -> GroundEstimate | None:
    """Distância e altura pela hipótese de chão plano.

    Returns:
        A estimativa, ou None se o pé não for confiável: cortado pela vista ou perto
        demais do horizonte (pé acima de -2°).
    """
    if camera_height_m <= 0:
        msg = f"altura da câmera deve ser positiva, recebido {camera_height_m}"
        raise ValueError(msg)
    if det.cut_bottom or det.el_min > -MIN_FOOT_DEPRESSION:
        return None
    d = camera_height_m / math.tan(-det.el_min)
    return GroundEstimate(
        distance_m=d,
        height_m=camera_height_m + d * math.tan(det.el_max),
        height_is_lower_bound=det.cut_top,
    )
