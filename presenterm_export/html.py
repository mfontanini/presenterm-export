import re
from typing import List
from ansi2html import Ansi2HTMLConverter

"""
A magical multiplier that converts a font size in pixels to a font width.

There's probably something somewhere that specifies what the relationship
really is but I found this by trial and error an I'm okay with that.
"""
FONT_SIZE_WIDTH = 0.605


def slide_to_html(slide: str, rows_per_slide: int) -> str:
    """
    Convert a slide using ansi escaped code into HTML.

    This performs all necessary conversions to end up with a nice looking HTML.
    This is _very_ tailored to the output of ansi2html and therefore very fragile.
    """
    converter = Ansi2HTMLConverter(markup_lines=True, inline=True)
    html = converter.convert(slide)
    html = html.replace('class="body_foreground body_background"', "")
    html = html.replace("font-size: normal;", "")
    rows = re.findall(r'<span id="line-[\d]+">(.*)</span>', html)

    # For some reason there's an extra line
    rows = rows[:-1]

    if len(rows) > rows_per_slide:
        print(
            f"Number of rows ({len(rows)}) is larger than expected ({rows_per_slide})"
        )

    # Some slides (e.g. intro slide) can cut short so make sure we have enough
    missing_rows = rows_per_slide - len(rows)
    rows.extend([""] * missing_rows)

    output = ""
    for row in rows:
        if len(row) == 0:
            row = " "
        output += f'    <div class="content-line"><pre>{row}</pre></div>\n'
    return output


def slides_to_html(slides: List[str], rows_per_slide: int) -> str:
    """
    Take a list of slides and convert them into a single chunk of HTML.
    """

    html_slides = [slide_to_html(slide, rows_per_slide) for slide in slides]
    body = ""
    for index, html_slide in enumerate(html_slides):
        body += f"<!-- slide-{index} -->\n\n"
        body += html_slide
    return f"""<html>
<head>
</head>
<body style="color: white">
{body}
</body>
</html>"""


def find_background_color(html: str) -> str:
    """
    Find the slides' background color.
    """
    matches = re.search('style="background-color: ([^"]+)"', html)
    if matches is None:
        raise Exception("background color not found")
    return matches.groups()[0]
