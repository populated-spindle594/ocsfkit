from ocsfkit.paths import extract_json_path, set_dotted


def test_json_path_extraction() -> None:
    source = {"userIdentity": {"userName": "alice"}}
    assert extract_json_path(source, "$.userIdentity.userName") == "alice"


def test_dotted_target_assignment() -> None:
    target: dict[str, object] = {}
    set_dotted(target, "actor.user.name", "alice")
    set_dotted(target, "resources[].name", "i-123")
    assert target["actor"] == {"user": {"name": "alice"}}
    assert target["resources"] == [{"name": "i-123"}]

