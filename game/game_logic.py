import random

class Cell:
    def __init__(self, r, c):
        self.r = r
        self.c = c
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

class MinesweeperLogic:
    def __init__(self, rows=30, cols=30, mines=150):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.board = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
        self.mine_positions = set()
        self.game_over = False
        self.victory = False
        self.first_click = True
        self.revealed_count = 0
        self.flag_count = 0

    def get_cell(self, r, c):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.board[r][c]
        return None

    def get_neighbors(self, r, c):
        neighbors = []
        for i in range(max(0, r - 1), min(self.rows, r + 2)):
            for j in range(max(0, c - 1), min(self.cols, c + 2)):
                if i != r or j != c:
                    neighbors.append((i, j))
        return neighbors

    def place_mines(self, safe_r, safe_c):
        """Piazza le mine garantendo che safe_r, safe_c e vicini siano liberi."""
        safe_cells = set()
        for r in range(max(0, safe_r - 1), min(self.rows, safe_r + 2)):
            for c in range(max(0, safe_c - 1), min(self.cols, safe_c + 2)):
                safe_cells.add((r, c))

        # Evita loop infinito se troppe mine
        available_spots = (self.rows * self.cols) - len(safe_cells)
        if self.mines > available_spots:
            safe_cells = {(safe_r, safe_c)}

        while len(self.mine_positions) < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) not in safe_cells and (r, c) not in self.mine_positions:
                self.mine_positions.add((r, c))
                self.board[r][c].is_mine = True

        # Calcola i numeri per le celle adiacenti
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].is_mine:
                    count = 0
                    for nr, nc in self.get_neighbors(r, c):
                        if (nr, nc) in self.mine_positions:
                            count += 1
                    self.board[r][c].adjacent_mines = count

    def reveal(self, r, c):
        """Ritorna True se la mossa è valida (o ha causato game over), False se ignorata."""
        cell = self.get_cell(r, c)
        if not cell or self.game_over or cell.is_revealed or cell.is_flagged:
            return False

        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False

        cell.is_revealed = True
        self.revealed_count += 1

        if cell.is_mine:
            self.game_over = True
            self.victory = False
            return True

        if self.revealed_count == (self.rows * self.cols) - self.mines:
            self.game_over = True
            self.victory = True
            return True

        if cell.adjacent_mines == 0:
            # Flood fill automatico per gli zeri
            for nr, nc in self.get_neighbors(r, c):
                self.reveal(nr, nc)
        
        return True

    def toggle_flag(self, r, c):
        cell = self.get_cell(r, c)
        if not cell or self.game_over or cell.is_revealed:
            return
        
        cell.is_flagged = not cell.is_flagged
        self.flag_count += (1 if cell.is_flagged else -1)