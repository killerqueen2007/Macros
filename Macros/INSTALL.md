# Platform-Specific Installation Guide

This guide provides detailed, step-by-step instructions for each operating system.

---

## Table of Contents
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Quick Start Commands](#quick-start-commands)

---

## Windows Installation

### Prerequisites
- Windows 10 or later
- Administrator access

### Step-by-Step

1. **Install Python**
   - Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
   - Verify installation:
     ```cmd
     python --version
     ```

2. **Download the Application**
   - Extract the ZIP file to a folder (e.g., `C:\MacroApp`)

3. **Install Dependencies**
   ```cmd
   cd C:\MacroApp
   pip install -r requirements.txt
   ```

4. **First Run**
   ```cmd
   Start.bat
   ```
   Or:
   ```cmd
   python main.py
   ```

5. **Verify Installation**
   - A tray icon should appear in your system tray (bottom-right)
   - Right-click the icon to access the menu

### Troubleshooting Windows

**Problem: "Python is not recognized"**
- Solution: Reinstall Python and check "Add to PATH"
- Or add Python manually to PATH in System Environment Variables

**Problem: Macros don't work**
- Solution: Run as administrator
- Right-click `Start.bat` → "Run as administrator"

**Problem: Tray icon doesn't appear**
- Solution: Check Windows notification area settings
- Settings → Personalization → Taskbar → Select which icons appear

---

## Linux Installation

### Supported Distributions
- Ubuntu 20.04+
- Debian 11+
- Fedora 35+
- Arch Linux
- Pop!_OS
- Linux Mint
- Most other distributions with X11 or Wayland

### Prerequisites
- Python 3.8+
- sudo access
- X11 (recommended) or Wayland

### Step-by-Step for Ubuntu/Debian

1. **Update System**
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. **Install System Dependencies**
   ```bash
   sudo apt install python3 python3-pip python3-tk xdotool
   ```

3. **Download and Extract**
   ```bash
   cd ~/Downloads
   unzip macro-app.zip
   cd macro-app
   ```

4. **Install Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Make Scripts Executable**
   ```bash
   chmod +x start.sh
   ```

6. **Setup Permissions (Choose One Method)**

   **Method A: Add to Input Group (Recommended)**
   ```bash
   sudo usermod -a -G input $USER
   ```
   Then **log out and log back in**.

   **Method B: Run with Sudo Each Time**
   ```bash
   sudo python3 main.py
   ```

7. **First Run**
   ```bash
   ./start.sh
   ```

### Step-by-Step for Fedora/RHEL

1. **Install Dependencies**
   ```bash
   sudo dnf install python3 python3-pip python3-tkinter xdotool
   ```

2. **Continue with steps 3-7 from Ubuntu instructions above**

### Step-by-Step for Arch Linux

1. **Install Dependencies**
   ```bash
   sudo pacman -S python python-pip tk xdotool
   ```

2. **Continue with steps 3-7 from Ubuntu instructions above**

### Troubleshooting Linux

**Problem: "xdotool: command not found"**
```bash
sudo apt install xdotool        # Debian/Ubuntu
sudo dnf install xdotool        # Fedora
sudo pacman -S xdotool          # Arch
```

**Problem: "Permission denied" on keyboard events**
- Run with sudo: `sudo python3 main.py`
- Or add to input group and re-login

**Problem: Tray icon doesn't appear (GNOME)**
```bash
# Install GNOME extension
sudo apt install gnome-shell-extension-appindicator
# Enable it in Extensions app or GNOME Tweaks
```

**Problem: Works on X11 but not Wayland**
- Switch to X11 session at login screen
- Or accept limited functionality on Wayland

**Problem: "No module named 'tkinter'"**
```bash
sudo apt install python3-tk     # Debian/Ubuntu
```

### Autostart on Linux (Optional)

**Using systemd:**
```bash
# Edit service file
nano macro-app.service

# Update YOUR_USERNAME and /path/to/macro/app

# Install
sudo cp macro-app.service /etc/systemd/system/
sudo systemctl enable macro-app.service
sudo systemctl start macro-app.service
```

**Using desktop autostart:**
```bash
# Edit desktop file
nano macro-app.desktop

# Update /path/to/macro/app

# Install
mkdir -p ~/.config/autostart
cp macro-app.desktop ~/.config/autostart/
```

---

## macOS Installation

### Prerequisites
- macOS 10.14 (Mojave) or later
- Administrator access

### Step-by-Step

1. **Install Homebrew** (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python and Tkinter**
   ```bash
   brew install python-tk
   ```

3. **Download and Extract the Application**
   ```bash
   cd ~/Downloads
   unzip macro-app.zip
   cd macro-app
   ```

4. **Install Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Make Script Executable**
   ```bash
   chmod +x start.sh
   ```

6. **First Run**
   ```bash
   python3 main.py
   ```

7. **Grant Permissions**
   - macOS will prompt for accessibility permissions
   - Go to: System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal (or your terminal app) to the list
   - Check the box to enable it

### Troubleshooting macOS (Untested)

**Problem: "Permission denied" errors**
- Grant accessibility permissions (see step 7 above)

**Problem: "No module named '_tkinter'"**
```bash
brew install python-tk
```

**Problem: Keyboard events not detected**
- Check Security & Privacy → Privacy → Accessibility
- Make sure Terminal/iTerm has permission

### Autostart on macOS

1. Open System Preferences → Users & Groups
2. Select your user
3. Click "Login Items" tab
4. Click '+' button
5. Navigate to the application folder
6. Add `start.sh` or create an Application wrapper

---

## Quick Start Commands

### Windows
```cmd
# Install
pip install -r requirements.txt

# Run
Start.bat
```

### Linux (Ubuntu/Debian)
```bash
# Install
sudo apt install python3 python3-pip python3-tk xdotool
pip3 install -r requirements.txt
sudo usermod -a -G input $USER
# Log out and back in

# Run
./start.sh
```

### macOS
```bash
# Install
brew install python-tk
pip3 install -r requirements.txt

# Run
python3 main.py
```

---

## Verification Checklist

After installation, verify:

- [ ] Python version 3.8 or higher: `python --version` or `python3 --version`
- [ ] All dependencies installed: `pip list` shows pystray, keyboard, etc.
- [ ] Application starts without errors
- [ ] Tray icon appears in system tray
- [ ] Can open Macro Editor from tray menu
- [ ] Test a simple macro works

---

## Uninstallation

### Windows
1. Close the application (right-click tray icon → Quit)
2. Delete the application folder
3. Optionally uninstall Python packages:
   ```cmd
   pip uninstall pystray keyboard pyautogui -y
   ```

### Linux
1. Stop the application
2. Remove autostart entries if configured
3. Delete the application folder
4. Optionally remove from input group:
   ```bash
   sudo gpasswd -d $USER input
   ```

### macOS
1. Quit the application
2. Remove from Login Items if configured
3. Delete the application folder
4. Optionally uninstall packages:
   ```bash
   pip3 uninstall pystray keyboard pyautogui -y
   ```
