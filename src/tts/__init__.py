from pydoover.docker import run_app

from .application import TtsApplication

def main():
    """Run the application."""
    run_app(TtsApplication())
