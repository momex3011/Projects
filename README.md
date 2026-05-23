# Projects Overview

This repository contains several standalone apps, websites, tools, and games. Each project below is listed in the same order as it appears in the repository root. Use the matching folder name and commands to run the project you want.

Do not commit real secrets such as `.env`, `APIs.env`, API keys, generated credential files, virtual environments, `node_modules`, or production databases.

## 1. `al_nabak_council_mobile`

### Overview

`al_nabak_council_mobile` is the Expo React Native mobile version of the Al-Nabk City Civil Council platform. It is not only a WebView wrapper. It connects to the paired Flask website through JSON API endpoints and uses an in-app WebView only for website-backed screens such as login and dashboard access.

### What It Does

- Shows public home content, announcements, news, useful links, and statistics.
- Displays council projects, project progress, trackers, volunteer counts, and deadlines.
- Shows public council proposals and vote totals.
- Lists donation campaigns and lets users submit pending donation pledges.
- Allows public suggestions to be sent to the council or a project tracker.
- Allows volunteer requests for projects.
- Supports English and Arabic, including right-to-left layout behavior for Arabic.

### How To Activate It

First start the paired Flask website:

```powershell
cd al_nabak_council_website
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Then start the mobile app:

```powershell
cd ..\al_nabak_council_mobile
npm install
$env:EXPO_PUBLIC_API_BASE_URL="http://YOUR_COMPUTER_IP:5000"
npm run start
```

Scan the QR code with Expo Go.

### What Is Needed

- Node.js and npm.
- Expo Go on a phone, or an Android/iOS simulator.
- The paired `al_nabak_council_website` Flask app running.
- Phone and computer on the same Wi-Fi network when using a real phone.
- `EXPO_PUBLIC_API_BASE_URL` set to the computer LAN IP, not `127.0.0.1`.

## 2. `al_nabak_council_website`

### Overview

`al_nabak_council_website` is a Flask and SQLite civic management portal for the Al-Nabk City Civil Council. It powers the public website, admin workflows, role-based dashboards, donation tools, proposal voting, and the mobile API used by `al_nabak_council_mobile`.

### What It Does

- Provides public pages for home content, useful sites, projects, calendar, proposals, donations, and suggestions.
- Supports user login, registration, profile editing, and role-based permissions.
- Includes roles for admins, council members, project trackers, and news editors.
- Allows admins to manage users, permissions, site links, home posts, donation campaigns, and donation confirmations.
- Allows project creation, project voting, project assignment, progress tracking, comments, and volunteer requests.
- Supports council proposals with visibility controls, voting deadlines, and vote totals.
- Supports English and Arabic through Flask-Babel translations.
- Exposes mobile JSON endpoints under `/<locale>/api/mobile/...`.

### How To Activate It

```powershell
cd al_nabak_council_website
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEFAULT_ADMIN_PASSWORD="choose-a-password"
.\.venv\Scripts\python.exe -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Open:

```text
http://127.0.0.1:5000/en/home
```

The default admin username is `admin`. If `DEFAULT_ADMIN_PASSWORD` is not set, the app generates a password and writes it to `instance/default_admin_credentials.txt`.

### What Is Needed

- Python 3.
- Dependencies from `requirements.txt`.
- SQLite, which is used automatically through `instance/site.db`.
- Optional `SECRET_KEY` environment variable for production.
- Optional `DEFAULT_ADMIN_PASSWORD` environment variable for predictable local admin login.

## 3. `arlington_council__mobile`

### Overview

`arlington_council__mobile` is the Expo React Native mobile version of the Arlington City Council Portal. It connects to the paired Arlington Flask website through API endpoints and gives residents a mobile-friendly way to view projects, donations, proposals, suggestions, and role-based web tools.

### What It Does

- Shows Arlington-focused public updates, announcements, news, and civic statistics.
- Displays projects, project progress, trackers, deadlines, and volunteer actions.
- Shows donation campaigns and allows pending donation pledges.
- Shows public council proposals and vote totals.
- Allows users to submit suggestions to the council or project trackers.
- Opens login, dashboard, donation admin, donation dashboard, and role workspace pages through an in-app WebView.
- Supports English and Spanish.

### How To Activate It

First start the paired Flask website:

```powershell
cd arlington_council__website
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Then start the mobile app:

```powershell
cd ..\arlington_council__mobile
npm install
$env:EXPO_PUBLIC_API_BASE_URL="http://YOUR_COMPUTER_IP:5000"
npm run start
```

Scan the QR code with Expo Go.

### What Is Needed

- Node.js and npm.
- Expo Go on a phone, or an Android/iOS simulator.
- The paired `arlington_council__website` Flask app running.
- Phone and computer on the same Wi-Fi network when using a real phone.
- `EXPO_PUBLIC_API_BASE_URL` set to the computer LAN IP, not `127.0.0.1`.

## 4. `arlington_council__website`

### Overview

`arlington_council__website` is a standalone Arlington and DFW version of the council platform. It keeps the same core civic systems as the Al-Nabk build but uses Arlington-focused content, English/Spanish localization, and a UTA-inspired blue/orange visual style.

### What It Does

- Provides public home content, announcements, news posts, useful links, projects, calendar, donations, suggestions, and proposal pages.
- Includes role-based workspaces for admins, council members, trackers, and news editors.
- Supports project creation, progress tracking, voting, comments, volunteer requests, and tracker assignment.
- Supports public and internal council proposals with vote transparency controls.
- Supports donation campaigns, groups, pledges, payment references, and admin confirmation flows.
- Includes admin dashboards, analytics, user management, site options, and mobile JSON APIs.
- Supports English and Spanish through Flask-Babel.

### How To Activate It

```powershell
cd arlington_council__website
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --debug --host 0.0.0.0 --port 5000
```

Open:

```text
http://127.0.0.1:5000/en/home
```

For a new database, the default admin login is:

```text
username: admin
password: admin
```

You can override the password by setting `DEFAULT_ADMIN_PASSWORD` before the first run.

### What Is Needed

- Python 3.
- Dependencies from `requirements.txt`.
- SQLite, which is used automatically through `instance/site.db`.
- Optional `DEFAULT_ADMIN_PASSWORD` environment variable for local setup.

## 5. `flag_designer`

### Overview

`flag_designer` is a desktop flag design tool built with Python, Tkinter, and Pillow. It lets users create flag layouts visually, customize colors, add text or image layers, preview the result, and export the final design as a PNG.

### What It Does

- Provides preset flag structures such as solid field, bicolor, tricolor, quartered, canton, Nordic cross, diagonal split, and chevron.
- Provides palette presets and manual color selection.
- Allows text layers with font, color, size, opacity, rotation, and placement controls.
- Allows image/emblem layers from local image files.
- Renders a large flag canvas and a live preview.
- Exports the completed flag to PNG.

### How To Activate It

```powershell
cd flag_designer
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe flag_designer.py
```

### What Is Needed

- Python 3.
- Tkinter, usually included with the standard Python installer.
- Pillow from `requirements.txt`.
- Local image files if you want to add emblems or symbols.

## 6. `Flappy_Game`

### Overview

`Flappy_Game` is a Pygame version of a Flappy Bird-style arcade game. The player keeps a bird in the air, avoids pipes, earns points by passing pipe pairs, and can restart after game over.

### What It Does

- Runs a side-scrolling obstacle game.
- Uses gravity, flap input, pipe spawning, collision detection, scoring, and a game-over screen.
- Supports keyboard and mouse input.
- Plays background music and sound effects when the required audio assets are present.

### How To Activate It

```powershell
cd Flappy_Game
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pygame
.\.venv\Scripts\python.exe flappy_game.py
```

### What Is Needed

- Python 3.
- Pygame.
- Required asset files in `assets/sprites/`: `background-day.png`, `base.png`, `pipe-green.png`, `bird1.png`, `bird2.png`, and `bird3.png`.
- Required audio files in `assets/audio/`: `wing.wav`, `point.wav`, `hit.wav`, and `music.mp3`.
- Controls: press `Space` or click/tap to flap.

## 7. `hospital app`

### Overview

`hospital app` is a Java Swing desktop application for basic hospital patient management. It stores patient records locally, displays saved patients, and allows treatments to be attached to patients.

### What It Does

- Opens a desktop GUI using Java Swing.
- Lets users add patients with ID, name, address, and phone number.
- Displays saved patients in a text area.
- Allows treatments to be added to selected patients.
- Stores and loads patient data through `patient_data.txt`.
- Includes a `HospitalDatabase` class for JDBC-style database access, although the main GUI currently uses the file-based data handler.

### How To Activate It

```powershell
cd "hospital app"
javac *.java
java Main
```

### What Is Needed

- Java JDK.
- Write access to `patient_data.txt`.
- Optional database and JDBC driver only if you extend or use `HospitalDatabase`.

## 8. `organizer_app`

### Overview

`organizer_app` is a Python Tkinter desktop utility that watches a selected folder and automatically sorts files into category folders based on file extension.

### What It Does

- Lets the user choose a folder through a desktop GUI.
- Sorts images, documents, videos, audio, archives, and scripts into matching subfolders.
- Keeps unmatched files in place.
- Avoids overwriting files by creating unique destination names.
- Rechecks the selected folder every few seconds while the organizer is running.
- Shows actions and errors in an activity log.

### How To Activate It

```powershell
cd organizer_app
python organizer_app.py
```

### What Is Needed

- Python 3.
- Tkinter, usually included with the standard Python installer.
- A folder you want the organizer to watch and sort.

## 9. `Pokechat`

### Overview

`Pokechat` is a full-stack Pokemon assistant built with a React frontend and a Flask backend. The frontend lets users ask Pokemon-related questions, while the backend sends the query to Azure OpenAI and returns Pokemon names or IDs that the frontend displays as cards.

### What It Does

- Provides a React web interface with Home, Pokemon card browser, and PokeChat assistant pages.
- Lets users type custom Pokemon prompts or use preset prompt buttons.
- Calls a Flask API endpoint at `/chat/query`.
- Uses Azure OpenAI to interpret the user's Pokemon request.
- Normalizes returned Pokemon IDs or names.
- Uses PokeAPI on the frontend to display Pokemon card details.
- Includes a Makefile workflow for install, backend, frontend, and submission packaging.

### How To Activate It

Create and fill in the environment file:

```powershell
cd Pokechat
copy .env.example .env
```

Edit `.env` and fill in the Azure OpenAI values.

Install and run the backend:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\backend\.venv\Scripts\python.exe backend\chat.py
```

In a second terminal, run the frontend:

```powershell
cd Pokechat
npm install
npm start
```

If `make` is available on your system, you can also use:

```bash
make install
make backend
make frontend
```

### What Is Needed

- Python 3.
- Node.js and npm.
- Azure OpenAI endpoint, API key, API version, and deployment name in `.env`.
- Internet access for Azure OpenAI and PokeAPI.
- Backend running on port `3001` by default.
- Frontend running through Create React App, usually on `http://localhost:3000`.

## 10. `Pong`

### Overview

`Pong` is a Pygame recreation of Pong with a player paddle, computer opponent, difficulty selection, score tracking, and a win condition.

### What It Does

- Opens a Pygame window with a Pong court.
- Lets the player choose Easy, Normal, or Hard.
- Uses mouse movement to control the player paddle.
- Runs an AI-controlled opponent paddle.
- Tracks player and opponent scores.
- Ends the round when either side reaches the win score.

### How To Activate It

```powershell
cd Pong
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pygame
.\.venv\Scripts\python.exe pong_game.py
```

### What Is Needed

- Python 3.
- Pygame.
- Mouse input for paddle movement.

## 11. `project_alnabak`

### Overview

`project_alnabak` is the original Flask version of the Al-Nabk council project tracking system. It is a simpler predecessor to `al_nabak_council_website` and focuses on users, projects, voting, tracker assignment, volunteer requests, and calendar views.

### What It Does

- Provides localized English and Arabic Flask pages.
- Supports login, logout, profile editing, and user roles.
- Includes admin, council member, and tracker roles.
- Allows project creation, editing, voting, and results viewing.
- Allows project tracker assignment and tracker-only project progress access.
- Supports volunteer requests for projects.
- Includes basic Flask-Admin model management and analytics.
- Stores data in SQLite under `instance/site.db`.

### How To Activate It

```powershell
cd project_alnabak
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open:

```text
http://127.0.0.1:5000/en/dashboard
```

For a new database, the default admin login is:

```text
username: admin
password: adminpassword
```

### What Is Needed

- Python 3.
- Dependencies from `requirements.txt`.
- SQLite, created automatically in `instance/site.db`.
- A stronger `SECRET_KEY` and changed default password before any real deployment.

## 12. `Server_app`

### Overview

`Server_app` is a simple socket-based chat system. It includes a threaded Python TCP server and a CustomTkinter desktop client that connects to the server and exchanges messages with other connected clients.

### What It Does

- Runs a TCP server on port `12345`.
- Accepts multiple clients.
- Handles each client on its own thread.
- Broadcasts messages from one client to all other clients.
- Provides a GUI client with server IP input, chat display, message field, and send button.

### How To Activate It

Start the server:

```powershell
cd Server_app
python server.py
```

Start one or more clients in separate terminals or computers:

```powershell
cd Server_app
python -m pip install customtkinter
python client.py
```

Enter the server computer's IP address in the client.

### What Is Needed

- Python 3.
- `customtkinter` for the GUI client.
- Devices on the same network, or firewall/network rules that allow TCP port `12345`.
- Run `server.py` before connecting clients.

## 13. `Space_Shooter`

### Overview

`Space_Shooter` is a Pygame arcade shooter. The player controls a ship, shoots lasers, destroys enemies, earns points, and can restart after losing.

### What It Does

- Opens a Pygame window with a start screen.
- Lets the player move left and right.
- Fires lasers with the spacebar.
- Spawns enemies and tracks laser-enemy collisions.
- Adds score for each enemy destroyed.
- Ends the game when an enemy hits the player.
- Supports restart or quit from the game-over screen.

### How To Activate It

```powershell
cd Space_Shooter
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pygame
.\.venv\Scripts\python.exe Space_Shooter.py
```

### What Is Needed

- Python 3.
- Pygame.
- Required image assets in the project folder: `player.png`, `enemy.png`, and `laser.png`.
- Controls: arrow keys or `A`/`D` to move, `Space` to shoot.

## 14. `UTA-CampusFlow-main`

### Overview

`UTA-CampusFlow-main` is an Expo Router mobile app for University of Texas at Arlington campus life. It combines campus activity widgets, crowd reporting, maps, dining/gym/library views, gamification, Firebase authentication, and Firestore-backed data.

### What It Does

- Supports UTA email login, signup, email verification, password reset, and guest login.
- Uses Firebase Authentication and Firestore.
- Shows home widgets for bus arrival, gym capacity, dining status, and campus activity.
- Includes heat map, survey/reporting, bus tracker, dining availability, fitness center, library, leaderboard, and theme shop screens.
- Gives signed-in users MavPoints for participation and displays leaderboard-style gamification.
- Restricts full account login to emails ending in `@mavs.uta.edu`.

### How To Activate It

```powershell
cd UTA-CampusFlow-main
npm install
npx expo start
```

Then run it in Expo Go, an Android emulator, an iOS simulator, or web if supported by the selected features.

### What Is Needed

- Node.js and npm.
- Expo Go or a mobile simulator.
- Firebase project configured in `firebase/firebase.ts`.
- Firebase Authentication enabled for email/password and anonymous sign-in if using guest mode.
- Firestore enabled for reports, users, surveys, leaderboard, and points data.
- Internet access for Firebase services.

## 15. `Video switch file format and type`

### Overview

`Video switch file format and type` is a full-stack media conversion app. The frontend is built with Next.js, React, TypeScript, and Tailwind CSS. The backend is built with FastAPI and uses FFmpeg to handle chunked uploads and convert media files between GIF, video, and animated image formats.

### What It Does

- Provides a polished web interface for selecting conversion tools.
- Supports tools such as GIF maker, video to GIF, GIF to MP4, GIF to WebM, GIF to MOV, WebP to GIF, APNG to GIF, and AVIF to GIF.
- Accepts chunked uploads for large files.
- Validates file type and upload size.
- Uses FFmpeg to create converted output files.
- Provides a download endpoint for finished conversions.
- Includes placeholder AI processing endpoints for future upscaling, colorization, interpolation, restoration, and audio enhancement.

### How To Activate It

Start the FastAPI backend:

```powershell
cd "Video switch file format and type"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Start the Next.js frontend in a second terminal:

```powershell
cd "Video switch file format and type\frontend"
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

### What Is Needed

- Python 3.
- Node.js and npm.
- Backend dependencies from `backend/requirements.txt`.
- Frontend dependencies from `frontend/package.json`.
- FFmpeg and FFprobe installed and available on `PATH`.
- Storage folders are created automatically under `storage/`.

## 16. `War-Tracker`

### Overview

`War-Tracker` is a Flask-based conflict mapping and war event tracking platform. It stores wars, events, factions, sub-factions, territories, territory snapshots, capitals, sources, and location data, then displays that information through public maps and admin tools.

### What It Does

- Provides a public list of tracked wars.
- Shows war maps with event data by date.
- Exposes API endpoints for wars, events, categories, territories, hotspots, factions, capitals, snapshots, and territory history.
- Includes admin tools for creating wars and events.
- Includes faction and sub-faction management.
- Includes an interactive territory editor using GeoJSON.
- Supports time-based territory snapshots so map control can be viewed by date.
- Includes ingestion scripts for gathering and analyzing conflict-related source data.
- Includes AI-assisted event analysis and territory update helpers for advanced ingestion workflows.

### How To Activate It

For the local Flask app:

```powershell
cd War-Tracker
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt Flask-Migrate Flask-Bcrypt Flask-Login
.\.venv\Scripts\python.exe app.py
```

Open:

```text
http://127.0.0.1:5000
```

For AI ingestion workflows, create an `APIs.env` file with the required keys and then run the relevant ingestion script, for example:

```powershell
.\.venv\Scripts\python.exe ingest_engine.py
```

### What Is Needed

- Python 3.
- SQLite database file `wartracker.db` for local use.
- Dependencies from `requirements.txt`.
- Additional Flask packages may be needed for the web app: `Flask-Migrate`, `Flask-Bcrypt`, and `Flask-Login`.
- Optional Redis if using Celery/rate-limited AI ingestion workflows.
- Optional Groq, Gemini, or Ollama credentials for AI analysis, configured through `APIs.env`.
- Optional Docker and Docker Compose if you want to adapt the included deployment files.

## 17. `Website_Maker`

### Overview

`Website_Maker` contains `my-website-builder`, a drag-and-drop website builder with a Next.js frontend and a Flask backend. It lets users assemble pages from visual blocks, customize project state, save versions, and publish generated sites through Flask.

### What It Does

- Provides a visual builder workspace with sidebar, canvas, topbar, and properties panel.
- Supports draggable blocks such as containers, text, images, and contact forms.
- Uses Zustand for builder state.
- Uses `@dnd-kit` and `react-rnd` for dragging, nesting, positioning, and resizing.
- Saves projects and versions through Flask API endpoints.
- Stores users, projects, and project versions in SQLite.
- Publishes saved projects under `/p/<project_id>`.
- Can run as a Next.js development app or as a static export served by Flask.

### How To Activate It

For frontend development:

```powershell
cd Website_Maker\my-website-builder
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

For the Flask-backed export/deployment flow:

```powershell
cd Website_Maker\my-website-builder
npm install
npm run build
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open:

```text
http://localhost:5000
```

### What Is Needed

- Node.js and npm.
- Python 3.
- Frontend dependencies from `package.json`.
- Flask backend dependencies from `requirements.txt`.
- SQLite, created automatically in `data/website_builder.db`.
- Optional environment variables such as `FLASK_PORT`, `FLASK_DEBUG`, `FRONTEND_DIR`, `PROJECT_DATA_DIR`, `DATABASE_PATH`, and `DEFAULT_USERNAME`.
