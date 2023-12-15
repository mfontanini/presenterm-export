import json
import sys
from importlib.metadata import version
from argparse import REMAINDER, ArgumentParser
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from typing import List, Dict
from dataclass_wizard import JSONWizard

from presenterm_export.capture import capture_slides
from presenterm_export.html import FONT_SIZE_WIDTH, slides_to_html
from presenterm_export.image import ImageMetadata, ImageProcessor
from presenterm_export.pdf import PdfOptions, generate_pdf


@dataclass
class PresentationMetadata(JSONWizard):
    presentation_path: str
    images: List[ImageMetadata]
    commands: List[Dict[str, str]]


@dataclass
class PresentationPath:
    path: str

    def replace_extension(self, new_extension: str) -> str:
        return self.path.removesuffix(".md") + f".{new_extension}"


def run(args, metadata: PresentationMetadata):
    output_directory = TemporaryDirectory()
    print(f"Writing temporary files into {output_directory.name}")

    input_path = PresentationPath(metadata.presentation_path)
    final_pdf_path = input_path.replace_extension("pdf")
    options = PdfOptions(output_path=final_pdf_path, font_size=10, line_height=12)
    char_width = int(options.font_size * FONT_SIZE_WIDTH)

    with open(input_path.path) as fd:
        presentation = fd.read()

    processor = ImageProcessor(output_directory.name, char_width)

    print("Running presentation to capture slide...")
    presentation = capture_slides(
        args.rest, metadata.presentation_path, metadata.commands
    )
    if not presentation.slides:
        raise Exception("could not capture any slides")

    print("Converting slides to HTML...")
    presentation_html = slides_to_html(presentation.slides)
    if args.emit_intermediate:
        persist(presentation_html, input_path.replace_extension("pre.html"))

    print("Replacing images...")
    presentation_html = processor.replace_final_images(
        presentation_html, metadata.images
    )
    if args.emit_intermediate:
        persist(presentation_html, input_path.replace_extension("final.html"))

    print("Generating PDF")
    generate_pdf(presentation_html, presentation.size, options)
    print(f"PDF generation finished, output PDF is at {options.output_path}")


def load_metadata() -> PresentationMetadata:
    raw_metadata = sys.stdin.read()

    try:
        metadata = json.loads(raw_metadata)
    except Exception as e:
        raise Exception(f"Metadata is corrupted: {e}")
    return PresentationMetadata.from_dict(metadata)


def persist(contents: str, path: str):
    with open(path, "w") as fd:
        fd.write(contents)


def main():
    parser = ArgumentParser(
        prog="presenterm-export",
        description="converts presenterm presentations into PDF files",
    )
    parser.add_argument(
        "--emit-intermediate",
        help="whether to emmit intermediate files for testing",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--version",
        help="print the version",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "rest",
        nargs=REMAINDER,
    )

    args = parser.parse_args()
    if args.version:
        print(version("presenterm-export"))
        exit(0)
    metadata = load_metadata()
    run(args, metadata)
