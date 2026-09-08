![Pyrich logo](https://raw.githubusercontent.com/diego-cores/pyrich/main/images/logo.png)
![Version](https://img.shields.io/badge/version-1.0.2-blue) ![License](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=fff) ![Python>=3.11](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=fff) ![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=fff) ![Binance](https://img.shields.io/badge/Binance-F0B90B?logo=binance&logoColor=fff)

## Stay rich. Stay present

A Python-based Discord Rich Presence client for Binance USDS-M Futures traders.
Displays your open positions, closed positions, and assets changes.
Your trades, on your Discord profile.

---

## ⚠️ Important Notices

- **Pyrich** is not affiliated with or endorsed by **Binance**.
- By using this software you agree to the [License](LICENSE) terms.

---

![Preview](https://raw.githubusercontent.com/diego-cores/pyrich/main/images/preview.png "Pyrich preview")

---

## 📦 Installation

1. **Download** — Go to the [releases page](https://github.com/diego-cores/pyrich/releases) and download the latest ZIP.
2. **Unzip** — Extract the contents to any directory you prefer.
3. **Install dependencies** — Open a terminal in that folder and run: `pip install -r requirements.txt`.
4. **Upload images** — In [Discord Developer Portal](https://discord.com/developers/applications) → Your App → Rich Presence, upload the images from `/images/upload`.
5. **Create .env** — Create a `.env` file in the repository directory with the following variables:

```env
CLIENT_ID=  # Discord app ID
API_KEY=    # Binance API key
SECRET_KEY= # Binance secret key
```

---

## 🚀 Quick start

Run the main script:

```bash
python src/main.py
```

**Windows users:** Use `pyrich.bat` instead and place a shortcut in the startup folder to run it automatically on boot.

To stop the process:

```bash
python kill_prss.py
```

---

## ⚙️ Configuration

Create a `config.toml` file in the repository directory.
See `default.toml` for all available parameters and examples.

### 🪛 Main parameters

**`[assets.SYMBOL]`** — Replace `SYMBOL` with the actual Binance USDS-M Futures symbol.

- `img` — Image name registered in Discord Developer -> App -> Rich Presence.
- `name` — Display name for the symbol.

**`[general]`**

- `trade_assets` — Symbols to display trades. Use `*` to mirror the `assets` list.
- `repo_mode` — Enables or disables `repository_mode`.

---

## ✨ Support

If you found Pyrich useful, please consider leaving a ⭐ — it would be much appreciated!
