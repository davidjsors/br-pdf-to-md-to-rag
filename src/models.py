"""
Modelos de dados centrais para a arquitetura de orquestração do Comitê de Especialistas v2.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from pathlib import Path


class ZoneType(Enum):
    """Tipos de zona detectados pelo Radar Espacial."""
    TEXT = auto()
    TABLE = auto()
    IMAGE = auto()
    TITLE = auto()
    HEADER = auto()
    FOOTER = auto()
    LIST = auto()
    UNKNOWN = auto()


@dataclass
class Zone:
    """Uma zona individual detectada dentro de uma página."""
    zone_type: ZoneType
    page_number: int
    content: str = ""
    bbox: Optional[tuple] = None  # (x0, y0, x1, y1)
    metadata: dict = field(default_factory=dict)


@dataclass
class PageManifest:
    """Manifesto de uma página PDF após a varredura do Radar."""
    page_number: int
    zones: list[Zone] = field(default_factory=list)

    @property
    def has_tables(self) -> bool:
        return any(z.zone_type == ZoneType.TABLE for z in self.zones)

    @property
    def has_images(self) -> bool:
        return any(z.zone_type == ZoneType.IMAGE for z in self.zones)

    @property
    def is_text_only(self) -> bool:
        return not self.has_tables and not self.has_images


@dataclass
class DocumentManifest:
    """Manifesto completo do documento após a varredura do Radar."""
    pdf_path: Path
    pages: list[PageManifest] = field(default_factory=list)
    total_pages: int = 0

    @property
    def pages_with_tables(self) -> list[int]:
        return [p.page_number for p in self.pages if p.has_tables]

    @property
    def pages_with_images(self) -> list[int]:
        return [p.page_number for p in self.pages if p.has_images]


@dataclass
class StageResult:
    """Resultado de uma etapa de processamento."""
    stage_name: str
    content: str = ""
    tables: list[str] = field(default_factory=list)
    visuals: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class OrchestratorResult:
    """Resultado final do orquestrador após todas as etapas."""
    final_markdown: str = ""
    winner_description: str = ""
    stats: dict = field(default_factory=dict)
    mdeval_score: float = 0.0
    success: bool = True
    error: Optional[str] = None
