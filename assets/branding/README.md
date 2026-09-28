# Peyvand visual identity

See the [decision log](../../DECISIONS.md) for accepted choices, rejected directions, and proposed next steps.

## Music kit

The user-selected [music kit v1 and Claude handoff](music-v1/README.md) contain five cues
for the main theme, conversation bed, build, high-energy clips and a logo sting.
The kit preserves source MP3s, editing WAVs, prompts and checksums. It does not replace
the existing approved animation soundtrack automatically.

## Selected logo

The user selected and asked to save `peyvand-logo.png` on 2026-09-28.

This is an unchanged copy of `concepts/peyvand-abstract-exchange-v3.png`.

Selected design:

- Two separate, offset abstract calligraphic strokes suggesting an exchange.
- Smaller Persian wordmark: **پیوند**.
- Near-black artwork on a cool light-grey background.
- Tight portrait framing.
- No Iran map, geographic cutout, or literal human profiles.

Preserve this selection as the starting point for future brand work. Earlier and rejected directions remain in `concepts/` for reference.

The selected file is the unchanged raster visual reference generated with the built-in image tool. The generation prompt is in `concepts/peyvand-abstract-exchange-v3-brief.md`.

## Production logo kit

On 2026-09-28, the user authorized creating the logo variations. The production kit is complete and verified: [usage guide](logo-kit/README.md), [visual preview](logo-kit/preview.png), and [ZIP download](peyvand-logo-kit.zip).

The user subsequently approved keeping these variations with “ok store these.” This is the approved production baseline. The [storage record](approved-logo-kit.json) records file checksums for the saved kit, archive, master and selected reference.

The [vector master](master/peyvand-logo-master.svg) is prepared with independent `stroke-left`, `stroke-right`, and `wordmark` groups. It traces the original Persian lettering rather than substituting a font, and its rendered foreground mask overlaps the selected raster by 99.695%.

The kit contains:

- Transparent full-logo, symbol-only, and wordmark-only SVG/PNG exports in dark and light ink.
- Symbol avatars on light and dark backgrounds.
- Separate component SVGs using the same coordinates for animation.
- A preview and ZIP package.

There are 26 SVG/PNG assets and 31 files in the complete ZIP package. Verification covers matching alpha masks across dark/light artwork, all six Persian dots and the transparent letter counter, circular avatar clearance, component geometry matching the master, visual inspection, and ZIP integrity.

The production colours, near-black `#15181B` and cool light grey `#E9ECEF`, are flat values normalized from the selected artwork. They implement its existing treatment; they do not record approval of a new palette. The selected raster remains unchanged.

## Opening animation

The user authorized the next animation step with “ok do it.” [Version 1](animation/README.md) now provides a 2.8-second staggered two-stroke exchange and Persian wordmark reveal, in landscape and vertical formats, each with light/dark and sound-on/silent copies. The short sonic signature is also saved separately as WAV, with four generated alternatives retained.

Open the [playback preview](animation/preview.html) or download the [complete animation ZIP](peyvand-animation-v1.zip). The user approved saving the delivered motion and sound with “cool save it.” Version 1 is the approved motion baseline; the [storage record](approved-animation-v1.json) identifies the saved files. The approved logo kit and all recorded baseline checksums are unchanged.

## Approved speaker backgrounds

The matching reading-room backgrounds for [Milad](backgrounds/milad-reading-room-v1.png) and [Hooman](backgrounds/hooman-reading-room-v1.png) were approved for storage on 2026-09-28. [Complete package](backgrounds/peyvand-speaker-backgrounds-v1.zip), [manifest](backgrounds/speaker-background-manifest.json), and [Claude handoff](backgrounds/CLAUDE-HANDOFF.md). Placement and renderer integration are left to Claude.
