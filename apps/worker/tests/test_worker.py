from gamehost_worker.main import health_check


async def test_health_check() -> None:
    assert await health_check({}) == "ok"
