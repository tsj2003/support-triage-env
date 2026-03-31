"""FastAPI application for the support triage environment."""

from __future__ import annotations

from starlette.responses import RedirectResponse
from openenv.core.env_server.http_server import create_app

try:
    from ..models import SupportTriageAction, SupportTriageObservation
    from .support_triage_environment import SupportTriageEnvironment
except ImportError:
    from models import SupportTriageAction, SupportTriageObservation
    from server.support_triage_environment import SupportTriageEnvironment


app = create_app(
    SupportTriageEnvironment,
    SupportTriageAction,
    SupportTriageObservation,
    env_name="support_triage_env",
    max_concurrent_envs=4,
)

# Redirect root to health endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/health")


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the local development server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
