# Anki Pomodoro Timer & Breathing Exercise Plugin

This is an Anki plugin that combines the Pomodoro technique with breathing exercises to help you stay focused and relaxed while studying.

## Features

- 🍅 Pomodoro timer (default 25 minutes)
- 🌬️ Breathing exercise (inhale-hold-exhale cycle)
- ⏱️ Real-time status bar display
- 🎯 Long break mechanism (after completing specified Pomodoro sessions)
- ⚙️ Fully configurable settings

## Installation

1. In Anki, click "Tools" > "Add-ons" > "Get Add-ons"
2. Enter code `1953077949`
3. Restart Anki

## Usage

### Basic Usage

1. The timer starts automatically when reviewing cards
2. Status bar shows remaining time (e.g. "🍅 24:59") and progress
3. Automatically enters break time after Pomodoro
4. Starts breathing exercise after break
5. Returns to deck browser after breathing exercise

### Break Mechanism

- Short break after each Pomodoro
- Long break after completing specified Pomodoro sessions
- Break time shown in status bar with special icon
- Configurable maximum break duration

### Breathing Exercise

Configurable stages:
- Inhale (default 4 seconds)
- Hold (disabled by default)
- Exhale (default 6 seconds)

### Timer Window

- Optional circular timer window
- Can be set to "always on top"
- Four position options
- Shows Pomodoro and break progress

## Configuration

Access via "Tools" > "Pomodoro & Breathing Settings..."

### General Settings
- Enable/disable plugin
- Show/hide status bar timer
- Show/hide circular timer window
- Timer window position
- Pomodoro duration (1-180 minutes)
- Consecutive Pomodoro count for long break
- Long break duration
- Maximum break time limit

### Breathing Exercise Settings
- Cycle count (0-50)
- Enable/disable stages
- Stage duration (0-60 seconds)

## Development

### Requirements
- Python 3.9
- aqt >= 25.0

### Project Structure
```
AnkiPomodoroTimerBreatheExericise/
├── __init__.py         # Plugin entry
├── breathing.py        # Breathing exercise core
├── config.py           # Configuration
├── constants.py        # Constants
├── hooks.py            # Anki hooks
├── pomodoro.py         # Pomodoro core
├── timer_utils.py      # Timer utilities
└── ui/                 # UI components
    ├── __init__.py
    ├── circular_timer.py
    ├── config_dialog.py
    └── statusbar.py
```