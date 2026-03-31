"""
server/app.py — OpenEnv multi-mode deployment entry point.
Exposes a `main()` function as required by the validator's [project.scripts] check.
"""
import uvicorn


def main():
    """Start the AI Work OS server."""
    uvicorn.run("api.main:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
