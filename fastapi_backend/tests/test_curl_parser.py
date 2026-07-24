from fastapi_backend.services.curl_parser import parse_curl


def test_parse_curl_preserves_json_request_contract():
    result = parse_curl(
        "curl -X POST http://example.test/orders -H 'X-Request-Id: acceptance' -d '{\"order\":\"A-100\"}'"
    )

    assert result == {
        "method": "POST",
        "url": "http://example.test/orders",
        "headers": {"X-Request-Id": "acceptance"},
        "body": {"order": "A-100"},
        "body_type": "raw",
        "content_type": "application/json",
    }


def test_parse_curl_maps_urlencoded_data_to_fields():
    result = parse_curl("curl --data 'name=alice&role=qa' https://example.test/users")

    assert result["method"] == "POST"
    assert result["body"] == {"name": "alice", "role": "qa"}
    assert result["body_type"] == "form-data"
