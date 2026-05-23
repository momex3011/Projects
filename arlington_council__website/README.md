# Arlington City Council Portal

This is a standalone Arlington/DFW version of the council platform. It keeps the same core systems from the Al-Nabk build:

- public home page, announcements, and news posts
- projects, tracking, volunteer requests, and project voting
- council proposals with visibility and vote transparency controls
- donation campaigns, groups, pledges, and admin confirmation flows
- public suggestions routed to the council or project trackers
- admin hub, users, permissions, site links, useful sites, and content management
- English/Spanish routing, dark mode, and Expo Go mobile app

The visual system uses a UTA-inspired blue/orange civic palette with an Arlington-focused content model, Spanish localization, and seeded demo data.

## Run The Website

```powershell
cd path\to\ready_to_move_apps\arlington\website
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Open:

```text
http://127.0.0.1:5000/en/home
```

If the database is new, a local admin account is created with username `admin` and password `admin`.

## Run The Mobile App

```powershell
cd path\to\ready_to_move_apps\arlington\mobile
npm.cmd install
$env:EXPO_PUBLIC_API_BASE_URL="http://YOUR_COMPUTER_IP:5000"
npm.cmd run start
```

Use the computer's Wi-Fi/LAN IP for `EXPO_PUBLIC_API_BASE_URL` when testing on a real phone.
