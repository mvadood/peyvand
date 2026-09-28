# Peyvand editable vector master

`peyvand-logo-master.svg` is the production vector conversion of the selected
`../peyvand-logo.png`. It preserves the selected artwork, tight 1086 × 1448
canvas, smaller Persian wordmark, lettering contours, and all dots. It has no
embedded raster image, live text, or font dependency. The source reference has
not been changed.

The background is transparent and the nominal artwork fill is `#15181B`.
The production kit uses `#E9ECEF` as its corresponding light colour. These
solid export colours normalize the subtle colour variation in the raster
reference.

## Editing and animation

- `stroke-left`: the larger upper-left abstract stroke.
- `stroke-right`: the lower-right abstract stroke.
- `wordmark`: the original **پیوند** lettering, including every dot.

Each group is independently editable and animatable. All shapes use native,
closed SVG paths. The counter inside **و** uses an even-odd compound path,
so it stays transparent when the artwork colour changes. The master does not
prescribe timing, easing, sound, or a final animation treatment.

## Geometry validation

`geometry-validation.json` records the comparison between a rendered vector
and the source raster at the same resolution. The outline trace has 10 SVG
paths and 125 cubic or straight segments. At the source resolution:

- Foreground-mask intersection over union: **99.695%**.
- Maximum sampled boundary deviation: **1 pixel**.
- Mean sampled boundary deviation: **0.189 pixel**.

`peyvand-logo-master-validation.png` is a transparent render for inspection,
not an additional selected design. The generated final logo-kit exports live
outside this master directory.

## Reproduce

From the repository root:

```sh
.venv/bin/python scripts/build_logo_master.py
```

The script measures subpixel isocontours halfway between the reference's
foreground and background luminance using marching squares. It fits cubic
Bézier paths to those measurements with a 0.65 source-pixel fitting tolerance,
preserves the symbol's sharp terminals, and uses `rsvg-convert` to render and
validate the result. It reads but never edits the original raster. Required
Python dependencies (`numpy`, `scipy`, `cv2`) and `rsvg-convert` were already
available in the local environment; no dependencies were installed.
