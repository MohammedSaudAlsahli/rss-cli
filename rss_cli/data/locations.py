from pathlib import Path

from xdg_base_dirs import xdg_config_home, xdg_data_home


def _rss_dir(root: Path) -> Path:
    """Given a root, ensure and return the rss-cli directory within it."""
    (save_to := root / "rss-cli").mkdir(parents=True, exist_ok=True)
    return save_to


def data_dir() -> Path:
    """The path to the data directory for the application.

    Returns:
        The path to the data directory for the application.

    Note:
        If the directory doesn't exist, it will be created as a side-effect
        of calling this function.
    """
    return _rss_dir(xdg_data_home())


def config_dir() -> Path:
    """The path to the configuration directory for the application.

    Returns:
        The path to the configuration directory for the application.

    Note:
        If the directory doesn't exist, it will be created as a side-effect
        of calling this function.
    """
    return _rss_dir(xdg_config_home())
