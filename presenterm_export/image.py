from math import ceil
from typing import List
from dataclasses import dataclass
from PIL import Image

from presenterm_export.html import find_background_color

BASE_COLOR = 0xFFBAD3


@dataclass
class ImageMetadata:
    content_path: str
    full_path: str
    line: int
    column: int


class ImageProcessor:
    def __init__(self, output_directory: str, char_size: int):
        self._images = {}
        self._char_size = char_size
        self._output_directory = output_directory
        self._next_color = BASE_COLOR

    def prepare_images(self, contents: str, images: List[ImageMetadata]) -> str:
        """
        Prepare the images in the presentation's contents.

        This replaces every image with a new image of the same size as the original
        but made up of purely one color. This makes it easy to spot in the output later
        on, which lets us replace it with the real thing once we get to the HTML stage.
        """
        # Iterate in reverse so we don't invalidate indexes.
        images = sorted(
            images, key=lambda image: (image.line, image.column), reverse=True
        )
        front_matter_end = ImageProcessor._find_front_matter_end(contents)
        line_lengths = ImageProcessor._build_cumulative_line_lengths(contents)
        for image in images:
            color = self._build_next_color()
            new_path = self._generate_image(image.full_path, color)
            self._images[color] = image.full_path
            print(
                f"Assigning color {color} to image {image.content_path}, replacing with {new_path}"
            )

            offset = line_lengths[image.line - 1] + image.column + front_matter_end - 1
            contents = ImageProcessor._replace_image(
                contents, image.content_path, new_path, offset
            )
        return contents

    def replace_final_images(self, contents: str) -> str:
        """
        Replace images in the given HTML contents.

        This replaces images found in the prepare step with their real version.
        """
        background_color = find_background_color(contents)
        for color, image_path in self._images.items():
            print(f"Transforming color block #{color} into image {image_path}")
            contents = self._transform_color(
                contents, color, image_path, background_color
            )
        return contents

    @staticmethod
    def _find_front_matter_end(contents: str) -> int:
        start_index = contents.index("---")
        if start_index != 0:
            return 0
        front_matter_end = contents.find("---", start_index + 3)
        if front_matter_end != -1:
            return front_matter_end + 3
        else:
            return 0

    @staticmethod
    def _build_cumulative_line_lengths(contents: str) -> List[int]:
        sum = 0
        output = []
        for line in contents.split("\n"):
            output.append(sum)
            sum += len(line)
        return output

    @staticmethod
    def _replace_image(contents: str, old_path: str, new_path: str, index: int) -> str:
        index = contents.find(old_path, index)
        if index == -1:
            raise Exception(f"could not find image {old_path}")
        return contents[:index] + new_path + contents[index + len(old_path) :]

    def _build_next_color(self) -> str:
        # color = hex(self._next_color).replace("0x", "")
        color = f"{self._next_color:06x}"
        self._next_color += 1
        return color

    def _generate_image(self, original_path: str, color: str) -> str:
        image_name = f"replacement_{len(self._images)}.png"
        replacement_path = f"{self._output_directory}/{image_name}"
        # TODO handle relative paths
        with Image.open(original_path) as original:
            width, height = original.size
        replacement = Image.new("RGB", (width, height), f"#{color}")
        replacement.save(replacement_path)
        return replacement_path

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
