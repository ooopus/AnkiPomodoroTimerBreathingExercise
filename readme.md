[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ooopus/AnkiPomodoroTimerBreathingExercise)

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

## Development

### Requirements

- Python 3.9
- aqt >= 25.0

### Internationalization (i18n)

The plugin automatically uses your system language for translations. If a translation for your system language isn't available, it will fall back to English.

#### Translation File Structure

```
locales/
└── en_US/
   └── LC_MESSAGES/
       ├── messages.mo
       └── messages.po
```

#### Translation Workflow

This section describes the process for managing translations. All commands should be run from the project root directory (`AnkiPomodoroTimerBreatheExercise`).

```bash
git clone https://github.com/ooopus/AnkiPomodoroTimerBreathingExercise
```

##### Prerequisites: Install Babel

Ensure you have the Babel package installed. Run:

```bash
pip install babel
pybabel --version  # Verify installation
```

##### Step 1: Extract Strings

Extract all translatable strings from the source code into a template file (`messages.pot`). This command scans the project for strings wrapped in `_()` and collects them.

```bash
cd src
pybabel extract -F babel.cfg -o locales/messages.pot .
```

##### Step 2: Initialize New Language

Create a new translation file for a language that hasn't been added before. Replace `<language_code>` with the appropriate locale (e.g., `de_DE` for German, `fr_FR` for French).

```bash
pybabel init -i locales/messages.pot -d locales -l <language_code>
```

Example for Simplified Chinese:

```bash
pybabel init -i locales/messages.pot -d locales -l zh_CN
```

##### Step 3: Update Existing Translations

When new strings are added or existing ones are modified, update all translation files to include these changes. This command updates the PO files for all languages.

```bash
pybabel update -i locales/messages.pot -d locales
```

##### Step 4: Edit Translation Files

Translate the extracted strings by editing the PO file for your target language. Each `msgid` represents the original string, and you should provide the translation in the `msgstr` field.

- Open `locales/<language_code>/LC_MESSAGES/messages.po` in a text editor or PO editor
- For each entry, add your translation between the quotes in the `msgstr` line

Example:

```
msgid "开始"
msgstr "Start"
```

##### Step 5: Compile Translations

Compile the PO files into MO files, which are binary formats used by the application at runtime.

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

- 简体中文 (zh_CN)
- English (en_US)
- Deutsch (de_DE)

#### Contributing Translations

1. Fork this repository
2. Add new language or improve existing translations following the workflow above
3. Submit Pull Request

### Development Guide

#### Code Style

- Use Python type annotations
- Follow PEP 8 guidelines
- All user-visible strings must be wrapped with `_()` for translation support

### Issue Reporting

If you find any issues or have suggestions for improvement, please submit an Issue on the GitHub repository.
