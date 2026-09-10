# Tactical Fire Direction Dashboard (IOE HUD v4.2)

A desktop tactical fire direction command dashboard interface built with Python and **PySide6** (Qt for Python).

---

## 🚀 How to Run on macOS

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your Mac.

Check if Python is installed:
```bash
python3 --version
```
> *If Python 3 is not installed, install it using [Homebrew](https://brew.sh/):*
> ```bash
> brew install python
> ```

---

### 2. Navigate to Project Directory
Open **Terminal** on your Mac and navigate to the project directory:
```bash
cd /path/to/tactical_fire_direction_dashboard
```

---

### 3. Set Up a Virtual Environment (Recommended)
Creating a virtual environment isolates project dependencies:

```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

---

### 4. Install Dependencies
Install dependencies from the consolidated requirements file one level up
(shared with ArtilleryProject_Backend, so one install covers both):
```bash
pip install -r ../requirements.txt
```
*(Or directly: `pip install PySide6`)*

---

### 5. Launch the Application
Run the main script:
```bash
python3 main.py
```

---

## 🛠️ Troubleshooting on macOS

- **"ModuleNotFoundError: No module named 'PySide6'"**
  Ensure your virtual environment is activated (`source venv/bin/activate`) before running `main.py`.

- **macOS Security & Permissions (Camera / Input / Window focus)**
  When launching PySide6 applications for the first time, macOS may prompt for terminal permissions to display interactive desktop windows. Grant Terminal permission if prompted.

- **Apple Silicon (M1 / M2 / M3 / M4) Macs**
  PySide6 has native `arm64` wheels for Apple Silicon. Ensure you are running a native `arm64` version of Python (`python3 -c "import platform; print(platform.machine())"` should print `arm64`).

---

## 🧪 Run Tests (Offscreen Verification)
To verify layout and GUI signal integrity without launching the visual window:
```bash
python3 test_app.py
```
