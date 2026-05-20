# Workflow Instructions

## Syncing Garmin Activities

When the user asks to sync or analyze Garmin data:

1. **Sync** — Call `garmin__sync_garmin_activities(limit=20)` to fetch the latest 20 activities from Garmin with metrics and splits.
2. **Ask about May 13th** — After the sync completes, ask the user two questions specifically for activity **22866136891** (May 13th session):
   - Is this workout **intervals**? (answer: `"true"` or `"false"`)
   - What is the **workout structure**? (free-text description, e.g. `"5 x 3min threshold / 2min rest"`)
3. **Save** — Call `garmin__update_workout_metadata` with `activity_id="22866136891"`, `is_intervals`, and `workout_structure` to store the answers.
4. **Analyze HR Profile** — Call `garmin__analyze_hr_profile(activity_id="22866136891")` to generate an HR plot, send it to Anthropic for analysis, and save the HR profile summary. The result includes the HR profile summary, splits data, and workout structure.

## Periodic Tasks

# Add tasks below (one per line, starting with `- `)

# Format: - [priority|status] Task description

# priority: high, medium (default), low

# status: active (default), paused, completed

#

# Examples:

# - [high] Check my email for important messages

# - Review my calendar for upcoming events

# - [low|paused] Check the weather forecast
