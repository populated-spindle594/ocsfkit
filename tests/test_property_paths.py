from hypothesis import given
from hypothesis import strategies as st

from ocsfkit.paths import get_dotted, set_dotted
from ocsfkit.privacy import scan_value
from ocsfkit.redact import redact_value
from ocsfkit.transforms import severity_id_to_text, severity_text_to_id

PATH_PART = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), min_codepoint=48),
    min_size=1,
    max_size=12,
).filter(lambda value: value.isidentifier())


@given(PATH_PART, PATH_PART, st.one_of(st.text(max_size=30), st.integers(), st.booleans()))
def test_set_then_get_dotted_round_trips(parent: str, child: str, value: object) -> None:
    target: dict[str, object] = {}
    path = f"{parent}.{child}"
    set_dotted(target, path, value)
    assert get_dotted(target, path) == value


@given(st.sampled_from(["unknown", "informational", "low", "medium", "high", "critical"]))
def test_severity_text_round_trip(text: str) -> None:
    severity_id = severity_text_to_id(text)
    assert severity_text_to_id(severity_id_to_text(severity_id)) == severity_id


@given(st.emails())
def test_redact_removes_email_findings(email: str) -> None:
    redacted = redact_value({"email": email})
    assert not scan_value(redacted)
