from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import producers as P
from wxgzh_pipeline.secrets import wechat_credentials_present


def test_media_subprocess_env_matches_doctor_dotenv_source(tmp_path, monkeypatch):
    project = tmp_path
    run_dir = project / ".temp" / "wxgzh-pipeline" / "run-obs47"
    run_dir.mkdir(parents=True)
    (project / ".env").write_text(
        "WECHAT_APP_ID=wx-fake-doctor-id\nWECHAT_APP_SECRET=fake-doctor-secret\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("WECHAT_APP_ID", raising=False)
    monkeypatch.delenv("WECHAT_APP_SECRET", raising=False)

    child_env = P._media_subprocess_env(SimpleNamespace(run_dir=run_dir, env={}))
    ok, detail = wechat_credentials_present(child_env)

    assert ok is True
    assert detail == {
        "WECHAT_APP_ID_nonempty": True,
        "WECHAT_APP_SECRET_nonempty": True,
    }
    assert child_env["WECHAT_APP_ID"] == "wx-fake-doctor-id"
    assert child_env["WECHAT_APP_SECRET"] == "fake-doctor-secret"
