# Arlington Civic Mobile

Expo Go mobile version for the Arlington City Council Portal.

The app is not a WebView wrapper. It synchronizes with Flask through JSON endpoints added to the website:

- Home summary, announcements, news, useful links
- Projects and project progress
- Public council proposals
- Donation campaigns, groups, and pending donation references
- Public suggestion submission
- Volunteer request submission

## Setup

Install packages:

```powershell
cd path\to\ready_to_move_apps\arlington\mobile
npm.cmd install
```

Run Flask so your phone can reach it over Wi-Fi:

```powershell
cd path\to\ready_to_move_apps\arlington\website
python -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Find your computer's Wi-Fi/LAN address:

```powershell
ipconfig
```

Start Expo with that address:

```powershell
cd path\to\ready_to_move_apps\arlington\mobile
$env:EXPO_PUBLIC_API_BASE_URL="http://YOUR_COMPUTER_IP:5000"
npm.cmd run start
```

If you are using `cmd.exe` instead of PowerShell, use:

```cmd
cd path\to\ready_to_move_apps\arlington\mobile
set EXPO_PUBLIC_API_BASE_URL=http://YOUR_COMPUTER_IP:5000
npm.cmd run start
```

Open the QR code in Expo Go.

## Notes

- Do not use `127.0.0.1` from a real phone. That points to the phone itself, not your computer.
- Keep the phone and computer on the same Wi-Fi network.
- If Expo Go says the project requires a newer version even after updating Expo Go, restart Metro with the scripts above. This app targets Expo SDK 54 to match Expo Go client 54.x.
- Donation pledges create pending payment references in the same database. Real payment-provider integration is still a separate security-sensitive project.
- The app supports English and Spanish, matching the website routes.
- Set `EXPO_PUBLIC_API_BASE_URL` before starting Expo so the app connects to the paired website.
