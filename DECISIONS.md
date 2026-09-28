# Decision log

Record project and creative decisions here so future work follows the user's choices. Separate accepted decisions from proposals. When a choice changes, add a dated entry that supersedes the earlier decision; preserve the history.

## Current direction

- Peyvand is a Persian conversational podcast covering Iran, abstract ideas, technology, politics and books, with long-form YouTube episodes and vertical clips for Instagram Reels and YouTube Shorts. The broader subject scope was clarified during the music discussion.
- The user requested the five generated music use-case variations be retained for Claude; see the [music kit v1 handoff](assets/branding/music-v1/README.md). Renderer integration and replacement of the existing animation soundtrack have not been performed.
- The identity should feel serious and energetic, with creative abstraction and room for animation.
- The selected logo is [assets/branding/peyvand-logo.png](assets/branding/peyvand-logo.png): two offset abstract strokes, a smaller **پیوند** wordmark, near-black on cool light grey, and tight framing.
- The selected file remains the unchanged raster visual reference. The production logo kit is complete, verified, and approved for storage; see its [usage guide](assets/branding/logo-kit/README.md), [preview](assets/branding/logo-kit/preview.png), and [ZIP package](assets/branding/peyvand-logo-kit.zip). The [opening animation and sonic signature](assets/branding/animation/README.md) are approved and saved as version 1 under D-016.

## Accepted decisions — 2026-09-28

| ID | Decision | Reason / user direction | Scope or reference |
|---|---|---|---|
| D-001 | Build a consistent identity across long-form YouTube episodes, Instagram Reels, and YouTube Shorts. | The project produces episodes for a conversational podcast; the theme should remain consistent. | Series-wide direction. |
| D-002 | Develop the identity one asset at a time, starting with the logo. | The user requested a step-by-step process. | Other brand assets remain future work. |
| D-003 | Use the Persian name **پیوند** in the logo. | The user explicitly requested a Persian logo. | No English wordmark is selected. |
| D-004 | Use two abstract, offset calligraphic strokes suggesting an exchange. | The user liked the two-party conversation idea, then asked for more creativity and abstraction. The literal profiles felt like two men and were rejected. | Selected symbol: [v3](assets/branding/concepts/peyvand-abstract-exchange-v3.png). |
| D-005 | Keep the tone serious while retaining visual energy. | Multiple bright colours felt inconsistent with a serious tone; the literal, soft composition felt sleepy. | Shape and composition should carry the energy. |
| D-006 | Use the near-black and cool light-grey treatment shown in the selected logo. | The user preferred this treatment after rejecting the earlier colour directions, then approved saving the resulting design. | Logo palette only; the existing episode renderer and its backgrounds have not been recoloured. |
| D-007 | Make the Persian wordmark smaller than the symbol. | The user asked for smaller text and preferred the revision. | Preserve the relative scale in the selected image. |
| D-008 | Use tighter framing around the complete logo. | The user said the previous presentation had too much margin. | Preserve the selected crop as the visual reference; placement-specific safe space is not yet defined. |
| D-009 | Return to the logo without an Iran detail. | After exploring a subtle Iran reference, the user explicitly requested the previous version without it. | Supersedes the Iran experiments; [v4](assets/branding/concepts/peyvand-abstract-exchange-v4-iran.png) is rejected. |
| D-010 | Save the tight, smaller-wordmark version as the selected logo. | The user said “ok save this” after returning to the version without Iran. | Canonical file: [peyvand-logo.png](assets/branding/peyvand-logo.png), an unchanged copy of concept v3. |
| D-011 | Preserve room for motion graphics and animation. | The user explicitly wanted animation potential. | The two strokes should remain independently animatable when a vector master is prepared. No motion treatment is approved yet. |
| D-012 | Maintain a decision log. | The user requested this log. | Update this file as meaningful decisions are made. |
| D-013 | Prepare the production logo variations from the selected design. | The user said “ok create the logo variations et” after the proposed logo kit. | Authorizes the vector master, transparent light/dark artwork, symbol-only variants and animation-ready components. Production exports are complete and verified; this does not approve new colours or an animation treatment. |
| D-014 | Keep the delivered logo kit as the approved production baseline. | After reviewing the variations, the user said “ok store these.” | Retain the SVG/PNG variants, avatars, master and motion components as delivered. [Storage record](assets/branding/approved-logo-kit.json) identifies the saved files and their checksums. Animation design remains a proposed next step. |
| D-015 | Create the proposed 2–3-second opening animation and short sonic signature. | The user said “ok do it” after the proposed staggered two-stroke exchange, wordmark reveal, landscape/vertical exports and sonic signature. | Authorizes creation. Version 1 is saved in [animation/](assets/branding/animation/README.md), with light/dark versions, sound-on and silent MP4s, a separate WAV and retained audio alternatives. This does not yet mark the delivered motion or sound as creatively approved. |

| D-016 | Approve and save opening animation version 1 and its sonic signature. | After viewing the delivered animation, the user said “cool save it.” | Keep all eight landscape/vertical, light/dark, sound-on/silent exports and the finished WAV as the motion baseline. The used sound is take 3; other takes remain alternatives. [Storage record](assets/branding/approved-animation-v1.json) records the files and archive checksums. Supersedes the pending-review status in D-015. |

## Production implementation — 2026-09-28

These are implementation choices within D-013, rather than new creative decisions approved by the user.

- The [vector master](assets/branding/master/peyvand-logo-master.svg) traces the selected artwork and retains three independent groups: `stroke-left`, `stroke-right`, and `wordmark`. Its rendered foreground mask overlaps the raster reference by 99.695%.
- Flat production colours are normalized from the selected artwork to near-black `#15181B` and cool light grey `#E9ECEF`. This specifies the existing treatment for reproducible exports; it is not a newly approved palette or a change to episode backgrounds.
- The completed [production kit](assets/branding/logo-kit/README.md) contains 26 SVG/PNG assets: full-logo, symbol-only, and wordmark-only transparent exports in dark and light ink; symbol avatars on light and dark backgrounds; and component SVGs sharing the master coordinates for animation. The [preview](assets/branding/logo-kit/preview.png) shows the variants, and the [ZIP package](assets/branding/peyvand-logo-kit.zip) contains 31 files including documentation and validation data.
- Verification confirmed matching alpha masks across dark/light pairs, all six Persian dots and the transparent letter counter, safe circular avatar crops, and component paths identical to the master. The preview was visually inspected and ZIP integrity passed.
- The selected raster remains unchanged. Component separation prepares the logo for motion; timing, movement, sound, and reveal design remain undecided.

## Motion implementation — 2026-09-28

Version 1 under D-015 uses the exact approved SVG paths. The strokes enter at 0.08s and 0.36s, settle by 1.06s, then the Persian wordmark reveals from 1.12–1.58s. The final composition holds until 2.8s. Exported at 30 fps for landscape 1920×1080 and vertical 1080×1920, each in light/dark and sound-on/silent versions.

The proposed audio cue was generated using ElevenLabs Sound Effects v2. Four successful takes are retained; take 3 was chosen for the first edit based on measured attack timing close to the stroke entrances. A 48 kHz stereo WAV supplies the AAC video mix. The delivered sound and motion were subsequently approved under D-016. [Generation notes](assets/branding/animation/audio/generation-notes.json) record the prompt, source IDs and processing.

All eight exports passed decoding, duration, frame-count, dimensions and audio-stream checks. Final vector paths match the master; the 34 files in the approved logo storage record retain their checksums. [Source renderer](scripts/render_logo_animation.py), [preview](assets/branding/animation/preview.html), [validation](assets/branding/animation/validation.json), and [complete ZIP](assets/branding/peyvand-animation-v1.zip) are saved. Episode renderers have not yet been integrated with this treatment.


## Episode layout exploration — 2026-09-28

The user authorized a quick first mockup and explicitly prioritized fast iteration. Two landscape stills are saved in [layout-v1](assets/branding/layout-v1/README.md): a two-speaker frame using the existing recordings, and a three-column extension with a labelled guest placeholder. These explore the proposed pale-grey editorial layout, Persian headings, captions, names and approved logo. They are drafts for review, not approved identity assets. No episode renderer changes or motion sample were made at this stage.


## Layout feedback and revision — 2026-09-28

The user rejected layout v1 as too plain, criticized its fonts, and said it looked like a Zoom call. Avoid equal video-call tiles and generic name boxes. Version 2 is a quick draft in [layout-v2/conversation-focus.png](assets/branding/layout-v2/conversation-focus.png): dominant active speaker, smaller unboxed reaction, dark backdrop with an oversized approved logo stroke, and properly shaped Vazirmatn Persian typography. The editorial topic title is a proposed heading, not a spoken quote. This revised composition and font choice remain unapproved. The existing matte edges need refinement only if this direction is selected.


## Background-only direction — 2026-09-28

The user redirected this work to reusable assets, leaving speaker sizing and placement to Claude. They questioned a plain backdrop and requested an example of the proposed natural reading-room setting. [Reading room v1](assets/branding/backgrounds/reading-room-v1.png) is a generated background-only concept with plaster, walnut shelving, books, plants and side light; [prompt](assets/branding/backgrounds/reading-room-v1-brief.md). It is pending review. Additional room angles have not been generated, and the episode renderer is unchanged.

## Music decisions — 2026-09-28

Music-specific IDs keep this side-conversation record separate from the visual-asset numbering.

| ID | Decision / status | User direction | Scope |
|---|---|---|---|
| M-001 | Use AI-generated music for the current exploration. | The user asked to generate and audition music. | ElevenLabs Music v2; provenance recorded per track. |
| M-002 | Keep a serious but engaging contemporary sound with audible Iranian character. | Initial takes were too techy; acoustic revisions were too acoustic; the user then requested more Iranian character. | Persian melody and tombak with rounded tar, warm electronic bass and restrained modern drums. No requirement for literal national symbols in the visual logo is implied. |
| M-003 | Develop melody and harmony instead of relying on a repeating motif. | The first Iranian hybrid was good but too monotone/repetitive; the developed revision was better. | Question, response, departure, breathing space and transformed return; excitement needs musical development as well as denser drums. |
| M-004 | Reduce the ney prominence. | “the ney sound is a bit extreme” | Latest cues were prompted with faint low background ney only, no piercing flute lead; the sting excludes it. Actual sonic details remain subject to listening review. |
| M-005 | Keep versions for different energy levels and uses. | The user asked for variations that can increase excitement, then requested different cases. | Main theme, conversation bed, build/reveal, high energy and short logo sting. |
| M-006 | Store the delivered five-take kit and document it for Claude. | “ok store these so claude can pick them up. document them etc” | [Music v1](assets/branding/music-v1/README.md), original MP3s, editing WAVs and manifest. Approval to retain this working kit; no final edit, mastering, renderer integration or automatic replacement of D-016's animation sound. |

The high-energy take was requested at 30 seconds but returned about 51.6 seconds; preserve it intact and consult measured durations in the manifest. These cues were generated independently from a shared brief, not from a common audio reference; identical melodies/keys and seamless looping are not verified. Previous experimental rounds remain in the linked ElevenLabs flow; only the latest five requested takes are archived in this kit.


## Two-speaker background assets — 2026-09-28

After the reading-room example, the user said “ok not bad. create one for me and hooman to begin with and let's leave the rest for claude”. This selects the reading-room direction for the first pair and delegates sizing, placement and integration to Claude. Generated [Milad’s window-side view](assets/branding/backgrounds/milad-reading-room-v1.png) and [Hooman’s shelf/alcove view](assets/branding/backgrounds/hooman-reading-room-v1.png), using the same reference. Both are clean background assets; final individual plate approval is not yet recorded. [Handoff](assets/branding/backgrounds/CLAUDE-HANDOFF.md) and [manifest](assets/branding/backgrounds/speaker-background-manifest.json) are saved. No existing backgrounds or renderer code were changed.


## Speaker background approval — 2026-09-28

The user approved storing both delivered speaker backgrounds with “ok store these.” Milad’s window-side plate and Hooman’s shelf/alcove plate are now the approved background baseline. This supersedes their pending-review status above. [Manifest](assets/branding/backgrounds/speaker-background-manifest.json), [handoff](assets/branding/backgrounds/CLAUDE-HANDOFF.md) and [ZIP package](assets/branding/backgrounds/peyvand-speaker-backgrounds-v1.zip) are updated; image bytes are unchanged. Claude retains responsibility for sizing, placement and renderer integration.

## Shorts direction — 2026-09-28

Decisions the user gave in chat while reviewing the first Shorts and the POC.

| ID | Decision | User direction | Scope |
|---|---|---|---|
| D-017 | Spell the guest's on-screen name **هومان**, never «هومن». | "it's also هومان not هومن" | All captions, name labels and graphics. Source files corrected; POC re-rendered. |
| D-018 | Shorts open with the hook, not the logo animation; the logo animation and its sonic signature close the clip, with a small logo watermark throughout. | "agree with 1" | Shorts/Reels. Long-form order (cold open → ident → episode) remains a proposal. |
| D-019 | Dark navy is an acceptable accent alongside the logo's near-black and cool grey. | "i feel dark navy is fine. we don't want everything to be too boring/ the same" | Video graphics and cards; the logo palette itself is unchanged. |
| D-020 | Show the speakers less; carry stories with imagery (generated or sourced). | "use more images/ creatives … the less we see the speakers the better" | Shorts first; long-form to follow. |
| D-021 | Test a dominant-speaker layout with a small listener/narrator bubble instead of equal tiles. | "ok on 5" | Test only; not yet approved as the house layout. |
| D-022 | Use the music kit v1 cues in edits, for as long as each scene needs. | "ok on music" / "can we use the music files now" | Parking short v2: conversation bed → build/reveal → main theme → approved sonic signature. |
| D-023 | Avoid frequent zoom toggles; motion should be slow push-ins and soft dissolves. | The first Shorts "feel like the video flashes many times". | All renderers. |

Delivered for review (not yet approved): parking short v2 (`renders/shorts/parking_v2.mp4`, plus cover and thumbnail JPGs; renders are not in git), built by `short2.py`. Its B-roll is a new generated illustration set — see the [B-roll manifest](assets/episodes/01/broll/manifest.json) for style, generation IDs and cost. The reading-room plates are used for the ~20 s of on-camera speaker time with edge decontamination, light wrap, colour matching and depth-of-field blur; their suitability is still under test. The end-card link is a placeholder.

## Rejected or superseded directions

| Direction | Outcome |
|---|---|
| Navy/amber logo treatment | Rejected during the first conversation-symbol exploration. |
| Coral/turquoise with plum | Proposed, then rejected as too bright for the desired serious tone; not generated. |
| Warm charcoal/parchment | Explored, then superseded after the user continued to dislike the colour treatment. |
| Literal facing human profiles | Rejected as sleepy and too specifically suggestive of two men. |
| Large wordmark and generous surrounding margins | Superseded by smaller lettering and a tighter crop. |
| Iran-shaped negative space / small Iran cutout | Explored, then rejected; return to the clean abstract symbol. |

Earlier images and their generation prompts are retained in [assets/branding/concepts/](assets/branding/concepts/) as history. They are not the selected logo.

## Proposed next steps — not yet approved or implemented

1. Develop the remaining identity assets one at a time, such as video layouts, captions, and thumbnails. Their order and designs remain undecided.

## Adding a decision

Record the date, decision, status, reason, affected files, and any earlier decision it supersedes. A suggestion stays proposed until the user chooses it or clearly authorizes it. Keep the current-direction section aligned with the accepted decisions.
