"""Segmentação do chão com OneFormer treinado no ADE20K (SHI Labs, código e pesos MIT).

Linha de base para as larguras da via (ADR 0008). O ADE20K tem termos de uso próprios
(voltados a pesquisa): antes de uso comercial em produção, revisar com o jurídico ou
retreinar com imagens próprias rotuladas.

Precisa do extra `vision`. torch e transformers só são importados ao construir.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.extraction.cross_section import GroundClass

DEFAULT_MODEL = "shi-labs/oneformer_ade20k_swin_large"

#: Nomes do ADE20K (id2label do modelo) → classe do chão. Casamento pelo primeiro termo.
ADE_PARA_CHAO: dict[str, GroundClass] = {
    "road": GroundClass.ROAD,
    "sidewalk": GroundClass.SIDEWALK,
    "path": GroundClass.SIDEWALK,
    "grass": GroundClass.VEGETATION,
    "plant": GroundClass.VEGETATION,
    "earth": GroundClass.VEGETATION,
    "field": GroundClass.VEGETATION,
    "flower": GroundClass.VEGETATION,
    "car": GroundClass.VEHICLE,
    "truck": GroundClass.VEHICLE,
    "van": GroundClass.VEHICLE,
    "bus": GroundClass.VEHICLE,
    "minibike": GroundClass.VEHICLE,
    "bicycle": GroundClass.VEHICLE,
}


def tabela_de_classes(id2label: dict[int, str]) -> NDArray[np.uint8]:
    """Tabela id do ADE20K → `GroundClass` (o que não está no mapa vira OTHER)."""
    lut = np.zeros(max(id2label) + 1, np.uint8)
    for i, nome in id2label.items():
        termo = nome.split(",")[0].strip().lower()
        lut[i] = ADE_PARA_CHAO.get(termo, GroundClass.OTHER)
    return lut


class OneFormerGroundSegmenter:
    """Implementa a porta `GroundSegmenter`."""

    def __init__(self, model_id: str = DEFAULT_MODEL, device: str | None = None) -> None:
        """Carrega o modelo (float32: o MPS não aceita os buffers float64 do original)."""
        import torch
        from transformers import OneFormerForUniversalSegmentation, OneFormerProcessor

        self._torch: Any = torch
        self.device = device or (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
        self.model_id = model_id
        self._proc: Any = OneFormerProcessor.from_pretrained(model_id)
        self._model: Any = (
            OneFormerForUniversalSegmentation.from_pretrained(model_id)
            .to(torch.float32)
            .to(self.device)
            .eval()
        )
        self._lut = tabela_de_classes({int(k): v for k, v in self._model.config.id2label.items()})

    def segment(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Rótulos `GroundClass` por pixel (H × W)."""
        from PIL import Image

        h, w = image.shape[:2]
        inp = self._proc(
            images=Image.fromarray(image), task_inputs=["semantic"], return_tensors="pt"
        ).to(self.device)
        with self._torch.no_grad():
            out = self._model(**inp)
        seg = (
            self._proc.post_process_semantic_segmentation(out, target_sizes=[(h, w)])[0]
            .cpu()
            .numpy()
        )
        return self._lut[seg]
