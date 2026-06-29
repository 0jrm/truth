try:
    from importlib.metadata import version

    __version__ = version("truth-memory")
except Exception:
    __version__ = "1.1.1"
