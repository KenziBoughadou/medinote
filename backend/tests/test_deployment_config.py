import importlib.util


def test_config(root):
    spec = importlib.util.spec_from_file_location(
        "check", root / "scripts/check_deployment_config.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.check_deployment_config(root)
