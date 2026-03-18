# 🎮 Upside Down: Tactical Escape

A real-time tactical AI game built using **Python** and **Pygame**, inspired by the *Stranger Things* universe.
Control Eleven as she attempts to escape a maze filled with Demogorgons using intelligent decision-making algorithms.

---

## 🚀 Features

* 🧠 **MCTS (Monte Carlo Tree Search)** for Eleven's movement
* 🤖 **Minimax Algorithm** for Demogorgon AI behavior
* 🧱 Dynamic **maze environment** with walls and exits
* ⚔️ **Combat system** with directional mechanics (backstab vs frontal attack)
* 🌫️ **Detection system** with enemy radius visualization
* 🎨 Procedurally generated sprites (no external assets required)
* 🕹️ Fully automated gameplay (AI vs AI)

---

## 🧠 AI System Overview

### 🔵 Eleven (Player AI)

* Uses **Monte Carlo Tree Search (MCTS)**
* Simulates multiple future states to choose safest path
* Prioritizes:

  * Distance from enemies
  * Shortest path to exit
  * Survival probability

---

### 🔴 Demogorgons (Enemy AI)

* Uses **Minimax Algorithm**
* Behavior:

  * **Chase mode** (when player detected)
  * **Patrol mode** (when player not detected)
* Objective:

  * Block Eleven’s path to exits
  * Minimize escape chances

---

## 🗺️ Game Mechanics

### 🎯 Objective

* Escape through one of the maze exits
  **OR**
* Defeat all Demogorgons

---

### ❤️ Health System

* Eleven's health = `(Number of Demogorgons × 3) - 1`
* Each Demogorgon has **3 lives**

---

### ⚔️ Combat Rules

* **Backstab (from behind):**

  * Damages Demogorgon
* **Frontal attack:**

  * Damages Eleven
* Includes knockback effects

---

### 👁️ Detection System

* Demogorgons detect Eleven within a certain radius
* Visual "scent" effect shows detection area

---

## 🧱 Project Structure (Recommended)

```
upsidedownchase/
│
├── main.py
├── game.py
├── entities.py
├── maze.py
├── ai/
│   ├── mcts.py
│   └── minimax.py
├── assets/ (optional)
├── README.md
└── .gitignore
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/TheWorthless11/upside-down-chase.git
cd upside-down-chase
```

---

### 2️⃣ Install dependencies

```bash
pip install pygame
```

---

### 3️⃣ Run the game

```bash
python main.py
```

---

## 🎮 Controls

| Key | Action                    |
| --- | ------------------------- |
| ESC | Quit game                 |
| R   | Restart (after game over) |
| Q   | Quit (after game over)    |

---

## ⚙️ Configuration

You can tweak gameplay via constants in the code:

* `GRID_SIZE` → Maze size
* `FPS` → Game speed
* `mcts_simulations` → AI strength/performance
* `detection_radius` → Enemy awareness

---

## 📈 Future Improvements

* 🎯 Difficulty levels (easy / medium / hard)
* 🧠 Improved MCTS optimization
* 🌐 Multiplayer / manual control mode
* 🎨 Enhanced UI and animations
* 📊 Performance optimization for large simulations
* 💾 Save/load game states

---

## 🧑‍💻 Author

**Mahhia**
CSE Undergraduate Student

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

## 🌟 Acknowledgements

* Inspired by *Stranger Things*
* Built with ❤️ using Python & Pygame

---

## ⭐ Support

If you like this project:

* Give it a ⭐ on GitHub
* Share it with others

---
