def test_mywebtemplate_demo_routers_are_not_registered():
    from server import app

    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert not any(path.startswith("/api/v1/sample") for path in route_paths)
    assert not any(path.startswith("/api/v1/transaction") for path in route_paths)
