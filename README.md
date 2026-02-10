# Beyond Binary Hackathon — Voice to Text

This app records audio in the browser, sends it to a Python backend, converts **voice → text**, and saves each transcript as a `.txt` file in `backend/sample/`.

---

## What you need to install

- **Python 3.10+**
- **pip** (comes with most Python installs)
- **ffmpeg** (free, used to convert browser audio → WAV)
- **Vosk English model** (free offline speech‑to‑text model)

Everything else (Flask, Vosk Python package, etc.) is handled by `requirements.txt`.

---

## Step 1 — Install Python dependencies

In a terminal (PowerShell) from the project root:

```bash
cd backend
python -m pip install -r requirements.txt
```

This installs **Flask**, **vosk**, and their Python dependencies.

---

## Step 2 — Install ffmpeg (Windows)

The backend calls `ffmpeg` as a command‑line tool, so it must be on your **PATH**.

### Option A: Using `winget` (recommended)

1. Open a new **PowerShell** window.
2. Run:

```powershell
winget install --id Gyan.FFmpeg -e
```

3. Close that PowerShell window, open a **fresh** one, and verify:

```powershell
ffmpeg -version
```

If you see version information, `ffmpeg` is correctly installed.

### Option B: Manual ZIP download

1. Go to the ffmpeg builds site (e.g. `https://www.gyan.dev/ffmpeg/builds/`).
2. Download a **full** Windows build (for example: “ffmpeg-git-full.7z” or a similar zip).
3. Extract it somewhere, e.g. to `C:\ffmpeg\` so that you have:
   - `C:\ffmpeg\bin\ffmpeg.exe`
4. Add `C:\ffmpeg\bin` to your **PATH**:
   - Open **“Edit the system environment variables”** → **Environment Variables…**
   - Under **User variables**, select `Path` → **Edit** → **New**.
   - Paste `C:\ffmpeg\bin` and click **OK** on all dialogs.
5. Close and reopen PowerShell, then check:

```powershell
ffmpeg -version
```

You must see version info here before starting the app, otherwise audio conversion will fail.

---

## Step 3 — Download and place the Vosk model

1. Open the Vosk model page: `https://alphacephei.com/vosk/models`
2. Download the English small model: **`vosk-model-small-en-us-0.15`** (free).
3. Extract the downloaded archive.
4. Move the extracted folder into your project so that it becomes:

- `backend/models/vosk-model-small-en-us-0.15/`

Inside that directory you should see files like `am`, `conf`, `model.conf`, etc.

The backend expects the model at:

- `C:\Coding Project\Github\Beyond_Binary_Hackathon\backend\models\vosk-model-small-en-us-0.15`

If you want to keep it somewhere else, set the environment variable `VOSK_MODEL_DIR` to that folder path before starting the app, for example:

```powershell
$env:VOSK_MODEL_DIR="C:\path\to\vosk-model-small-en-us-0.15"
python app.py
```

---

## Step 4 — Run the backend server

From the project root (or any folder), in a terminal:

```bash
cd backend
python app.py
```

If everything is set up correctly you should see Flask start on port **5000**.

---

## Step 5 — Use the web app

1. Open your browser and go to:
   - `http://localhost:5000`
2. Click **“Start recording”** and allow microphone access when prompted.
3. Speak into your microphone.
4. Click **“Stop recording”**.
5. The app will:
   - Upload your recording to the backend.
   - Convert the audio to 16 kHz mono WAV using `ffmpeg`.
   - Run offline speech‑to‑text using the Vosk model.
   - Display the transcript on the page.
   - Save the transcript into a text file.

You can also press **“Copy”** next to the transcript to copy the text to your clipboard.

---

## Where transcripts are saved

- Each recording’s transcript is saved into:
  - `backend/sample/transcript_YYYYMMDD_HHMMSS.txt`

You can open these files directly (for example, with VS Code or a text editor) or process them further in other scripts.