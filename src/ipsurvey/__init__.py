"""ipsurvey: levantamento móvel de ativos de iluminação pública."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ipsurvey")
except PackageNotFoundError:  # pragma: no cover - pacote não instalado
    __version__ = "0.0.0"

PIPELINE_VERSION = __version__
