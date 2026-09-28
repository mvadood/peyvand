# Peyvand music kit v1 — Claude handoff

Saved at the user's request on 2026-09-28. Start here when selecting music for episodes, Reels, Shorts, trailers or transitions. The user accepted the latest direction and requested these five takes be stored and documented for Claude.

## Files and intended uses

| Cue | Editing file | Approx. duration | Intended use |
|---|---|---:|---|
| Main theme | [peyvand-main-theme-v1.wav](wav/peyvand-main-theme-v1.wav) | 30 s | Opening/closing passages; choose a short phrase for an intro and let speech begin promptly. |
| Conversation bed | [peyvand-conversation-bed-v1.wav](wav/peyvand-conversation-bed-v1.wav) | 60 s | Quiet support beneath selected narration or transitions; music need not run beneath an entire conversation. |
| Build and reveal | [peyvand-build-and-reveal-v1.wav](wav/peyvand-build-and-reveal-v1.wav) | 25 s | Anticipation before a key question or reveal. Align the musical arrival by listening. |
| High energy | [peyvand-high-energy-v1.wav](wav/peyvand-high-energy-v1.wav) | 51.6 s reported | Trailers, announcements and energetic social clips. Requested 30 s, but the provider returned a longer take; retain the full source and edit as needed. |
| Logo sting | [peyvand-logo-sting-v1.wav](wav/peyvand-logo-sting-v1.wav) | 4 s | A short musical logo or section break. This is an alternative, not an automatic replacement for the already approved animation sound. |

The matching original MP3s are in [source/](source/). The [manifest](manifest.json) contains full generation prompts, source IDs, requested/reported/measured durations, stream metadata, byte sizes and SHA-256 checksums. Use its verified durations for editing rather than assuming the request was followed exactly.

WAVs are stereo 48 kHz, 24-bit PCM editing derivatives decoded from the generated MP3s. This conversion does not restore information lost to MP3 compression. Sources have not been trimmed, equalized, normalized or remastered.

## Creative direction to preserve

The podcast is Persian-language and covers Iran, abstract ideas, technology, politics and other conversational subjects, including books. Its music should be serious, curious and contemporary, with energy when needed.

- Iranian identity should be audible through melody, phrasing and tombak rhythm, while contemporary bass and drums supply weight and motion.
- The selected direction uses a rounded, softened tar lead, tombak, deep warm electronic bass and restrained harmonic texture.
- The user found the ney too extreme. These generations were directed to keep it faint, low and behind the tar, with no piercing or sustained flute lead. The sting explicitly excludes ney/flute. This is the requested mix direction, not an auditory verification of every generated instrument.
- Develop ideas: question, answering melody, harmonic departure, a moment of space and a transformed return. Avoid a static four-note loop with progressively louder drums.
- Create excitement through melodic development, changing bass harmony, rhythmic density and contrast. Keep speech intelligible.
- Avoid tech-ad synth plucks and rigid sequencers; also avoid an overly acoustic ensemble, exposed guitar picking, sentimental piano, ornate traditional pastiche, dramatic news menace and festival-style EDM drops.

## Decisions and iteration history

1. Initial electronic sketches were promising but too techy.
2. Acoustic piano/guitar/bass revisions overcorrected; the user disliked the audible guitar-string character.
3. The user clarified the broader subject matter and requested more Iranian character.
4. A tar/tombak/electronic hybrid was liked but found monotonous/repetitive.
5. A version with melodic and harmonic development was judged better.
6. The user requested use-case variations and a less extreme ney, then asked to store these five takes for Claude.

These are five independent generations following a shared sonic brief, not stems or remixes of one verified master. Identical melody, key, exact 100 BPM timing, seamless looping and precise section timestamps have not been verified. Do not claim those properties merely because they appear in the prompts. The five tracks are retained as the requested working kit; final mix levels, exact edits and renderer integration remain future implementation work.

## Integration notes for Claude

- Start with the WAV appropriate to the scene. Listen to the actual cue to choose edit points, fades and gain; the conversation bed is not certified as a seamless loop.
- Preserve the original MP3s and these WAVs. Put trims, loops, normalized versions or mastered mixes in a separate derived-output location with processing notes.
- `assets/music.wav` and `music.py` still contain the prior synthesized placeholder; they were not replaced. Inspect renderer music paths before integrating these cues.
- Existing logo animation v1 is 2.8 seconds and has its own approved sound under D-016. The new four-second sting needs a deliberate sync/edit decision before it is used there.
- Keep foreground dialogue dominant. Use background music selectively and duck it under speech; make final loudness decisions in the episode mix rather than normalizing every source to the episode target.
- The source prompts are reproducibility notes, not instructions to regenerate. The saved files are the takes the user asked to retain.

## Provenance and usage rights

Generated through ElevenLabs Music v2 in [Peyvand — Music sketches](https://elevenlabs.io/app/flows/ixm4k3AeZGLb0CXbXTLd). Source and session IDs are in the manifest. No signed download URLs are retained in project documentation.

The account's plan eligibility was not inspected, so this kit is not a license certificate or a guarantee of exclusive copyright. The earlier licensing discussion used the [music model-specific terms](https://elevenlabs.io/eleven-music-model-specific-terms) and [music service terms](https://elevenlabs.io/music-terms); retain the applicable account entitlement with production records.

## Validation

The archive process checks file metadata and decodes every editing WAV fully. Checksums and exact measurements are in `manifest.json`. This is technical validation, not a claim that the assistant listened to or musically verified each generated result.
