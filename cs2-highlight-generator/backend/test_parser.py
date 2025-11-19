#!/usr/bin/env python3
"""
Quick test script to debug demoparser2 behavior
"""

import sys
from pathlib import Path
from demoparser2 import DemoParser

# Get the most recent demo file
demo_dir = Path("../demo_files")
demo_files = list(demo_dir.glob("*.dem"))

if not demo_files:
    print("No demo files found!")
    sys.exit(1)

# Use the most recent one
demo_file = max(demo_files, key=lambda p: p.stat().st_mtime)
print(f"Testing with: {demo_file}")
print(f"File size: {demo_file.stat().st_size / 1024 / 1024:.2f} MB")
print()

# Parse it
parser = DemoParser(str(demo_file))

# Test 1: Parse player_death with no parameters
print("=" * 60)
print("TEST 1: parse_event('player_death') - NO PARAMETERS")
print("=" * 60)
kills_df = parser.parse_event("player_death")
print(f"Total kills extracted: {len(kills_df)}")
print(f"DataFrame shape: {kills_df.shape}")
print(f"Columns: {len(kills_df.columns)} total")
print()

# Show all column names
print("All column names:")
for i, col in enumerate(kills_df.columns, 1):
    print(f"  {i:3d}. {col}")
print()

# Check for round-related columns
round_cols = [col for col in kills_df.columns if 'round' in col.lower()]
print(f"Round-related columns: {round_cols}")

if round_cols:
    for col in round_cols:
        print(f"  {col}: min={kills_df[col].min()}, max={kills_df[col].max()}")
print()

# Check for name-related columns
name_cols = [col for col in kills_df.columns if 'name' in col.lower()]
print(f"Name-related columns: {name_cols}")
print()

# Show first kill
if len(kills_df) > 0:
    print("First kill event (all fields):")
    print("-" * 60)
    for col in kills_df.columns:
        value = kills_df.iloc[0][col]
        print(f"  {col}: {value}")
    print()

# Show last kill
if len(kills_df) > 1:
    print("Last kill event (all fields):")
    print("-" * 60)
    for col in kills_df.columns:
        value = kills_df.iloc[-1][col]
        print(f"  {col}: {value}")
    print()

print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
