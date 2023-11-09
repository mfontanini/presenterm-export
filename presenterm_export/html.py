import re
from typing import List
from ansi2html import Ansi2HTMLConverter

"""
A magical multiplier that converts a font size in pixels to a font width.

There's probably something somewhere that specifies what the relationship
really is but I found this by trial and error an I'm okay with that.
"""
FONT_SIZE_WIDTH = 0.605


def slide_to_html(slide: str) -> str:
    """
    Convert a slide using ansi escaped code into HTML.

    This performs all necessary conversions to end up with a nice looking HTML.
    This is _very_ tailored to the output of ansi2html and therefore very fragile.
    """
    converter = Ansi2HTMLConverter(markup_lines=True, inline=True)
    html = converter.convert(slide)
    html = html.replace('class="body_foreground body_background"', "")
    html = html.replace("font-size: normal;", "")
    # Remove this as it wraps every line somehow
    html = html.replace('<span id="line-0">', "")
    # Replace last closing line span with a closing div
    html = html.replace("</span>\n</pre>", "</div>\n</pre>")
    # Replace all line spans with divs (keep the span because whitespace)
    html = re.sub('<span id="line-[0-9]+">', '<div class="content-line"><span>', html)

    # Find all line divs and replace their closing tag to be a /div rather than /span
    needle = '<div class="content-line">'
    index = html.find(needle, html.find(needle) + 1)
    while index != -1:
        html = html[:index] + "</div>" + html[index:]
        index = html.find(needle, index + len("</div>") + 1)
    # Replace this as it shows up at the end and adds a fake line
    return html.replace('<div class="content-line"><span></span></div>', "")


def slides_to_html(slides: List[str]) -> str:
    """
    Take a list of slides and convert them into a single chunk of HTML.
    """
    html_slides = [slide_to_html(slide) for slide in slides]
    output = "".join(html_slides)
    # Strip all the closing tags in between <pre>s as this closes body/html multiple
    # times otherwise
    close_needle = "</pre>"
    pre_close_index = output.find(close_needle)
    while pre_close_index != -1:
        next_index = output.find("<pre", pre_close_index)
        if next_index == -1:
            break
        output = output[: pre_close_index + len(close_needle)] + output[next_index:]
        pre_close_index = output.find(close_needle, pre_close_index + 1)
    return output


def find_background_color(html: str) -> str:
    """
    Find the slides' background color.
    """
    matches = re.search('style="background-color: ([^"]+)"', html)
    if matches is None:
        raise Exception("background color not found")
    return matches.groups()[0]
