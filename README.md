# Mika Desktop Companion

## V2
Mika is a Windows desktop companion with a gamer/anime-inspired personality.

### Included
- Dark V2 interface
- Mood/expression changes
- Persistent sessions, messages, timers and notes
- `souviens-toi ...` memory command
- Minecraft / Valorant / Modrinth reactions
- Custom timers
- Stats panel
- Notepad launcher
- Idle reactions
- No external Python packages required

## Run

### Version normale
1. Lance `Mika.exe` si tu as téléchargé le build Windows.
2. **Aucun Python n'est nécessaire** pour cette version.

### Pour les développeurs
Python reste nécessaire uniquement si tu veux modifier `companion.py`.

## V3

- 🤖 **Vraie IA** via l'API OpenAI avec `MIKA_OPENAI_API_KEY`
- 🔊 **Voix féminine Windows** si une voix féminine est installée
- 🌸 **Personnage anime animé** dans l'interface
- 🎮 Détection locale de Minecraft, VALORANT, Modrinth, Steam et Discord
- 🔔 Notifications Windows
- 👀 Réactions automatiques aux applications ouvertes

## Build Windows sans Python

Le dépôt contient un workflow GitHub Actions qui fabrique automatiquement `Mika.exe` avec PyInstaller.

Dans **Actions → Build Mika for Windows → Run workflow**, puis télécharge l'artifact **Mika-Windows**.


V3 can add real AI chat, female TTS voice, animated character art, app/process detection, notifications and richer desktop behavior.
