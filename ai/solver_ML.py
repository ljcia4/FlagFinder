import random
import sys
import os
import tkinter as tk
import warnings
import pandas as pd # Necessario per il modello
import joblib       # Necessario per caricare il modello

# Cache globale per il modello per evitare di ricaricarlo ad ogni istanza
_CACHED_MODEL = None
_MODEL_ATTEMPTED = False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.minesweeper import MinesweeperGUI

class MinesweeperAI:
    def __init__(self, game_logic):
        self.game = game_logic
        self.running = False
        
        # Colonne necessarie per ricostruire il DataFrame corretto per il modello
        self.dataset_columns = [f"cell_{r}_{c}" for r in range(-2, 3) for c in range(-2, 3) if not (r==0 and c==0)]
        
        # --- CARICAMENTO MODELLO ML ---
        global _CACHED_MODEL, _MODEL_ATTEMPTED
        
        # Percorso del modello
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minesweeper_ai_model_opt.pkl')
        
        # Tenta il caricamento solo se non è mai stato provato prima o se è None
        if not _MODEL_ATTEMPTED:
            _MODEL_ATTEMPTED = True
            if os.path.exists(model_path):
                try:
                    # Silenzia warnings (es. VersionMismatch)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        loaded_model = joblib.load(model_path)
                    
                    # Disabilita output verboso del modello
                    if hasattr(loaded_model, "verbose"):
                        loaded_model.verbose = 0
                    
                    _CACHED_MODEL = loaded_model
                    print("AI: Modello ML caricato. Modalità Probabilità Massima.")
                except Exception as e:
                    print(f"AI: Errore caricamento modello: {e}")
        
        self.model = _CACHED_MODEL

    def _get_effective_value(self, r, c):
        """Calcola il valore 'Smart' per il contesto."""
        if not (0 <= r < self.game.rows and 0 <= c < self.game.cols):
            return -2 # Muro

        cell = self.game.board[r][c]
        if not cell.is_revealed:
            return -1 # Incognita

        # Calcolo mine residue locali
        neighbors = self.game.get_neighbors(r, c)
        current_flags = len([n for n in neighbors if self.game.board[n[0]][n[1]].is_flagged])
        return cell.adjacent_mines - current_flags

    def _get_features_for_cell(self, r, c):
        """Estrae la riga di feature 5x5 per una singola cella."""
        features = []
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0: continue
                val = self._get_effective_value(r + dr, c + dc)
                features.append(val)
        return features

    def step(self):
        if self.game.game_over: return False
        made_move = False
        
        # 1. Logica Base (Hill Climbing)
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.game_over: return False
                cell = self.game.board[r][c]
                
                if cell.is_revealed and cell.adjacent_mines > 0:
                    neighbors = [self.game.board[nr][nc] for nr, nc in self.game.get_neighbors(r, c)]
                    hidden = [(n.r, n.c) for n in neighbors if not n.is_revealed and not n.is_flagged]
                    flags = len([n for n in neighbors if n.is_flagged])
                    
                    if not hidden: continue
                        
                    # Rule: Hidden == Value - Flags -> Tutte Mine
                    if len(hidden) == cell.adjacent_mines - flags:
                        for hr, hc in hidden:
                            self.game.toggle_flag(hr, hc)
                            made_move = True
                            
                    # Rule: Value == Flags -> Tutte Safe
                    elif cell.adjacent_mines == flags:
                        for hr, hc in hidden:
                            self.game.reveal(hr, hc)
                            made_move = True

        if made_move: return True

        # 2. Logica Avanzata (Insiemi)
        if self.run_advanced_logic(): return True

        # 3. Guessing (ML Probabilità Massima)
        self.make_guess_with_ml()
        return True

    def run_advanced_logic(self):
        """Risolve pattern complessi (es. 1-2-1) tramite differenza insiemi."""
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
                            self.game.toggle_flag(dr, dc)
                            made_move = True
        return made_move

    def make_guess_with_ml(self):
        """
        Usa il modello ML per trovare la cella con la probabilità più alta (best-first).
        """
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
        
        # --- LOGICA ML (PROBABILITÀ) ---
        if self.model:
            features_batch = []
            for r, c in frontier_list:
                features_batch.append(self._get_features_for_cell(r, c))
            
            X_input = pd.DataFrame(features_batch, columns=self.dataset_columns)
            
            try:
                # predict_proba restituisce array [[prob_0, prob_1], ...]
                probs = self.model.predict_proba(X_input)
                safe_probs = probs[:, 1] # Prendiamo solo la colonna "Safe" (Classe 1)
                
                # Trova l'indice della probabilità massima assoluta
                best_idx = safe_probs.argmax()
                best_prob = safe_probs[best_idx]
                
                best_move = frontier_list[best_idx]
                # print(f"AI: Scelgo ({best_move[0]}, {best_move[1]}) con confidenza: {best_prob:.2%}")
                
            except Exception as e:
                print(f"Errore ML: {e}")
                best_move = random.choice(frontier_list)
        
        else:
            best_move = random.choice(frontier_list)

        if best_move:
            self.game.reveal(best_move[0], best_move[1])

    def run_gui_loop(self, root, gui_update_callback):
        if not self.running:
            cr, cc = self.game.rows // 2, self.game.cols // 2
            self.game.reveal(cr, cc)
            self.running = True
            gui_update_callback()
        
        if self.game.game_over:
            return

        self.step()
        gui_update_callback()
        root.after(100, lambda: self.run_gui_loop(root, gui_update_callback))

if __name__ == "__main__":
    root = tk.Tk()
    app = MinesweeperGUI(root)
    ai = MinesweeperAI(app.game)
    root.after(100, lambda: ai.run_gui_loop(root, app.update_gui))
    root.mainloop()