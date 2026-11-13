# 00 — Goals And Requirements

## Main Goal

Build a new semi-automated faceless content system called:

```text
8_Channel_Content_Factory
```

The user already has a separate working system called:

```text
WC Klips
```

WC Klips must stay separate and protected.

## Final Overall Plan

There are 9 total channels/projects in the full plan:

1. Fictional Reddit-Style Stories
2. English Learning
3. Psychology / Human Behavior
4. Dark History / Mystery
5. AI Tools + Automation
6. Quiz / Brain Challenge
7. Faceless Facts / Did You Know
8. Sports Type 3 + Safer Highlight Review
9. WC Klips — already working separately

This new system handles only the first 8 channels.

## Most Important Architecture Rule

The new system must have:

```text
one shared core system
+ eight separate protected channel modules
```

Changing one channel must not break another.

Examples:

- Changing English Learning captions must not affect Reddit Stories.
- Changing Quiz design must not affect Psychology.
- Changing Sports templates must not affect AI Tools.

## Semi-Automated Requirement

The user wants to do the least possible work.

Target:

```text
System: 80% to 90% of work
User: 10% to 20% of work
```

User should mostly:

- choose channel
- approve topic
- approve/review script
- review final video
- manually upload
- mark posted

System should handle:

- topic ideas
- script generation
- AI voice
- captions
- video rendering
- thumbnails
- metadata
- folder organization
- dashboard
- posting tracker

## Dashboard Requirement

The dashboard should be organized like WC Klips:

- channel filter
- video list
- video preview
- status badges
- review queue
- posting status
- metadata copy buttons
- clean folders

## Manual Upload Rule

At first, no auto-upload.

The system prepares files and metadata. The user manually uploads and marks posted.

## Build Priority

Start with MVP channels:

1. Reddit Stories
2. Quiz
3. English Learning

Then later add:

4. Psychology
5. Facts
6. Dark History
7. Sports Reviews
8. AI Tools + Automation
