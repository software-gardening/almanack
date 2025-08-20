# 2025 Poster

The content here is for creating a poster for 2025 conference poster.

## Poster Details

Poster dimensions will be within (but may not exactly match) SBI2 2023's maximum specifications: `91" wide x 44.75” high`.

## Poster development

We use [Quarto](https://github.com/quarto-dev/quarto-cli)'s [Typst](https://github.com/typst/typst) [integration](https://quarto.org/docs/output-formats/typst.html) through a Quarto extension for posters under [`quarto-ext/typst-templates/poster`](https://github.com/quarto-ext/typst-templates/tree/main/poster).
Related [Poe the Poet](https://poethepoet.natn.io/index.html) tasks are defined to run processes defined within `pyproject.toml` under the section `[tool.poe.tasks]`.

See the following examples for more information:

```bash
# preview the poster during development
poetry run poe poster-preview

# build the poster PDF from source
poetry run poe poster-render
```

## References

- Fonts were sourced locally for rendering within Quarto and Typst:
  - [Vollkorn](https://fonts.google.com/specimen/Vollkorn)
  - [Lato](https://fonts.google.com/specimen/Lato)
- QR codes with images were generated and saved manually via [https://github.com/lyqht/mini-qr](https://github.com/lyqht/mini-qr)
- [ImageMagick](http://www.imagemagick.org/) was used to form the bottom logos together as one and render the poster pdf as png using the following commands:

```shell
# append text to qr codes
magick images/sga-qr.png -gravity South -background transparent -splice 0x15 -pointsize 40 -font Arial -weight Bold -annotate 0x15 'Scan for GitHub!' images/sga-qr-text.png

# create a transparent spacer
magick -size 100x460 xc:transparent images/spacer.png

magick images/sga-qr-text.png -resize x460 images/sga-qr-text.png
magick images/bssw-logo-w-background.png -resize x460 images/bssw-logo-w-background.png
magick images/sustainable-horizons-institute-logo.png -resize x460 images/sustainable-horizons-institute-logo.png
magick images/cu-anschutz-short.png -resize x460 images/cu-anschutz-short.png
# combine the images together as one using the spacer for separation
magick -background none images/sga-qr-text.png images/spacer.png images/bssw-logo-w-background.png images/spacer.png images/sustainable-horizons-institute-logo.png images/spacer.png images/cu-anschutz-short.png +append images/header-combined-images.png

# convert the poster pdf to png and jpg with 150 dpi and a white background
magick -antialias -density 300 -background white -flatten poster.pdf poster.png
magick -antialias -density 300 -background white -flatten poster.pdf poster.jpg

# create the title with clip path through svg (typst doesn't support https://github.com/typst/typst/issues/5611)
magick forest_modified.png -resize 5700x400^ -gravity center -extent 5700x400 \
  \( -background none -fill white \
     -font "Vollkorn-Bold" -pointsize 340 \
     label:"The Software Gardening Almanack" \
     -gravity West -extent 5700x400 \) \
  -compose copy_opacity -composite title-text.png
```
