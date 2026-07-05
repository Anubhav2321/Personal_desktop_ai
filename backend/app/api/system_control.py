"""
ARIS System Control Engine
Full laptop access: apps, files, system info, media, web, screenshots, volume.
"""

import subprocess
import os
import platform
import webbrowser
import shutil
import json
import ctypes
import glob
from datetime import datetime
from pathlib import Path

# Web search service for internet knowledge
from ..services.web_search import search_web, get_web_info, get_news

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


# ==========================================
# 🔋 SYSTEM INFORMATION
# ==========================================

def get_system_stats():
    """Get comprehensive system stats: CPU, RAM, battery, disk, network."""
    stats = {
        "cpu_percent": 0,
        "ram_used_gb": 0,
        "ram_total_gb": 0,
        "ram_percent": 0,
        "battery_percent": None,
        "battery_charging": None,
        "battery_time_left": None,
        "disk_used_gb": 0,
        "disk_total_gb": 0,
        "disk_percent": 0,
        "boot_time": None,
        "platform": platform.system(),
        "hostname": platform.node(),
        "username": os.getlogin(),
    }

    if not PSUTIL_AVAILABLE:
        return stats

    # CPU
    # interval=0 returns cached value (non-blocking) instead of blocking for 500ms
    stats["cpu_percent"] = psutil.cpu_percent(interval=0)

    # RAM
    mem = psutil.virtual_memory()
    stats["ram_used_gb"] = round(mem.used / (1024 ** 3), 1)
    stats["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
    stats["ram_percent"] = mem.percent

    # Battery
    battery = psutil.sensors_battery()
    if battery:
        stats["battery_percent"] = round(battery.percent)
        stats["battery_charging"] = battery.power_plugged
        if battery.secsleft > 0 and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
            hours = battery.secsleft // 3600
            minutes = (battery.secsleft % 3600) // 60
            stats["battery_time_left"] = f"{hours}h {minutes}m"

    # Disk
    disk = psutil.disk_usage('/')
    stats["disk_used_gb"] = round(disk.used / (1024 ** 3), 1)
    stats["disk_total_gb"] = round(disk.total / (1024 ** 3), 1)
    stats["disk_percent"] = round(disk.percent)

    # Boot time
    boot = datetime.fromtimestamp(psutil.boot_time())
    stats["boot_time"] = boot.strftime("%Y-%m-%d %H:%M:%S")

    return stats


def get_battery_info():
    """Get detailed battery information."""
    if not PSUTIL_AVAILABLE:
        return "psutil is not installed. Cannot read battery info."
    
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery detected — this might be a desktop PC."
    
    status = "Charging" if battery.power_plugged else "Discharging"
    time_left = ""
    if battery.secsleft > 0 and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
        hours = battery.secsleft // 3600
        minutes = (battery.secsleft % 3600) // 60
        time_left = f", approximately {hours} hours and {minutes} minutes remaining"
    
    return f"Battery is at {round(battery.percent)}% and is currently {status}{time_left}."


def get_network_info():
    """Get network/WiFi info."""
    if not PSUTIL_AVAILABLE:
        return "psutil not available."
    
    info = []
    addrs = psutil.net_if_addrs()
    for iface, addr_list in addrs.items():
        for addr in addr_list:
            if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                info.append(f"{iface}: {addr.address}")
    
    if info:
        return "Connected. IP addresses: " + ", ".join(info)
    return "No active network connections detected."


def get_running_processes(limit=15):
    """Get top running processes by memory usage."""
    if not PSUTIL_AVAILABLE:
        return []
    
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            info = proc.info
            if info['memory_percent'] and info['memory_percent'] > 0.1:
                procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    procs.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
    return procs[:limit]


# ==========================================
# 🚀 APP LAUNCHER
# ==========================================

# Common Windows apps and their executable paths/commands
# Includes traditional apps, UWP/Store apps, and protocol URIs
WINDOWS_APPS = {
    # --- Classic Windows Apps ---
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "file explorer": "explorer",
    "explorer": "explorer",
    "control panel": "control",
    "settings": "ms-settings:",
    "snipping tool": "snippingtool",
    "snip": "snippingtool",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "system info": "msinfo32",
    "resource monitor": "resmon",
    "event viewer": "eventvwr",
    "registry editor": "regedit",
    "character map": "charmap",
    "wordpad": "wordpad",
    "magnifier": "magnify",
    "on-screen keyboard": "osk",
    "remote desktop": "mstsc",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "maps": "bingmaps:",
    "mail": "outlookmail:",
    "calendar": "outlookcal:",
    "photos": "ms-photos:",
    "camera": "microsoft.windows.camera:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "feedback hub": "feedback-hub:",
    "xbox": "xbox:",
    
    # --- Browsers ---
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "mozilla firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "brave": "brave",
    "opera": "opera",
    
    # --- Communication / Social (UWP protocol URIs) ---
    "whatsapp": "whatsapp:",
    "telegram": "tg:",
    "teams": "msteams:",
    "microsoft teams": "msteams:",
    "zoom": "zoommtg:",
    "skype": "skype:",
    
    # --- Dev Tools ---
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "visual studio": "devenv",
    "git bash": "git-bash",
    "postman": "postman",
    
    # --- Media ---
    "spotify": "spotify:",
    "vlc": "vlc",
    "itunes": "itunes",
    
    # --- Productivity ---
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "microsoft powerpoint": "powerpnt",
    "onenote": "onenote:",
    "outlook": "outlook",
    
    # --- Gaming ---
    "steam": "steam:",
    "discord": "discord:",
    "epic games": "com.epicgames.launcher:",
    
    # --- AI Apps ---
    "chatgpt": "chatgpt:",
    "copilot": "ms-copilot:",
    "microsoft copilot": "ms-copilot:",
}


def _search_start_menu(app_name):
    """Search Windows Start Menu shortcuts for an app by name."""
    search_dirs = [
        os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs'),
        r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs',
    ]
    
    app_lower = app_name.lower()
    
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        # Walk the directory tree looking for .lnk files
        for root, dirs, files in os.walk(search_dir):
            for f in files:
                if f.lower().endswith('.lnk') and app_lower in f.lower():
                    return os.path.join(root, f)
    
    return None


def _search_uwp_apps(app_name):
    """Search installed UWP/Store apps using PowerShell."""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-StartApps | Where-Object {{$_.Name -like "*{app_name}*"}} | Select-Object -First 1 -ExpandProperty AppId'],
            capture_output=True, text=True, timeout=8
        )
        app_id = result.stdout.strip()
        if app_id:
            return app_id
    except Exception:
        pass
    return None


def open_application(app_name):
    """Open a Windows application by name. Supports classic apps, UWP/Store apps, and protocol URIs."""
    app_lower = app_name.lower().strip()
    
    # 1. Check known apps dictionary
    if app_lower in WINDOWS_APPS:
        cmd = WINDOWS_APPS[app_lower]
        try:
            if cmd.endswith(':'):  # Protocol URI (ms-settings:, whatsapp:, spotify:, etc.)
                os.system(f'start "" "{cmd}"')
            else:
                subprocess.Popen(cmd, shell=True)
            return f"Successfully launched {app_name}."
        except Exception as e:
            # Fall through to smart discovery
            pass
    
    # 2. Search Start Menu shortcuts
    shortcut = _search_start_menu(app_name)
    if shortcut:
        try:
            os.startfile(shortcut)
            return f"Successfully launched {app_name} (found in Start Menu)."
        except Exception:
            pass
    
    # 3. Search UWP/Store apps via PowerShell Get-StartApps
    uwp_id = _search_uwp_apps(app_name)
    if uwp_id:
        try:
            subprocess.Popen(f'explorer shell:AppsFolder\\{uwp_id}', shell=True)
            return f"Successfully launched {app_name} (Windows Store app)."
        except Exception:
            pass
    
    # 4. Final fallback — try direct command
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"Attempting to launch {app_name}."
    except Exception as e:
        return f"Could not find or open '{app_name}'. Please make sure it is installed."


# ==========================================
# 🌐 WEB ACTIONS
# ==========================================

def open_url(url):
    """Open a URL in the default browser."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    webbrowser.open(url)
    return f"Opened {url} in your default browser."


def search_google(query):
    """Search Google for a query."""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching Google for '{query}'."


def search_youtube(query):
    """Search YouTube for a query."""
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching YouTube for '{query}'."


def open_youtube():
    """Open YouTube homepage."""
    webbrowser.open("https://www.youtube.com")
    return "Opened YouTube."


def play_on_youtube(song_name):
    """Play a specific song/video on YouTube."""
    url = f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching YouTube for '{song_name}'. Click the first result to play it."


# ==========================================
# 📁 FILE OPERATIONS
# ==========================================

def create_file(filepath, content=""):
    """Create a file at the specified path."""
    try:
        filepath = os.path.expanduser(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File created successfully at: {filepath}"
    except Exception as e:
        return f"Failed to create file: {str(e)}"


def read_file(filepath):
    """Read the content of a file."""
    try:
        filepath = os.path.expanduser(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) > 2000:
            content = content[:2000] + "\n... (truncated, file is larger)"
        return f"Content of {os.path.basename(filepath)}:\n{content}"
    except Exception as e:
        return f"Failed to read file: {str(e)}"


def delete_file(filepath):
    """Delete a file."""
    try:
        filepath = os.path.expanduser(filepath)
        if os.path.isfile(filepath):
            os.remove(filepath)
            return f"File deleted: {filepath}"
        elif os.path.isdir(filepath):
            return "That's a directory, not a file. Use a specific command for directories."
        else:
            return f"File not found: {filepath}"
    except Exception as e:
        return f"Failed to delete file: {str(e)}"


def list_directory(dirpath):
    """List contents of a directory."""
    try:
        dirpath = os.path.expanduser(dirpath)
        if not os.path.isdir(dirpath):
            return f"Directory not found: {dirpath}"
        
        items = os.listdir(dirpath)
        result = f"Contents of {dirpath} ({len(items)} items):\n"
        for item in sorted(items)[:50]:  # Limit to 50 items
            full_path = os.path.join(dirpath, item)
            if os.path.isdir(full_path):
                result += f"  [DIR]  {item}\n"
            else:
                size = os.path.getsize(full_path)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                result += f"  [FILE] {item} ({size_str})\n"
        
        if len(items) > 50:
            result += f"  ... and {len(items) - 50} more items."
        
        return result
    except Exception as e:
        return f"Failed to list directory: {str(e)}"


def open_folder(dirpath):
    """Open a folder in File Explorer."""
    try:
        dirpath = os.path.expanduser(dirpath)
        if os.path.isdir(dirpath):
            os.startfile(dirpath)
            return f"Opened folder: {dirpath}"
        else:
            return f"Directory not found: {dirpath}"
    except Exception as e:
        return f"Failed to open folder: {str(e)}"


# ==========================================
# 🔊 MEDIA / VOLUME CONTROL
# ==========================================

def set_volume(level):
    """Set system volume (0-100) on Windows."""
    try:
        # Use nircmd or PowerShell for volume control
        level = max(0, min(100, int(level)))
        # Map 0-100 to 0-65535 for Windows
        volume_val = int(level / 100 * 65535)
        subprocess.run(
            ['powershell', '-Command',
             f'$obj = New-Object -ComObject WScript.Shell; ' +
             ''.join(['$obj.SendKeys([char]174); ' for _ in range(50)]) +
             ''.join([f'$obj.SendKeys([char]175); ' for _ in range(level // 2)])
            ],
            capture_output=True, timeout=10
        )
        return f"Volume set to approximately {level}%."
    except Exception as e:
        return f"Could not change volume: {str(e)}"


def media_play_pause():
    """Send media play/pause key."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('playpause')
        return "Toggled play/pause."
    return "pyautogui not installed — cannot control media keys."


def media_next():
    """Send media next track key."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('nexttrack')
        return "Skipped to next track."
    return "pyautogui not installed."


def media_prev():
    """Send media previous track key."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('prevtrack')
        return "Went to previous track."
    return "pyautogui not installed."


def volume_up():
    """Increase volume."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('volumeup')
        pyautogui.press('volumeup')
        pyautogui.press('volumeup')
        return "Volume increased."
    return "pyautogui not installed."


def volume_down():
    """Decrease volume."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('volumedown')
        pyautogui.press('volumedown')
        pyautogui.press('volumedown')
        return "Volume decreased."
    return "pyautogui not installed."


def mute_toggle():
    """Toggle mute."""
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press('volumemute')
        return "Toggled mute."
    return "pyautogui not installed."


# ==========================================
# 🖥️ SYSTEM COMMANDS
# ==========================================

def take_screenshot():
    """Take a screenshot and save to Desktop."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(desktop, f"ARIS_Screenshot_{timestamp}.png")
        
        if PYAUTOGUI_AVAILABLE:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return f"Screenshot saved to: {filepath}"
        else:
            # Fallback: use Windows Snipping Tool
            subprocess.Popen("snippingtool", shell=True)
            return "Opened Snipping Tool for screenshot (pyautogui not available for direct capture)."
    except Exception as e:
        return f"Screenshot failed: {str(e)}"


def lock_screen():
    """Lock the Windows screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."
    except Exception as e:
        return f"Failed to lock screen: {str(e)}"


def shutdown_pc(delay=30):
    """Schedule a system shutdown."""
    try:
        os.system(f"shutdown /s /t {delay}")
        return f"System will shutdown in {delay} seconds. Use 'cancel shutdown' to abort."
    except Exception as e:
        return f"Shutdown failed: {str(e)}"


def cancel_shutdown():
    """Cancel a scheduled shutdown."""
    try:
        os.system("shutdown /a")
        return "Shutdown cancelled."
    except Exception as e:
        return f"Failed to cancel shutdown: {str(e)}"


def restart_pc(delay=10):
    """Schedule a system restart."""
    try:
        os.system(f"shutdown /r /t {delay}")
        return f"System will restart in {delay} seconds."
    except Exception as e:
        return f"Restart failed: {str(e)}"


def sleep_pc():
    """Put the PC to sleep."""
    try:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "System going to sleep."
    except Exception as e:
        return f"Sleep failed: {str(e)}"


def kill_process(process_name):
    """Kill a running process by name."""
    try:
        result = subprocess.run(
            ['taskkill', '/IM', process_name, '/F'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return f"Process '{process_name}' has been terminated."
        else:
            return f"Could not terminate '{process_name}': {result.stderr.strip()}"
    except Exception as e:
        return f"Failed to kill process: {str(e)}"


def get_current_time():
    """Get current date and time."""
    now = datetime.now()
    return now.strftime("It's %I:%M %p on %A, %B %d, %Y.")


def get_uptime():
    """Get system uptime."""
    if not PSUTIL_AVAILABLE:
        return "psutil not available."
    
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"System has been running for {uptime.days} days, {hours} hours, and {minutes} minutes."


# ==========================================
# 🎯 MASTER COMMAND EXECUTOR
# ==========================================

# Maps action names to their handler functions
ACTION_REGISTRY = {
    # System info
    "get_battery": get_battery_info,
    "get_system_stats": get_system_stats,
    "get_network_info": get_network_info,
    "get_time": get_current_time,
    "get_uptime": get_uptime,
    "get_processes": get_running_processes,
    
    # App launcher
    "open_app": open_application,
    
    # Web actions
    "open_url": open_url,
    "search_google": search_google,
    "search_youtube": search_youtube,
    "open_youtube": open_youtube,
    "play_youtube": play_on_youtube,
    
    # Internet knowledge (NEW — AI can pull data from the web)
    "web_search": search_web,
    "get_web_info": get_web_info,
    "get_news": get_news,
    
    # File operations
    "create_file": create_file,
    "read_file": read_file,
    "delete_file": delete_file,
    "list_directory": list_directory,
    "open_folder": open_folder,
    
    # Media control
    "play_pause": media_play_pause,
    "next_track": media_next,
    "prev_track": media_prev,
    "volume_up": volume_up,
    "volume_down": volume_down,
    "mute": mute_toggle,
    
    # System commands
    "screenshot": take_screenshot,
    "lock_screen": lock_screen,
    "shutdown": shutdown_pc,
    "cancel_shutdown": cancel_shutdown,
    "restart": restart_pc,
    "sleep": sleep_pc,
    "kill_process": kill_process,
}


def execute_action(action_name, params=None):
    """
    Execute a system action by name with optional parameters.
    Returns the result string.
    """
    if action_name not in ACTION_REGISTRY:
        return f"Unknown action: {action_name}"
    
    handler = ACTION_REGISTRY[action_name]
    
    try:
        if params:
            if isinstance(params, dict):
                return handler(**params)
            elif isinstance(params, (list, tuple)):
                return handler(*params)
            else:
                return handler(params)
        else:
            return handler()
    except Exception as e:
        return f"Action '{action_name}' failed: {str(e)}"
