# FSUUMC PvP Rankings

A local Flask + SQLite ranking site for FSUUMC. Includes all eight MCTiers-style modes, clickable tier lists, player profiles, owner-only editing, tier badges, mode logos, and title badges.

## Ranking rules

**Modes:** Vanilla, UHC, Pot, NethOP, SMP, Sword, Axe, Mace.

**Tier points:** HT1 60, LT1 45, HT2 30, LT2 20, HT3 10, LT3 6, HT4 4, LT4 3, HT5 2, LT5 1.

Points from all eight modes are added. An empty mode gives 0 points. This version calculates points from the tier currently entered; it does not track historical peak or retired tiers.

**Titles:** Combat Grandmaster 400+, Combat Master 250+, Combat Ace 100+, Combat Specialist 50+, Combat Cadet 20+, Combat Novice 10+, Rookie below 10.

These are the MCTiers-style values, not an official affiliation or endorsement.

## Windows 10 setup

1. Install Python 3.10 or newer.
2. Extract this ZIP.
3. Open the extracted `FSUUMC_Tier_Website` folder.
4. Click the address bar in File Explorer, type `cmd`, and press Enter.
5. Run these commands one at a time:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

6. Create an owner password hash:

```bat
py -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('New owner password: ')))"
```

Copy the full hash that appears. Do not share it. Then set it in the same Command Prompt window:

```bat
set "OWNER_PASSWORD_HASH=PASTE_THE_FULL_HASH_HERE"
set "FLASK_SECRET_KEY=PASTE_A_LONG_RANDOM_SECRET_HERE"
py app.py
```

7. Open `http://127.0.0.1:5000`.
8. Owner login: `http://127.0.0.1:5000/login`.

Keep the Command Prompt window open while using the site. To stop the server, press `Ctrl+C`.

## Owner dashboard

After logging in, open `/admin` to add or update players, assign tiers for all eight modes, edit the announcement, and delete entries. Use the exact Minecraft username. Player heads load from the public mc-heads.net service when internet is available.

## Before public hosting

- Change the owner password to a new, unique password.
- Use a strong random `FLASK_SECRET_KEY`.
- Set both environment variables in your hosting provider's secret/environment settings.
- Use a production WSGI server (such as Waitress or Gunicorn); do not expose Flask's development server directly.
- Back up `fsuumc.db` regularly.
- The site starts with no fake player entries. Add verified players through `/admin`.
