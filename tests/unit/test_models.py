from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from ipsurvey.domain.errors import CRSMismatchError
from ipsurvey.domain.ids import new_id
from ipsurvey.domain.models import PoleObservation, PoseENU, ProjectedPoint, Segment

T0 = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        PoseENU(
            t=datetime(2026, 1, 1),
            x=0,
            y=0,
            z=0,
            roll=0,
            pitch=0,
            yaw=0,
            sigma_xy=0.02,
            sigma_z=0.03,
        )


def test_entities_are_frozen() -> None:
    p = ProjectedPoint(x=1, y=2, crs="EPSG:31983")
    with pytest.raises(ValidationError):
        p.x = 5  # type: ignore[misc]


def test_crs_format_validated() -> None:
    with pytest.raises(ValidationError, match="EPSG"):
        ProjectedPoint(x=0, y=0, crs="31983")


def test_distance_requires_same_crs() -> None:
    a = ProjectedPoint(x=0, y=0, crs="EPSG:31983")
    b = ProjectedPoint(x=3, y=4, crs="EPSG:31983")
    assert a.distance_xy(b) == pytest.approx(5.0)
    with pytest.raises(CRSMismatchError):
        a.distance_xy(ProjectedPoint(x=3, y=4, crs="EPSG:31982"))


def test_segment_interval_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="posterior"):
        Segment(id=new_id(), capture_id=new_id(), t_start=T0, t_end=T0, length_m=500)
    Segment(
        id=new_id(),
        capture_id=new_id(),
        t_start=T0,
        t_end=T0 + timedelta(minutes=1),
        length_m=500,
    )


def test_confidence_requires_method() -> None:
    pos = ProjectedPoint(x=0, y=0, crs="EPSG:31983")
    with pytest.raises(ValidationError, match="método"):
        PoleObservation(
            id=new_id(),
            segment_id=new_id(),
            position=pos,
            height_m=9.0,
            confidence={"height_m": 0.9},
        )
    obs = PoleObservation(
        id=new_id(),
        segment_id=new_id(),
        position=pos,
        height_m=9.0,
        confidence={"height_m": 0.9},
        method={"height_m": "pca_slices_v1"},
    )
    assert obs.confidence["height_m"] == 0.9


def test_confidence_bounded() -> None:
    pos = ProjectedPoint(x=0, y=0, crs="EPSG:31983")
    with pytest.raises(ValidationError):
        PoleObservation(
            id=new_id(),
            segment_id=new_id(),
            position=pos,
            confidence={"height_m": 1.2},
            method={"height_m": "x"},
        )


def test_ids_are_uuid7_and_ordered() -> None:
    ids = [new_id() for _ in range(50)]
    assert all(i.version == 7 for i in ids)
    assert ids == sorted(ids)
