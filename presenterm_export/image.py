import base64
import os
from math import ceil
from typing import List, Optional
from dataclasses import dataclass

from presenterm_export.html import find_background_color


@dataclass
class ImageMetadata:
    path: Optional[str]
    contents: Optional[str]
    color: int


class ImageProcessor:
    def __init__(self, output_directory: str, char_size: int):
        self._char_size = char_size
        self._output_directory = output_directory
        self._generated_image_count = 0

    def replace_final_images(self, contents: str, images: List[ImageMetadata]) -> str:
        """
        Replace images in the given HTML contents.

        This replaces images found in the prepare step with their real version.
        """
        background_color = find_background_color(contents)
        for image in images:
            color = f"{image.color:06x}"
            if image.path:
                image_path = image.path
            elif image.contents:
                image_path = self._dump_generated_image(image.contents)
            else:
                raise Exception("image has no path nor contents")
            print(f"Transforming color block #{color} into image {image.path}")
            contents = self._transform_color(
                contents, color, image_path, background_color
            )
        return contents

    def _dump_generated_image(self, base64_contents: str) -> str:
        contents = base64.b64decode(base64_contents)
        filename = f"{self._generated_image_count}.png"
        self._generated_image_count += 1

        path = os.path.join(self._output_directory, filename)
        with open(path, "wb") as fd:
            fd.write(contents)
        return path

    @staticmethod
    def _replace_image(contents: str, old_path: str, new_path: str, index: int) -> str:
        index = contents.find(old_path, index)
        if index == -1:
            raise Exception(f"could not find image {old_path}")
        return contents[:index] + new_path + contents[index + len(old_path) :]

    def _transform_color(
        self, contents: str, color: str, image_path: str, background_color: str
    ) -> str:
        color = f"#{color.upper()}"
        needle = f'<span style="color: {color}'
        image_index = contents.find(needle)
        if image_index == -1:
            raise Exception(f"image color {color} not found")
        width = self._compute_width(contents, color)
        contents = self._replace_ascii_pixels(contents, needle, image_index)
        image_tag = f'<img width="{width}" src="file://{image_path}" style="position: absolute" />'
        contents = contents[:image_index] + image_tag + contents[image_index:]
        contents = contents.replace(color, background_color)
        return contents

    def _compute_width(self, contents: str, color: str) -> int:
        needle = f'<span style="color: {color}; background-color: {color}">'
        start_index = contents.find(needle)
        end_tag = contents.find(">", start_index)
        next_tag = contents.find("<", end_tag)
        total_chars = next_tag - end_tag - 1
        return ceil(total_chars * self._char_size)

    def _replace_ascii_pixels(
        self, contents: str, needle: str, start_index: int
    ) -> str:
        while start_index != -1:
            end_tag = contents.find(">", start_index)
            next_tag = contents.find("<", end_tag)
            amount_to_be_stripped = next_tag - end_tag - 1
            # If there's any pixels here replace them white whitespace so they don't
            # show up as characters behind the image.
            if amount_to_be_stripped > 0:
                replacement = " " * amount_to_be_stripped
                contents = contents[: end_tag + 1] + replacement + contents[next_tag:]
            start_index = contents.find(needle, start_index + 1)
        return contents
