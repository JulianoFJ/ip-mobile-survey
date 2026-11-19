"""Caso de uso: detectar estruturas de IP num panorama 360° (P6)."""

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from ipsurvey.application.ports import Detector
from ipsurvey.domain.detection import AngularDetection, merge_detections, to_angular
from ipsurvey.domain.geometry.perspective import PerspectiveView, render_view, view_ring


class DetectStructures:
    """Fatia o panorama em vistas planas, detecta em cada uma e junta em ângulos."""

    def __init__(
        self,
        detector: Detector,
        views: Sequence[PerspectiveView] | None = None,
    ) -> None:
        """Recebe o detector (porta) e o conjunto de vistas (padrão: `view_ring()`)."""
        self._detector = detector
        self._views = list(views) if views is not None else view_ring()

    @property
    def views(self) -> list[PerspectiveView]:
        """Vistas usadas, na ordem dos índices registrados nas detecções."""
        return list(self._views)

    def __call__(self, panorama: NDArray[np.uint8]) -> list[AngularDetection]:
        """Detecta estruturas num panorama equirretangular (H × W × 3, uint8)."""
        found: list[AngularDetection] = []
        for i, view in enumerate(self._views):
            image = render_view(panorama, view)
            found.extend(
                to_angular(det, view, view_index=i) for det in self._detector.detect(image)
            )
        return merge_detections(found)
