import os
from dataclasses import dataclass
from typing import Dict, List
from time import sleep
import libtmux


@dataclass
class PresentationSize:
    columns: int
    rows: int


@dataclass
class Presentation:
    slides: List[str]
    size: PresentationSize


def capture_slides(
    presenterm_path: str, presentation_path: str, commands: List[Dict[str, str]]
):
    """
    Capture the slides for a presentation.

    This uses tmux to run presenterm and capture every slide by following the given
    list of commands.
    """
    size = os.get_terminal_size()
    tmux_server = libtmux.Server()
    session = tmux_server.new_session(
        session_name="presenterm-capturer",
        attach=False,
        kill_session=True,
        x=size.columns,
        y=size.lines,
        window_command=f"{presenterm_path} --export {presentation_path}",
    )
    try:
        return _capture(session, commands)
    finally:
        session.kill_session()


def _capture(
    session: libtmux.session.Session,
    commands: List[Dict[str, str]],
) -> Presentation:
    if session is None:
        raise Exception("session not started")
    slides = []
    pane = session.attached_pane
    if pane is None:
        raise Exception("no attached pane")
    sleep(1)
    for command in commands:
        command_type = command["type"]
        if command_type == "capture":
            captured_text = pane.cmd("capture-pane", "-e", "-J", "-p").stdout
            slide = "\n".join(captured_text) + "\n"
            slides.append(slide)
            print(f"Captured {len(slides)} slides so far...")
        elif command_type == "wait_for_change":
            sleep(0.5)
        elif command_type:
            pane.send_keys(command["keys"])
    width = session.window_width
    height = session.window_height
    if width is None or height is None:
        raise Exception("no width/height")
    size = PresentationSize(
        columns=int(width),
        rows=int(height),
    )
    print(f"Captured {len(slides)} slides")
    return Presentation(slides, size)
