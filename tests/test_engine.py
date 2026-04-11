import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from urllib import error
from unittest.mock import patch

_ENGINE_PATH = Path(__file__).resolve().parents[1] / "engine.py"
_ENGINE_SPEC = spec_from_file_location("root_engine", _ENGINE_PATH)
assert _ENGINE_SPEC is not None
assert _ENGINE_SPEC.loader is not None
engine = module_from_spec(_ENGINE_SPEC)
_ENGINE_SPEC.loader.exec_module(engine)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_handle_github_automation_ignore_unsupported_event(capsys):
    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "push",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run") as run_mock,
        patch.object(engine.request, "urlopen") as urlopen_mock,
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert "Événement sans création de PR automatique." in captured.out
    run_mock.assert_not_called()
    urlopen_mock.assert_not_called()


def test_handle_github_automation_stops_on_git_diff_error(capsys):
    run_results = [
        None,
        None,
        None,
        None,
        type("Result", (), {"returncode": 2})(),
    ]

    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "schedule",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run", side_effect=run_results) as run_mock,
        patch.object(engine.request, "urlopen") as urlopen_mock,
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert (
        "Erreur vérification des changements git pour evolution/phi-mutation."
        in captured.out
    )
    assert run_mock.call_count == 5
    urlopen_mock.assert_not_called()


def test_handle_github_automation_reuses_existing_pull_request(capsys):
    run_results = [
        None,
        None,
        None,
        None,
        type("Result", (), {"returncode": 1})(),
        None,
        None,
    ]

    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
                "PHI_AUTOMATION_BRANCH": "evolution/stable",
                "PHI_BASE_BRANCH": "develop",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run", side_effect=run_results) as run_mock,
        patch.object(
            engine.request,
            "urlopen",
            return_value=_FakeResponse([{"number": 35}]),
        ) as urlopen_mock,
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert "PR déjà ouverte sur evolution/stable" in captured.out
    assert run_mock.call_args_list[-1].args[0] == [
        "git",
        "push",
        "--force-with-lease",
        "origin",
        "evolution/stable",
    ]
    assert urlopen_mock.call_count == 1
    request_obj = urlopen_mock.call_args.args[0]
    assert request_obj.full_url.endswith(
        "/repos/spockoo/phi-complexity/pulls?state=open&head=spockoo%3Aevolution%2Fstable&base=develop"
    )


def test_handle_github_automation_creates_pull_request(capsys):
    run_results = [
        None,
        None,
        None,
        None,
        type("Result", (), {"returncode": 1})(),
        None,
        None,
    ]

    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "schedule",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run", side_effect=run_results),
        patch.object(
            engine.request,
            "urlopen",
            side_effect=[_FakeResponse([]), _FakeResponse({})],
        ) as urlopen_mock,
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert "PR créée sur evolution/phi-mutation" in captured.out
    assert urlopen_mock.call_count == 2
    creation_request = urlopen_mock.call_args.args[0]
    assert creation_request.get_method() == "POST"
    assert creation_request.headers["Authorization"] == "Bearer token"
    assert creation_request.headers["Content-type"] == "application/json"
    assert json.loads(creation_request.data.decode("utf-8")) == {
        "title": "✨ Évolution Structurelle (Phi)",
        "head": "evolution/phi-mutation",
        "base": "main",
        "body": "Rééquilibrage automatique et audit continu des commits non fusionnés.",
    }


def test_handle_github_automation_handles_invalid_json(capsys):
    class _BrokenResponse(_FakeResponse):
        def read(self):
            return b"{not-json"

    run_results = [
        None,
        None,
        None,
        None,
        type("Result", (), {"returncode": 1})(),
        None,
        None,
    ]

    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "schedule",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run", side_effect=run_results),
        patch.object(engine.request, "urlopen", return_value=_BrokenResponse([])),
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert "Réponse API invalide lors de la lecture des PR ouvertes" in captured.out


def test_handle_github_automation_handles_http_error(capsys):
    run_results = [
        None,
        None,
        None,
        None,
        type("Result", (), {"returncode": 1})(),
        None,
        None,
    ]
    http_error = error.HTTPError(
        "https://api.github.com/repos/spockoo/phi-complexity/pulls",
        500,
        "boom",
        hdrs=None,
        fp=None,
    )

    with (
        patch.dict(
            engine.os.environ,
            {
                "GITHUB_EVENT_NAME": "schedule",
                "GITHUB_REPOSITORY": "spockoo/phi-complexity",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ),
        patch.object(engine.subprocess, "run", side_effect=run_results),
        patch.object(engine.request, "urlopen", side_effect=http_error),
    ):
        engine.handle_github_automation()

    captured = capsys.readouterr()
    assert (
        "Échec création/lecture PR pour evolution/phi-mutation dans spockoo/phi-complexity: 500 boom"
        in captured.out
    )
