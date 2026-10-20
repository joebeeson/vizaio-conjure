from dataclasses import FrozenInstanceError

import pytest

from vizaio_conjure import ConjureTarget, VizioNamespace


def test_defaults_are_friendly_and_normalized() -> None:
    target = ConjureTarget("http://example.test/app")
    assert target.app_id == "17"
    assert target.namespace == 4
    assert target.name_space == 4


@pytest.mark.parametrize("value", [VizioNamespace.CONJURE, "CONJURE", "conjure", 4, "4"])
def test_namespace_accepts_enum_name_and_numeric_forms(value: object) -> None:
    assert ConjureTarget("http://example.test/app", name_space=value).namespace == 4


def test_unknown_numeric_namespace_is_allowed_for_future_firmware() -> None:
    assert ConjureTarget("http://example.test/app", name_space=9).namespace == 9


@pytest.mark.parametrize(
    "url",
    ["", "example.test/app", "ftp://example.test/app", "http://user:pass@example.test/app"],
)
def test_url_validation_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(ValueError):
        ConjureTarget(url)


def test_target_is_frozen() -> None:
    target = ConjureTarget("http://example.test/app")
    with pytest.raises(FrozenInstanceError):
        target.url = "http://other.test/"  # type: ignore[misc]
