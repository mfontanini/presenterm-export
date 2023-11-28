from dataclasses import dataclass
import weasyprint

from presenterm_export.html import find_background_color
from presenterm_export.capture import PresentationSize


@dataclass
class PdfOptions:
    font_size: int
    line_height: int
    output_path: str


def generate_pdf(input_html: str, dimensions: PresentationSize, options: PdfOptions):
    """
    Generate a PDF out of the input presentation in HTML form.
    """

    background_color = find_background_color(input_html)
    html = weasyprint.HTML(string=input_html)
    font_size = options.font_size
    line_height = options.line_height
    height = dimensions.rows * line_height
    width = dimensions.columns * font_size * 0.605
    styles = f"""
        pre {{
            margin: 0;
        }}

        span {{
            display: inline-block;
        }}

        body {{
            margin: 0;
            font-size: {font_size}px;
            background-color: {background_color};
            width: {width}px;
        }}

        .content-line {{
            display: inline-block;
            line-height: {line_height}px; 
            margin: 0px;
            width: {width}px;
        }}

        @page {{
            margin: 0;
            height: {height}px;
            width: {width}px;
        }}
"""
    css = weasyprint.CSS(string=styles)
    html.write_pdf(
        target=options.output_path, stylesheets=[css], presentational_hints=True
    )
