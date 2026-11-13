# User Guide - Calendar Desktop Notifications

## Table of Contents
1. [Installation](#installation)
2. [Initial Setup](#initial-setup)
3. [Using the Application](#using-the-application)
4. [Configuration Options](#configuration-options)
5. [Troubleshooting](#troubleshooting)

## Installation

### Pre-built Executables (Recommended)

Download the appropriate version for your operating system from the [releases page](https://github.com/PretorianX/calendar-notifications/releases):

- **Windows**: `CalendarDesktopNotifications-<version>-setup.exe`
- **macOS**: `CalendarDesktopNotifications-<version>-unsigned.pkg`
- **Linux**: no pre-built package. Install from source.

#### Windows installer

1. Run `CalendarDesktopNotifications-<version>-setup.exe`. It installs for your user and needs no admin rights.
2. Keep "Start automatically when I sign in to Windows" selected if you want the app at every sign-in.
3. At the end, the installer starts the app. The calendar icon appears in the system tray.

NOTE: Windows 11 puts new tray icons in the hidden overflow area (the `^` arrow).
To keep the icon visible, open **Settings > Personalization > Taskbar > Other system tray icons** and turn on "Calendar Desktop Notifications".

The installer is not code-signed. If Windows SmartScreen shows a warning, select **More info > Run anyway**.
To remove the app, use **Settings > Apps > Installed apps**.

### From Source

1. Ensure Python 3.11 or later is installed
2. Clone the repository
3. Run the setup script:
   ```bash
   ./setup.sh
   ```

## Initial Setup

### 1. Launch the Application

- **Windows**: Open "Calendar Desktop Notifications" from the Start menu
- **macOS**: Open the app from `/Applications`
- **Linux**: Run `pipenv run start` in the project folder

The application will start in your system tray.

### 2. Configure CalDAV Connection

1. Right-click the system tray icon
2. Select "Settings"
3. Enter your CalDAV server details:
   - **URL**: Your CalDAV server URL (e.g., `https://caldav.example.com/`)
   - **Username**: Your CalDAV username
   - **Password**: Your CalDAV password
   - **Calendar Name**: (Optional) Specific calendar to sync

4. Click "Test Connection" to verify settings
5. Click "Save" to apply settings

## Using the Application

### System Tray Menu

Right-click the tray icon to access:

- **Force Sync**: Manually sync calendars
- **Settings**: Open configuration dialog
- **Quit**: Exit the application

### Notifications

The application will notify you:
- 1 minute before meetings
- 5 minutes before meetings
- 10 minutes before meetings

### Automatic Features

- **URL Opening**: If a meeting has a URL in the location field, it will automatically open in your browser
- **Sound Alerts**: Plays a sound for each notification (can be disabled in settings)
- **Time Display**: The tray icon shows time until your next meeting

## Configuration Options

### Sync Settings

- **Sync Interval**: How often to check for calendar updates (default: 5 minutes)
- **Sync Period**: How many hours ahead to sync events (default: 24 hours)

### Notification Settings

- **Notification Times**: Comma-separated list of minutes before event (e.g., "1,5,10")
- **Sound Enabled**: Toggle notification sounds on/off

### Other Options

- **Auto Open URLs**: Automatically open meeting URLs in browser

## Troubleshooting

### Connection Issues

1. Verify your CalDAV URL is correct
2. Check username and password
3. Ensure your internet connection is active
4. Try adding/removing trailing slash from URL

### Missing Notifications

1. Check system notification settings
2. Verify the application is running in system tray
3. Ensure sync is working (check last sync time)

### Sound Not Playing

1. Check system volume
2. Verify "Sound Enabled" is checked in settings
3. Ensure WAV files exist in the sounds directory

### Logs

The application writes its log to `.calendar_notifications.log` in your home folder
(on Windows: `%USERPROFILE%\.calendar_notifications.log`).

The log rotates at 20 MB and keeps 4 old files (`.log.1` to `.log.4`).
The log files never use more than 100 MB in total. 