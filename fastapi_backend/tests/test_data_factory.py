"""
测试数据工厂引擎单元测试
"""
import uuid
from fastapi_backend.services.autotest_data_factory_service import DataFactoryEngine


class TestDataFactoryEngine:

    def test_fixed_value(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("fixed", {"value": "hello"}, "test_field")
        assert val == "hello"

    def test_enum_value(self):
        engine = DataFactoryEngine()
        options = ["a", "b", "c"]
        for _ in range(20):
            val = engine._generate_value("enum", {"options": options}, "test_field")
            assert val in options

    def test_enum_empty_returns_empty(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("enum", {"options": []}, "test_field")
        assert val == ""

    def test_increment(self):
        engine = DataFactoryEngine()
        v1 = engine._generate_value("increment", {"prefix": "U", "start": 1, "step": 1}, "counter")
        v2 = engine._generate_value("increment", {"prefix": "U", "start": 1, "step": 1}, "counter")
        v3 = engine._generate_value("increment", {"prefix": "U", "start": 1, "step": 1}, "counter")
        assert v1 == "U1"
        assert v2 == "U2"
        assert v3 == "U3"

    def test_uuid_default(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("uuid", {}, "id_field")
        assert isinstance(val, str)
        parts = val.split("-")
        assert len(parts) == 5

    def test_uuid_simple(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("uuid", {"version": "simple"}, "id_field")
        assert "-" not in val
        assert len(val) == 32

    def test_uuid_short(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("uuid", {"version": "short"}, "id_field")
        assert len(val) == 8

    def test_timestamp(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("timestamp", {"format": "%Y-%m-%d %H:%M:%S"}, "ts")
        assert isinstance(val, str)
        assert len(val) >= 19

    def test_date_offset(self):
        engine = DataFactoryEngine()
        val_today = engine._generate_value("date_offset", {"format": "%Y-%m-%d", "offset_days": 0}, "date")
        val_tomorrow = engine._generate_value("date_offset", {"format": "%Y-%m-%d", "offset_days": 1}, "date")
        assert isinstance(val_today, str)
        assert val_today != val_tomorrow

    def test_phone_number(self):
        engine = DataFactoryEngine()
        for _ in range(10):
            val = engine._generate_value("phone", {}, "mobile")
            assert len(val) == 11
            assert val.isdigit()

    def test_phone_with_custom_prefix(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("phone", {"prefix": "138"}, "mobile")
        assert val.startswith("138")
        assert len(val) == 11

    def test_email(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("email", {"domains": ["test.com"], "username_prefix": "user"}, "email")
        assert "@test.com" in val
        assert val.startswith("user")

    def test_username(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("username", {"prefixes": ["tester"], "suffix_length": 4}, "name")
        assert val.startswith("tester_")
        parts = val.split("_")
        assert len(parts) == 2
        assert len(parts[1]) == 4

    def test_env_ref_returns_value(self):
        engine = DataFactoryEngine(env_vars={"API_URL": "http://test.local"})
        val = engine._generate_value("env_ref", {"variable_name": "API_URL"}, "url")
        assert val == "http://test.local"

    def test_env_ref_returns_default_when_not_set(self):
        engine = DataFactoryEngine(env_vars={})
        val = engine._generate_value("env_ref", {"variable_name": "MISSING", "default": "fallback"}, "url")
        assert val == "fallback"

    def test_unknown_rule_returns_value_from_config(self):
        engine = DataFactoryEngine()
        val = engine._generate_value("unknown", {"value": "fallback_val"}, "f")
        assert val == "fallback_val"

    def test_generate_preview_structure(self):
        engine = DataFactoryEngine()
        fields = [
            {"field_name": "name", "rule_type": "fixed", "rule_config": {"value": "Alice"}},
            {"field_name": "age", "rule_type": "increment", "rule_config": {"start": 20, "step": 1}},
            {"field_name": "uid", "rule_type": "uuid", "rule_config": {}},
        ]
        result = engine.generate_preview(fields, row_count=5)
        assert result["columns"] == ["name", "age", "uid"]
        assert len(result["rows"]) == 5
        assert len(result["rows"][0]) == 3

    def test_generate_preview_max_20_rows(self):
        engine = DataFactoryEngine()
        fields = [{"field_name": "x", "rule_type": "fixed", "rule_config": {"value": "test"}}]
        result = engine.generate_preview(fields, row_count=100)
        assert len(result["rows"]) == 20

    def test_generate_dataset_exact_rows(self):
        engine = DataFactoryEngine()
        fields = [{"field_name": "x", "rule_type": "fixed", "rule_config": {"value": "test"}}]
        result = engine.generate_dataset(fields, row_count=3)
        assert len(result["rows"]) == 3
        assert result["row_count"] == 3

    def test_generate_dataset_no_row_limit(self):
        engine = DataFactoryEngine()
        fields = [{"field_name": "x", "rule_type": "fixed", "rule_config": {"value": "test"}}]
        result = engine.generate_dataset(fields, row_count=50)
        assert len(result["rows"]) == 50