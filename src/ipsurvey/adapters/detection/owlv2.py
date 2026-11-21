"""Detector zero-shot OWLv2 (Google, Apache-2.0) via Hugging Face Transformers.

Encontra objetos a partir de descrições em texto, sem treino. É a linha de base da
detecção (issue #15) até haver rótulos para treinar um detector próprio.

Precisa do extra `vision` (`uv sync --extra vision`). torch e transformers só são
importados ao construir o detector, então o resto do pacote não depende deles.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.detection import BoxPx, Detection2D, StructureClass

DEFAULT_MODEL = "google/owlv2-base-patch16-ensemble"

#: Descrições em inglês (o modelo foi treinado em inglês). Várias por classe: o OWLv2
#: responde melhor a uma delas dependendo do tipo de poste (concreto, metálico, madeira).
DEFAULT_PROMPTS: Mapping[StructureClass, tuple[str, ...]] = {
    StructureClass.POLE: ("a utility pole", "a street light pole", "a concrete pole"),
    # "a street light" foi descartado: em inglês designa o poste inteiro com a luz.
    StructureClass.LUMINAIRE: (
        "a street lamp head",
        "an LED street light fixture",
        "a cobra head street light",
    ),
    StructureClass.ARM: ("a street light arm",),
}

#: Limiares por classe, escolhidos na avaliação visual do golden `panoramax-br-v0`.
DEFAULT_THRESHOLDS: Mapping[StructureClass, float] = {
    StructureClass.POLE: 0.25,
    StructureClass.LUMINAIRE: 0.20,
    StructureClass.ARM: 0.30,
}


@dataclass(frozen=True, slots=True)
class RawBox:
    """Saída bruta do modelo para uma descrição, antes do pós-processamento."""

    cls: StructureClass
    score: float
    x0: float
    y0: float
    x1: float
    y1: float
    prompt: str = ""


@dataclass(frozen=True)
class PostProcess:
    """Regras aplicadas às caixas brutas.

    Attributes:
        thresholds: Score mínimo por classe.
        min_pole_aspect: Altura/largura mínima de um poste. Elimina fachadas, placas e
            ônibus, que o modelo às vezes confunde com poste.
        max_luminaire_aspect: Altura/largura máxima de uma luminária. Caixas mais altas
            são o poste inteiro marcado como luminária.
        min_size_px: Lado mínimo da caixa; abaixo disso é ruído.
        nms_iou: Sobreposição (IoU) acima da qual duas caixas da mesma classe são a mesma.
    """

    thresholds: Mapping[StructureClass, float] = field(
        default_factory=lambda: dict(DEFAULT_THRESHOLDS)
    )
    min_pole_aspect: float = 2.5
    max_luminaire_aspect: float = 2.0
    min_size_px: float = 4.0
    nms_iou: float = 0.5

    def __call__(self, raw: Sequence[RawBox], width: int, height: int) -> list[Detection2D]:
        """Filtra, suprime duplicatas e converte para `Detection2D`."""
        kept: list[Detection2D] = []
        for cls in StructureClass:
            thr = self.thresholds.get(cls, 1.01)
            cand = []
            for r in raw:
                if r.cls is not cls or r.score < thr:
                    continue
                x0, y0 = max(0.0, r.x0), max(0.0, r.y0)
                x1, y1 = min(float(width), r.x1), min(float(height), r.y1)
                w, h = x1 - x0, y1 - y0
                if w < self.min_size_px or h < self.min_size_px:
                    continue
                if cls is StructureClass.POLE and h / w < self.min_pole_aspect:
                    continue
                if cls is StructureClass.LUMINAIRE and h / w > self.max_luminaire_aspect:
                    continue
                cand.append(Detection2D(cls, min(r.score, 1.0), BoxPx(x0, y0, x1, y1)))
            kept.extend(nms(cand, self.nms_iou))
        return kept


def iou(a: BoxPx, b: BoxPx) -> float:
    """Interseção sobre união de duas caixas."""
    ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    inter = ix * iy
    area = (a.x1 - a.x0) * (a.y1 - a.y0) + (b.x1 - b.x0) * (b.y1 - b.y0) - inter
    return inter / area if area > 0 else 0.0


def nms(dets: Sequence[Detection2D], iou_max: float) -> list[Detection2D]:
    """Supressão de não máximos: mantém a de maior score entre caixas sobrepostas."""
    out: list[Detection2D] = []
    for d in sorted(dets, key=lambda d: -d.score):
        if all(iou(d.box, k.box) <= iou_max for k in out):
            out.append(d)
    return out


class Owlv2Detector:
    """Implementa a porta `Detector` com OWLv2.

    Args:
        model_id: Modelo no Hugging Face Hub (baixado e guardado em cache na 1ª vez).
        prompts: Descrições por classe.
        post: Regras de pós-processamento.
        device: "mps", "cuda" ou "cpu". Padrão: o melhor disponível.
        raw_threshold: Score mínimo pedido ao modelo; abaixo disso nada é devolvido.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        prompts: Mapping[StructureClass, Sequence[str]] = DEFAULT_PROMPTS,
        post: PostProcess | None = None,
        device: str | None = None,
        raw_threshold: float = 0.05,
    ) -> None:
        """Carrega o modelo."""
        import torch
        from transformers import Owlv2ForObjectDetection, Owlv2Processor

        self._torch: Any = torch
        self.device = device or (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
        self.model_id = model_id
        self._processor: Any = Owlv2Processor.from_pretrained(model_id)
        self._model: Any = Owlv2ForObjectDetection.from_pretrained(model_id).to(self.device)
        self._model.eval()
        self._labels: list[tuple[StructureClass, str]] = [
            (cls, text) for cls, texts in prompts.items() for text in texts
        ]
        self.post = post or PostProcess()
        self.raw_threshold = raw_threshold

    def detect_raw(self, image: NDArray[np.uint8]) -> list[RawBox]:
        """Caixas brutas de todas as descrições, com score ≥ `raw_threshold`."""
        from PIL import Image

        torch = self._torch
        h, w = image.shape[:2]
        inputs = self._processor(
            text=[[t for _, t in self._labels]],
            images=Image.fromarray(image),
            return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            outputs = self._model(**inputs)
        # O OWLv2 trabalha num quadrado com preenchimento; target_sizes com o lado maior
        # devolve as caixas nos pixels da imagem original.
        side = max(h, w)
        res = self._processor.post_process_grounded_object_detection(
            outputs, threshold=self.raw_threshold, target_sizes=torch.tensor([[side, side]])
        )[0]
        boxes = res["boxes"].cpu().numpy()
        scores = res["scores"].cpu().numpy()
        labels = res["labels"].cpu().numpy()
        return [
            RawBox(self._labels[int(lab)][0], float(s), *map(float, b), self._labels[int(lab)][1])
            for b, s, lab in zip(boxes, scores, labels, strict=True)
        ]

    def detect(self, image: NDArray[np.uint8]) -> list[Detection2D]:
        """Detecta postes, braços e luminárias (porta `Detector`)."""
        h, w = image.shape[:2]
        return self.post(self.detect_raw(image), w, h)
