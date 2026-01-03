# FlagFinder - Advanced Minesweeper with AI

**FlagFinder** is a project developed for the **Artificial Intelligence Fundamentals** course.

The main objective is the implementation and comparison of various intelligent agents (solvers) capable of solving the **Minesweeper** game. The project explores deterministic approaches (Constraint Satisfaction) and probabilistic/statistical ones (Machine Learning and Neural Networks), analyzing their performance in terms of win-rate and efficiency.

## 🎮 Features

- **Classic Gameplay**: Familiar Minesweeper rules with left-click to reveal and right-click to flag.
- **Graphical Interface**: Built with `tkinter`, offering a responsive and clean UI.
- **Customizable Grid**: Supports standard and custom board sizes.
- **Smart First Move**: Guarantees the first click is always safe.
- **Auto-Expansion**: Automatically reveals safe areas ("0" value cells).
- **AI Integration**: Includes multiple AI solvers:
  - **Logic Solver**: Uses constraint satisfaction to solve deterministic boards.
  - **ML Solver**: Machine Learning powered agent that learns from gameplay (using Scikit-learn).
  - **MLP Solver**: Neural network-based solver.

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ljcia4/FlagFinder.git
   cd FlagFinder
   ```

2. **(Optional) Create a virtual environment**:
   It is recommended to use a virtual environment to manage dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   Ensure you have Python 3.8+ installed.
   ```bash
   pip install -r requirements.txt
   ```

## 🕹️ How to Play

### Manual Play
Run the game using the module flag to ensure imports work correctly:

```bash
python -m game.minesweeper
```

**Controls**:
- **Left Click**: Reveal a cell.
- **Right Click**: Toggle a flag marker.

### Running AI Solvers
You can watch the AI tackle the game by running the solver scripts in the `ai/` directory.

**Machine Learning Solver**:
```bash
python -m ai.solver_ML
```

## 📂 Project Structure

- `game/`: Core game implementation.
  - `minesweeper.py`: Main GUI application entry point.
  - `game_logic.py`: Game rules and board state management.
  - `images/`: Graphics assets (bombs, flags).
- `ai/`: Artificial Intelligence agents.
  - `solver.py`: Deterministic logic-based solver.
  - `solver_ML.py`: Machine Learning agent.
  - `solver_MLP.py`: Multi-Layer Perceptron agent.
- `solver_benchmark.ipynb` & `training.ipynb`: Jupyter notebooks for training models and benchmarking AI performance.

## 👥 Team
This project was developed by:
* [Michele Chierchia](https://github.com/MicheleChierchia)
* [Felicia Riccio](https://github.com/ljcia4)
* [Gloria Scarallo](https://github.com/gloriascarallo)

---
This repository contains the complete implementation for the *Artificial Intelligence Fundamentals* academic project.