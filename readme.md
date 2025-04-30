# Anki Pomodoro Timer & Breathing Exercise Plugin

This is an Anki plugin that combines the Pomodoro Technique with breathing exercises to help you maintain focus and relaxation while studying.

## Features

- 🍅 Pomodoro Timer (default 25 minutes)
- 🌬️ Breathing Exercise (inhale-hold-exhale cycle)
- ⏱️ Real-time countdown in status bar
- 🎯 Long break mechanism (after completing specified number of Pomodoros)
- ⚙️ Fully configurable parameters

## Installation

1. In Anki, click "Tools" > "Add-ons" > "Get Add-ons"
2. Enter code <code>1953077949</code>
3. Restart Anki

## Usage

### Basic Usage

1. The Pomodoro timer starts automatically when you begin reviewing cards
2. Status bar shows remaining time (e.g., "🍅 24:59") and progress
3. Automatically enters break time after Pomodoro completion
4. Breathing exercise starts after break time
5. Returns to deck browser after completing breathing exercise

### Break Mechanism

- Short break after each Pomodoro
- Long break triggers after completing specified number of Pomodoros
- Break time displays in status bar with special indicator
- Configurable maximum break duration to prevent over-resting

### Breathing Exercise Details

Breathing exercise includes the following configurable phases:

- Inhale (default 4 seconds)
- Hold (default disabled)
- Exhale (default 6 seconds)

### Shortcuts

- No specific shortcuts, all operations through interface

### Timer Window

- Optional circular timer window showing remaining time progress
- Window can be set to "Always on Top"
- Supports four position configurations: top-left, top-right, bottom-left, bottom-right
- Real-time display of Pomodoro and break time progress

## Configuration

Access via "Tools" > "Pomodoro & Breathing Settings..."

### General Settings

- Enable/Disable plugin
- Show/Hide status bar timer
- Show/Hide circular timer window
- Timer window position (top-left/top-right/bottom-left/bottom-right)
- Pomodoro duration (1-180 minutes)
- Consecutive Pomodoro count setting (for long break trigger)
- Long break duration setting
- Maximum break duration limit

### Breathing Exercise Settings

- Number of cycles (0-50)
- Enable/Disable each phase
- Duration for each phase (0-60 seconds)

The settings interface displays estimated total training time in real-time.

## Development

### Requirements

- Python 3.9
- aqt >= 25.0

### Internationalization (i18n)

#### Translation File Structure

```
locales/
└── en_US/
   └── LC_MESSAGES/
       ├── messages.mo
       └── messages.po
```

#### Translation Workflow

1. Extract strings for translation:

```bash
cd AnkiPomodoroTimerBreatheExericise
pybabel extract -F babel.cfg -o locales/messages.pot .
```

2. Initialize new language (first time only):

```bash
pybabel init -i locales/messages.pot -d locales -l <language_code>
```

Example: `pybabel init -i locales/messages.pot -d locales -l zh_CN`

3. Update existing translation files:

```bash
pybabel update -i locales/messages.pot -d locales
```

4. Edit translation content in .po files

- Edit `locales/<language_code>/LC_MESSAGES/messages.po`
- Add msgstr translations for each msgid

5. Compile translation files:

```bash
pybabel compile -d locales
```

#### Adding New Strings for Translation

1. Wrap strings with `_()` function in code:

```python
from .translator import _
message = _("Text to translate")
```

2. Repeat workflow steps 1-5 above

#### Supported Languages

- English (en_US)
- Simplified Chinese (zh_CN)

#### Contributing Translations

1. Fork this repository
2. Add new language or improve existing translations following the workflow above
3. Submit Pull Request

### Development Guide

#### Directory Structure

```
AnkiPomodoroTimerBreatheExericise/
├── __init__.py          # Plugin entry
├── babel.cfg            # Babel configuration
├── breathing.py         # Breathing exercise related
├── config.py           # Configuration management
├── constants.py        # Constants definition
├── hooks.py            # Anki hook functions
├── locales/            # Translation files
├── pomodoro.py         # Pomodoro functionality
├── timer_utils.py      # Timer utilities
├── translator.py       # Translator
└── ui/                 # User interface
```

#### Code Style

- Use Python type annotations
- Follow PEP 8 guidelines
- All user-visible strings must be wrapped with `_()` for translation support

### Issue Reporting

If you find any issues or have suggestions for improvement, please submit an Issue on the GitHub repository.
