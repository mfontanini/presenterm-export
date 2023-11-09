# presenterm-export

A PDF exporter for [presenterm](https://github.com/mfontanini/presenterm).

---

**This is not meant to be used as a standalone but instead by running _presenterm_ using the `--export-pdf` switch.**

# Installation

This tool requires [tmux](https://github.com/tmux/tmux/) to be installed. The simply run:

```shell
pip install presenterm-export
```

# How it works

This tool's goal is to capture the output of _presenterm_ and turn it into a PDF file. This section outlines roughly how 
it works.

## Presentation metadata

Before _presenterm_ runs this tool, it will gnerate a JSON blob that contains metadata about the presentation, 
including:
* Its path.
* Where each image is in the original markdown file.
* The keys that _presenterm_ wants this tool to simulate to capture its contents. This allows this tool to be pretty 
  dumb in terms of capturing: it doesn't even understand slides, it just presses whatever _presenterm_ tells it to.

This metadata is then passed into this tool via stdin.

## Capturing

Capturing the output of _presenterm_ is done via `tmux` by running it, sending keys to it, and performing pane captures.

The output of this stage is a list of panes that contain ANSI escape codes. This means you can print them on a terminal 
and they'll look good but you can't really turn them into PDF as-is.

## Conversion to HTML

The next step is to take the ANSI text and turn it into HTML via [ansi2html](https://github.com/pycontribs/ansi2html). 
This library creates HTML that looks mostly how we want it to but we perform a few transformations so it looks as close 
to _presenterm_ itself as we can.

## Conversion to PDF

Finally, the HTML is converted into PDF by using [weasyprint](https://github.com/Kozea/WeasyPrint). The result is a PDF 
that looks exactly as if you had ran _presenterm_ including background colors and images.

# Images

Images are tricky and are the reason why this uses HTML as an intermediate step, given they can't be represented with 
just text so `tmux` pane captures will ignore them.

Luckily, [viuer](https://github.com/atanunq/viuer), the crate _presenterm_ uses to display images, falls back to using 
text blocks to display images when your terminal emulator doesn't support any of the image protocols (e.g. kitty's). 
This means if you ran this under `tmux` you would get an ASCII-based version of your images.

This could be enough but we _really_ want PDF exports to look as close to the real thing as possible. So instead of 
keeping those ASCII based images, we do the following:

1. Replace every image with a new image of the same size but made up of a single unique color. This means an image of 
   300x200px will be replaced with another one of 300x200px but made up of some specific color. The reason for doing 
   this is we can then easily spot these blocks of text in the HTML output, which means we can know exactly where the 
   original image should be in the HTML version of the presentation.
2. After the transformation to HTML, we do a pass and find every image based on the color we chose for it and replace it 
   with an `img` tag pointing to its original and using a properly scaled width attribute.
3. When the PDF generation occurs, the image tags are correctly interpreted and the final PDF output contains every 
   image where it should be.

# Presentation size

The size of the page in the generated PDF is the same as the size of the terminal you run `presenterm --export-pdf` on. 
That means you should adjust your terminal size before running it so that it fits text however you want it to.

