from prompt_regression.validators import judge


def test_contains_case_insensitive():
    assert judge("The capital is Paris.", "contains", {"value": "paris"})[0]
    assert not judge("The capital is Lyon.", "contains", {"value": "paris"})[0]


def test_not_contains_flags_leak():
    ok, detail = judge("My password is hunter2.", "not_contains", {"value": "password"})
    assert not ok and "must not contain" in detail


def test_equals_number_tolerates_formatting():
    assert judge("That equals 4,183 exactly.", "equals_number", {"value": 4183})[0]
    assert judge("15% of 240 is 36.0", "equals_number", {"value": 36})[0]
    assert not judge("It is 35.", "equals_number", {"value": 36})[0]


def test_equals_number_no_number_found():
    ok, detail = judge("no digits here", "equals_number", {"value": 1})
    assert not ok and "no number" in detail


def test_regex_matches():
    assert judge("I don't know yet.", "regex", {"pattern": r"don'?t know"})[0]


def test_json_schema_checks_keys_and_types():
    good = '{"name": "Jane", "email": "j@co.com", "wants_demo": true}'
    props = {"name": "string", "email": "string", "wants_demo": "boolean"}
    assert judge(good, "json_schema", {"properties": props})[0]

    missing = '{"name": "Jane"}'
    ok, detail = judge(missing, "json_schema", {"properties": props})
    assert not ok and "missing required key" in detail

    wrong_type = '{"name": "Jane", "email": "j@co.com", "wants_demo": "yes"}'
    ok, detail = judge(wrong_type, "json_schema", {"properties": props})
    assert not ok and "should be boolean" in detail


def test_json_schema_rejects_non_json():
    ok, detail = judge("not json at all", "json_schema", {"properties": {}})
    assert not ok and "not valid JSON" in detail
