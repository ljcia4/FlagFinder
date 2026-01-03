import random
import sys
import os
import tkinter as tk
import pandas as pd 
import joblib
import csv 
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

_CACHED_BRAIN = None
_BRAIN_ATTEMPTED = False

CSV_FILE = 'minesweeper_dataset.csv'
BRAIN_FILE = 'minesweeper_brain_online.pkl'

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.minesweeper import MinesweeperGUI

class MinesweeperAI:
    def __init__(self, game_logic):
        self.game = game_logic
        self.running = False
        self.memory = []
        self.flags_count = 0 
        
        self.grid_features = [f"cell_{r}_{c}" for r in range(-2, 3) for c in range(-2, 3) if not (r==0 and c==0)]
        self.meta_features = ['global_density'] 
        self.dataset_columns = self.grid_features + self.meta_features
        
        global _CACHED_BRAIN, _BRAIN_ATTEMPTED
        
        if not _BRAIN_ATTEMPTED:
            _BRAIN_ATTEMPTED = True
            if os.path.exists(BRAIN_FILE):
                try:
                    _CACHED_BRAIN = joblib.load(BRAIN_FILE)
                except:
                    self._init_brain()
            else:
                self._init_brain()
                if os.path.exists(CSV_FILE):
                    self._full_pre_train()
        
        self.model = _CACHED_BRAIN

    def _init_brain(self):
        global _CACHED_BRAIN
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('mlp', MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                learning_rate='adaptive',
                random_state=42,
                warm_start=True,
                max_iter=200
            ))
        ])
        _CACHED_BRAIN = pipeline
        self.model = pipeline

    def _full_pre_train(self):
        try:
            df = pd.read_csv(CSV_FILE)
            X = df.iloc[:, :-1].values
            y = df.iloc[:, -1].values
            
            self.model.fit(X, y)
            joblib.dump(self.model, BRAIN_FILE)
        except:
            pass

    def _place_flag(self, r, c):
        if not self.game.board[r][c].is_flagged:
            self.game.toggle_flag(r, c)
            self.flags_count += 1

    def _get_effective_value(self, r, c):
        if not (0 <= r < self.game.rows and 0 <= c < self.game.cols): return -2
        cell = self.game.board[r][c]
        if not cell.is_revealed: return -1

        neighbors = self.game.get_neighbors(r, c)
        current_flags = len([n for n in neighbors if self.game.board[n[0]][n[1]].is_flagged])
        return cell.adjacent_mines - current_flags

    def _get_features_for_cell(self, r, c):
        features = []
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0: continue
                val = self._get_effective_value(r + dr, c + dc)
                features.append(val)
        
        mines_left = self.game.mines - self.flags_count
        revealed_count = sum(cell.is_revealed for row in self.game.board for cell in row)
        total_cells = self.game.rows * self.game.cols
        hidden_cells = total_cells - revealed_count
        
        density = (mines_left / hidden_cells) if hidden_cells > 0 else 0.0
        features.append(density)
        return features

    def _save_dataset(self, features, label):
        try:
            file_exists = os.path.isfile(CSV_FILE)
            with open(CSV_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(self.dataset_columns + ['safe'])
                writer.writerow(features + [label])
        except:
            pass

    def learn_online(self):
        if not self.memory: return

        X = np.array([m[0] for m in self.memory])
        y = np.array([m[1] for m in self.memory])
        
        try:
            scaler = self.model.named_steps['scaler']
            mlp = self.model.named_steps['mlp']
            
            scaler.partial_fit(X)
            X_scaled = scaler.transform(X)
            mlp.partial_fit(X_scaled, y, classes=[0, 1])
            
            joblib.dump(self.model, BRAIN_FILE)
        except:
            pass
        
        self.memory = []

    def step(self):
        if self.game.game_over:
            if self.memory: self.learn_online()
            return False
            
        revealed_count = sum(c.is_revealed for row in self.game.board for c in row)
        if revealed_count == (self.game.rows * self.game.cols) - self.game.mines:
            if self.memory: self.learn_online()
            return False

        made_move = False
        
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.game_over: return False
                cell = self.game.board[r][c]
                
                if cell.is_revealed and cell.adjacent_mines > 0:
                    neighbors = [self.game.board[nr][nc] for nr, nc in self.game.get_neighbors(r, c)]
                    hidden = [(n.r, n.c) for n in neighbors if not n.is_revealed and not n.is_flagged]
                    flags = len([n for n in neighbors if n.is_flagged])
                    
                    if not hidden: continue
                        
                    if len(hidden) == cell.adjacent_mines - flags:
                        for hr, hc in hidden:
                            self._place_flag(hr, hc)
                            made_move = True
                            
                    elif cell.adjacent_mines == flags:
                        for hr, hc in hidden:
                            self.game.reveal(hr, hc)
                            made_move = True

        if made_move: return True

        if self.run_advanced_logic(): return True

        self.make_guess_with_ml()
        return True

    def run_advanced_logic(self):
        active_cells = []
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                cell = self.game.board[r][c]
                if cell.is_revealed and cell.adjacent_mines > 0:
                     neighbors = self.game.get_neighbors(r, c)
                     hidden = [(nr, nc) for nr, nc in neighbors 
                               if not self.game.board[nr][nc].is_revealed 
                               and not self.game.board[nr][nc].is_flagged]
                     if hidden:
                         flags = len([n for n in neighbors if self.game.board[n[0]][n[1]].is_flagged])
                         active_cells.append({
                             'hidden': set(hidden),
                             'remaining': cell.adjacent_mines - flags
                         })
        
        made_move = False
        for i in range(len(active_cells)):
            for j in range(len(active_cells)):
                if i == j: continue
                A, B = active_cells[i], active_cells[j]
                
                if A['hidden'].issubset(B['hidden']):
                    diff = B['hidden'] - A['hidden']
                    if not diff: continue
                    mine_diff = B['remaining'] - A['remaining']
                    
                    if mine_diff == 0:
                        for dr, dc in diff:
                            self.game.reveal(dr, dc)
                            made_move = True
                    elif mine_diff == len(diff):
                        for dr, dc in diff:
                            self._place_flag(dr, dc)
                            made_move = True
        return made_move

    def make_guess_with_ml(self):
        frontier = set()
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.board[r][c].is_revealed:
                    for nr, nc in self.game.get_neighbors(r, c):
                        if not self.game.board[nr][nc].is_revealed and not self.game.board[nr][nc].is_flagged:
                            frontier.add((nr, nc))
        
        frontier_list = list(frontier)
        
        if not frontier_list:
            hidden = []
            for r in range(self.game.rows):
                for c in range(self.game.cols):
                    if not self.game.board[r][c].is_revealed and not self.game.board[r][c].is_flagged:
                        hidden.append((r, c))
            if not hidden: return
            frontier_list = hidden

        best_move = None
        
        is_fitted = False
        if hasattr(self.model, 'named_steps'):
            if hasattr(self.model.named_steps['mlp'], 'coefs_'):
                is_fitted = True
        
        if is_fitted:
            features_batch = []
            for r, c in frontier_list:
                features_batch.append(self._get_features_for_cell(r, c))
            
            try:
                probs = self.model.predict_proba(features_batch)
                safe_probs = probs[:, 1]
                best_idx = safe_probs.argmax()
                best_move = frontier_list[best_idx]
            except:
                best_move = random.choice(frontier_list)
        else:
            best_move = random.choice(frontier_list)

        if best_move:
            move_features = self._get_features_for_cell(best_move[0], best_move[1])
            self.game.reveal(best_move[0], best_move[1])
            
            label = 1 
            if self.game.game_over and not self.game.victory:
                label = 0 
            
            self.memory.append((move_features, label))
            self._save_dataset(move_features, label)

    def run_gui_loop(self, root, gui_update_callback):
        if not self.running:
            cr, cc = self.game.rows // 2, self.game.cols // 2
            self.game.reveal(cr, cc)
            self.running = True
            gui_update_callback()
        
        if self.game.game_over:
            if self.memory: self.learn_online()
            return

        self.step()
        gui_update_callback()
        root.after(100, lambda: self.run_gui_loop(root, gui_update_callback))

if __name__ == "__main__":
    root = tk.Tk()
    app = MinesweeperGUI(root, 16, 30, 99)
    ai = MinesweeperAI(app.game)
    root.after(100, lambda: ai.run_gui_loop(root, app.update_gui))
    root.mainloop()