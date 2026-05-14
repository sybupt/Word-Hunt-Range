# VocaBee - Interactive English Vocabulary Learning Game

[![Godot Version](https://img.shields.io/badge/Godot-4.6+-blue.svg)](https://godotengine.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README_EG.md) | [中文](README.md)

VocaBee is an engaging, gamified English vocabulary learning platform built with Godot 4.6. Designed for English learners at various proficiency levels, it offers multiple interactive game modes to make vocabulary acquisition both effective and enjoyable.

## 🎯 Features

### Game Modes
- **Listen and Pick**: Audio-based vocabulary recognition with visual word cards
- **Scene Game Mode**: Real-world scene exploration with interactive object identification

### Learning Content
- **Vocabulary Sets**: CET-4, CET-6, TEM-4, TEM-8, College Entrance Examination, Senior High School Entrance Examination
- **Scene Environments**: Bedroom, classroom, hospital, restaurant, supermarket
- **Bilingual Support**: English words with Chinese translations and phonetic spelling

### Gameplay Mechanics
- **Scoring System**: Earn points for correct answers
- **Health/Timer Modes**: Choose between lives-based or time-limited gameplay
- **Dynamic Card Layout**: Intelligent positioning prevents overlaps and ensures fair gameplay
- **Text-to-Speech**: Audio pronunciation for vocabulary words (system-dependent)

## 🚀 Quick Start

### Prerequisites
- **Godot Engine 4.6 or later** - Download from [godotengine.org](https://godotengine.org/download)
- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url> VocaBee
   cd VocaBee
   ```

2. **Open in Godot**:
   - Launch Godot Engine
   - Click "Import" → Select `project.godot` from the VocaBee folder
   - Wait for asset import to complete (may take 1-2 minutes on first open)

3. **Run the game**:
   - Press `F5` or click the "Play" button in Godot
   - The game will start at the main menu

### Standalone Distribution

To create an executable for distribution:

1. Open the project in Godot
2. Go to **Project → Export**
3. Click **Add...** and select your target platform (Windows, macOS, Linux)
4. Configure export settings as needed
5. Click **Export Project** and choose a save location
6. The executable will be created in the specified location

## 📁 Project Structure

```
VocaBee/
├── project.godot              # Godot project configuration
├── icon.svg                   # Game icon
├── assets/
│   └── scene_imgs/            # Scene background images
├── data/
│   ├── *.json                 # Vocabulary datasets
│   └── scene_data/
│       └── *.json             # Scene annotation data
├── scenes/                    # Godot scene files (.tscn)
│   ├── autoload/              # Global scene managers
│   ├── common/                # Reusable UI components
│   ├── menu/                  # Menu scenes
│   └── mods/                  # Game mode scenes
├── scripts/                   # GDScript source files
│   ├── autoload/              # Global scripts
│   ├── common/                # Shared components
│   ├── menu/                  # Menu logic
│   └── mods/                  # Game mode logic
├── tool/
│   └── annotate.py            # Scene annotation tool
└── doc/                       # Project documentation
```

## 🎮 How to Play

### Main Scene
- The main scene is `main_menu.tscn`, which serves as the game's entry point.

1. **Main Menu**: Select your preferred game mode
2. **Mode Selection**: Choose between Listen and Pick or Scene Game Mode
3. **Vocabulary Selection**: Pick from available word sets
4. **Gameplay**:
   - **Listen and Pick**: Listen to pronunciation, select correct word card
   - **Scene Game Mode**: Click on highlighted objects in scenes to identify words
5. **Scoring**: Earn points for correct answers, lose health/time for mistakes

### Notes
- Login and Register buttons: These buttons are designed to lead to game mode selection, but they are not yet implemented.
- Exit button: The exit game functionality is not yet implemented.
- Settings button: The game settings functionality is not yet implemented.

## 🛠️ Development

### Requirements
- Godot 4.6+
- Python 3.x (for annotation tool)

### Building from Source
1. Ensure Godot 4.6+ is installed
2. Clone the repository
3. Open `project.godot` in Godot
4. Make your changes
5. Test thoroughly before committing

### Adding New Content

#### Vocabulary Sets
Add new JSON files to `data/` following this format:
```json
{
  "1": {
    "english": "word",
    "chinese_trans": "translation",
    "spell": "/phonetic/"
  }
}
```

#### Scene Data
Use `tool/annotate.py` to create scene annotations:
```bash
python tool/annotate.py --image path/to/image.png --output data/scene_data/new_scene.json
```

## 🔧 Troubleshooting

### Common Issues

**"JSON file not found" error**
- Ensure all files in `data/` directory are present
- Check file paths in scripts match actual locations

**Images not loading**
- Verify `assets/scene_imgs/` contains all required PNG files
- Check import settings in Godot

**Text-to-Speech not working**
- TTS depends on system capabilities
- Game remains fully playable without audio

**Cards overlapping or off-screen**
- Layout algorithm handles positioning automatically
- Check boundary settings in `LayoutSolver2D.gd`

**Scene transitions failing**
- Verify all scene files (.tscn) exist in `scenes/` directory
- Check scene paths in transition scripts

### Performance Tips
- Close other applications during gameplay
- Ensure adequate RAM (2GB+ recommended)
- Update graphics drivers for best performance

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines
- Follow Godot GDScript style guidelines
- Test changes thoroughly across different platforms
- Update documentation for new features
- Ensure compatibility with Godot 4.6+

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Godot Engine](https://godotengine.org/)
- Vocabulary data sourced from standard English proficiency examinations
- Scene images from educational resources

---

**Happy Learning!** 🐝📚