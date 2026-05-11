from __future__ import annotations

"""Utility helpers for path handling, logging, and external solver execution.

This module centralizes the small pieces of shared infrastructure used by the
airfoil cross-section example scripts. The helpers here are intentionally
lightweight and focused on concerns that appear across multiple entry points:

- resolving user-provided paths into absolute paths
- configuring stream/file logging consistently
- managing per-case log files
- launching external solver executables and surfacing failures
"""

import asyncio
import logging
import shutil
from pathlib import Path
import traceback


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def resolve_path(path: str | Path, base_dir: str | Path | None = None) -> Path:
    """Resolve a user-provided path to an absolute path.

    Parameters
    ----------
    path : str or Path
        Input path supplied by the caller. The path may be absolute, relative,
        or use the ``~`` user-home shorthand.
    base_dir : str or Path or None, optional
        Base directory used when ``path`` is relative. If ``None``, relative
        paths are resolved against the current working directory.

    Returns
    -------
    Path
        Fully resolved absolute path.
    """
    resolved_path = Path(path).expanduser()
    if not resolved_path.is_absolute() and base_dir is not None:
        resolved_path = Path(base_dir).expanduser() / resolved_path
    return resolved_path.resolve()


def ensure_root_logging() -> None:
    """Install a default stream logger on the root logger.

    The helper is idempotent. If a stream handler created by this project is
    already present, the function leaves the logging configuration unchanged.

    Returns
    -------
    None
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if any(getattr(handler, "_airfoil_stream_handler", False) for handler in root_logger.handlers):
        return

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    stream_handler._airfoil_stream_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(stream_handler)


def configure_logging(log_file: str | Path) -> logging.Logger:
    """Configure process-wide logging for batch execution.

    Parameters
    ----------
    log_file : str or Path
        File path used for the persistent batch log.

    Returns
    -------
    logging.Logger
        Module logger for the caller. The root logger is configured with both
        a console handler and the requested file handler.
    """
    ensure_root_logging()
    root_logger = logging.getLogger()
    formatter = logging.Formatter(LOG_FORMAT)

    log_file = resolve_path(log_file)
    if not any(
        isinstance(handler, logging.FileHandler)
        and resolve_path(handler.baseFilename) == log_file
        for handler in root_logger.handlers
    ):
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)


def create_case_logger(case_dir: Path, airfoil_name: str) -> logging.Logger:
    """Create or retrieve a logger for one airfoil case directory.

    Parameters
    ----------
    case_dir : Path
        Working directory for the case. The case log file is written inside
        this directory as ``main.log``.
    airfoil_name : str
        Name used to namespace the logger instance.

    Returns
    -------
    logging.Logger
        Logger configured with propagation enabled and a per-case file handler.
    """
    logger = logging.getLogger(f"{__name__}.{airfoil_name}")
    logger.setLevel(logging.INFO)
    logger.propagate = True

    log_file = resolve_path(case_dir / "main.log")
    if not any(
        isinstance(handler, logging.FileHandler)
        and resolve_path(handler.baseFilename) == log_file
        for handler in logger.handlers
    ):
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger


def close_case_logger(logger: logging.Logger) -> None:
    """Detach and close file handlers owned by a case logger.

    Parameters
    ----------
    logger : logging.Logger
        Logger returned by :func:`create_case_logger`.

    Returns
    -------
    None
        The logger remains usable, but any file handlers attached by this
        helper are removed and closed.
    """
    for handler in list(logger.handlers):
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
            handler.close()


async def run_solver_command(
    command: list[str],
    cwd: Path,
    logger: logging.Logger,
    timeout: float | None = None,
) -> None:
    """Run one external solver command and fail loudly on errors.

    Parameters
    ----------
    command : list of str
        Command and arguments passed to :func:`subprocess.run`.
    cwd : Path
        Working directory for the subprocess.
    logger : logging.Logger
        Logger used to record the command execution.
    timeout : float or None, optional
        Maximum allowed runtime in seconds for the subprocess. ``None``
        disables the timeout.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If the executable is not available on ``PATH``.
    TimeoutError
        If the subprocess exceeds ``timeout`` seconds.
    RuntimeError
        If the subprocess exits with a nonzero status.
    """
    executable = command[0]
    if shutil.which(executable) is None:
        raise FileNotFoundError(
            f"Required executable '{executable}' was not found in PATH."
        )

    logger.info("Running command: %s", " ".join(command))
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.communicate()
        raise TimeoutError(
            f"Command timed out after {timeout} seconds: {' '.join(command)}"
        ) from exc
    except asyncio.CancelledError:
        process.kill()
        await process.communicate()
        raise

    completed_stdout = stdout.decode(errors="replace").strip()
    completed_stderr = stderr.decode(errors="replace").strip()
    if process.returncode != 0:
        message = completed_stderr or completed_stdout or "No solver output."
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{message}")


def write_case_error_file(
    case_dir: str | Path,
    exc: BaseException,
    header: str = "Case failed.",
) -> Path:
    """Write an exception traceback to ``error.txt`` inside a case directory.

    Parameters
    ----------
    case_dir : str or Path
        Case working directory where the error report will be written.
    exc : BaseException
        Exception being handled.
    header : str, default="Case failed."
        Short message written before the exception details.

    Returns
    -------
    Path
        Path to the written ``error.txt`` file.
    """
    case_dir = resolve_path(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    error_file = case_dir / "error.txt"
    traceback_text = traceback.format_exc()
    if traceback_text.strip() == "NoneType: None":
        traceback_text = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

    error_file.write_text(
        f"{header}\n\n{type(exc).__name__}: {exc}\n\n{traceback_text}",
        encoding="utf-8",
    )
    return error_file
