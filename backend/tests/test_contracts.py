from medinote.main import create_app


def test_schema_export_has_no_database_side_effect(settings):
    schema = create_app(settings).openapi()
    assert "/api/health/live" in schema["paths"]
    assert not settings.db_path.exists()
