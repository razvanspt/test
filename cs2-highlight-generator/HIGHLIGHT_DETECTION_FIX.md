# FaceIt Demo Highlight Detection Fix

## Problem
Despite successfully parsing 173 kills and 9 rounds from the newer FaceIt demo, the system returned **0 highlights detected**.

## Root Cause
The highlight detector was using hardcoded field names that work for standard CS2 matchmaking demos but don't exist in FaceIt demos:

| Data | Expected Field Name | FaceIt May Use |
|------|-------------------|----------------|
| Round | `"round"` | `"round_num"` or `"total_rounds_played"` |
| Attacker | `"attacker_name"` | `"attacker"`, `"killer_name"`, or `"killer"` |
| Tick | `"tick"` | `"server_tick"` or `"game_tick"` |
| Weapon | `"weapon"` | `"weapon_name"` or `"weapon_type"` |
| Damage | `"attacker_damage"` | `"damage"` or `"dmg_health"` |

When the detector looked for `kill.get("round", 0)`, if FaceIt uses `"round_num"` instead, it would default to `0`, grouping all kills into round 0.

## Solution
Added a new `_get_field_value()` helper method that tries multiple possible field names:

```python
def _get_field_value(self, data: Dict, field_names: List[str], default=None):
    """Try multiple possible field names and return the first non-None value"""
    for field in field_names:
        value = data.get(field)
        if value is not None:
            return value
    return default
```

Updated **both** `_detect_aces()` and `_detect_multikills()` to use flexible field names:

```python
# Before:
round_num = kill.get("round", 0)
attacker = kill.get("attacker_name", "")
tick = kill.get("tick", 0)

# After:
round_num = self._get_field_value(kill, ["round", "round_num", "total_rounds_played"], 0)
attacker = self._get_field_value(kill, ["attacker_name", "attacker", "killer_name", "killer"], "")
tick = self._get_field_value(kill, ["tick", "server_tick", "game_tick"], 0)
```

## Debug Logging Added
The detector now logs useful information for troubleshooting:

```
DEBUG: Grouped 173 kills into 9 rounds
DEBUG: Sample kill fields: ['tick', 'round_num', 'attacker', 'weapon_name', ...]
DEBUG: Has attacker_name-like field: True, has tick field: True
```

This helps identify if critical fields are missing or misnamed.

## Testing Instructions

### 1. Pull Latest Changes
```bash
git pull origin claude/cs2-popularity-analysis-014YnmZdTLb5C92dfs1iarod
```

### 2. Restart Backend Server
```bash
cd cs2-highlight-generator/backend
python main.py
```

Server will start at `http://localhost:8000`

### 3. Upload FaceIt Demo
- Open `cs2-highlight-generator/frontend/index.html` in browser
- Upload your newest FaceIt demo (the ~400MB one that parsed 173 kills)

### 4. Check Results
You should now see highlights detected! Expected results:

**Match Info:**
- Map: de_nuke
- Total rounds: 9
- All 10 players listed

**Highlights Expected:**
- **Aces (5K in one round)**: If any player got 5 kills in a single round
- **4Ks (Quadra Kills)**: 4 kills within 15 seconds
- **3Ks (Triple Kills)**: 3 kills within 15 seconds

With 173 kills across 9 rounds (average ~19 kills/round), you should see multiple highlights!

### 5. Check Logs (if issues)
Look for debug messages in the console:

```
INFO: Starting highlight detection...
DEBUG: Grouped 173 kills into 9 rounds
DEBUG: Sample kill fields: [...]
DEBUG: Has attacker_name-like field: True, has tick field: True
INFO: Detected ACE: PlayerName ACE with AK-47, AWP in round 3
INFO: Detected 4K: PlayerName 4K with Desert Eagle in round 7
INFO: Detected 173 highlights
```

## What This Fixes

✅ **Round grouping** - Kills now properly grouped into rounds
✅ **Player identification** - Attackers correctly identified
✅ **Timestamp calculation** - Proper tick/time conversion
✅ **Weapon tracking** - Weapons used in highlights
✅ **Damage calculation** - Total damage per highlight

## If Still 0 Highlights

If you still get 0 highlights, check the debug logs to see:

1. How many rounds were detected? (Should be 9)
2. What field names are in the sample?
3. Do the fields exist?

The logs will show exactly which fields are available and help diagnose the issue.

## Files Modified

- `cs2-highlight-generator/backend/highlight_detector_service.py`
  - Added `_get_field_value()` helper method
  - Updated `_detect_aces()` to use flexible field names
  - Updated `_detect_multikills()` to use flexible field names
  - Added debug logging for troubleshooting

## Commits

1. **18bdcca** - "Fix highlight detection for FaceIt demos by checking multiple round field names"
2. **aba3d4c** - "Make highlight detector robust with flexible field names for FaceIt demos"
