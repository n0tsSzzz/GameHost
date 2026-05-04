from gamehost_shared.schemas import ProblemDetail


def test_camel_aliases_are_available() -> None:
    problem = ProblemDetail(title="Bad request", status=400, instance="/api/v1/auth/login")

    assert problem.model_dump(by_alias=True)["instance"] == "/api/v1/auth/login"
