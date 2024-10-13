import os
from dataclasses import dataclass
from typing import Dict, List
from time import sleep
from tempfile import NamedTemporaryFile
import libtmux


@dataclass
class PresentationSize:
    columns: int
    rows: int


@dataclass
class Presentation:
    slides: List[str]
    size: PresentationSize


def capture_slides(args: List[str], commands: List[Dict[str, str]]) -> Presentation:
    """
    Capture the slides for a presentation.

    This uses tmux to run presenterm and capture every slide by following the given
    list of commands.
    """
    stderr_file = NamedTemporaryFile()
    size = os.get_terminal_size()
    tmux_server = libtmux.Server()
    command = " ".join([f"'{arg}'" for arg in args]) + f" 2> {stderr_file.name}"
    print(f"Running {command}")
    session = tmux_server.new_session(
        session_name="presenterm-capturer",
        attach=False,
        kill_session=True,
        x=size.columns,
        y=size.lines,
        window_command=command,
    )
    try:
        return _capture(session, commands, stderr_file)
    finally:
        try:
            session.kill_session()
        except:
            pass


def _capture(
    session: libtmux.session.Session,
    commands: List[Dict[str, str]],
    stderr_file: NamedTemporaryFile,
) -> Presentation:
    if session is None:
        raise Exception("session not started")
    slides = []
    pane = session.attached_pane
    if pane is None:
        raise Exception("no attached pane")
    sleep(1)
    width = int(session.window_width)
    height = int(session.window_height)
    for command in commands:
        command_type = command["type"]
        if command_type == "capture":
            captured_lines = pane.cmd("capture-pane", "-e", "-J", "-p").stdout
            if len(captured_lines) != height:
                # tmux 3.3a lies about the session height so we add an extra one
                captured_lines.append("")
            slide = "\n".join(captured_lines) + "\n"
            slides.append(slide)
            print(f"Captured {len(slides)} slides so far...")
        elif command_type == "wait_for_change":
            sleep(0.5)
        elif command_type:
            pane.send_keys(command["keys"])
    if width is None or height is None:
        raise Exception("no width/height")
    size = PresentationSize(
        columns=width,
        rows=height,
    )
    print(f"Captured {len(slides)} slides")
    stderr = stderr_file.read()
    if stderr:
        raise Exception(stderr.decode("utf8"))
    return Presentation(slides, size)
