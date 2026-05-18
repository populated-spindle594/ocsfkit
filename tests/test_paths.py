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


def test_json_path_array_index() -> None:
    source = {"items": [{"name": "first"}, {"name": "second"}]}
    assert extract_json_path(source, "$.items[1].name") == "second"


def test_json_path_array_filter() -> None:
    source = {"items": [{"type": "a", "name": "one"}, {"type": "b", "name": "two"}]}
    assert extract_json_path(source, "$.items[?type==b].name") == ["two"]
