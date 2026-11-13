# 07 — Common System Completed

The common/shared foundation is now built as far as possible before local testing.

## Common Features Done

- global config loader
- per-channel config loader
- SQLite database schema
- channel registration/bootstrap
- folder manager
- channel-owned workspace/output/upload package structure
- script generator interface
- metadata generator
- voice generator with local TTS attempt and fallback
- caption generator
- thumbnail generator
- renderer interface
- safety checker
- review manager
- posting tracker
- status manager
- output index generator
- setup health checker
- backup/handover zip generator
- system test script
- one main Flask dashboard
- dashboard per-channel sections
- dashboard setup status page
- dashboard backup button
- dashboard approve/needs-edit/archive/reject/post buttons

## What Per-Channel Agents Can Do Later

Each channel can be improved independently by editing only:

```text
channels/<channel_id>/prompts/prompts.yaml
config/channels/<channel_id>.yaml
channel-specific template assets
```

Shared code should only be changed when improving all channels.

## Do Not Break Rule

Changing one channel must not break another.
Keep channel-specific content out of shared core unless it is a reusable generic feature.
