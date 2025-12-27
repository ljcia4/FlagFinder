import tkinter as tk
from tkinter import messagebox
import os
from game_logic import MinesweeperLogic

class MinesweeperGUI:
    def __init__(self, master, rows=16, cols=16, mines=40):
        self.master = master
        self.master.title("Minesweeper")
        
        # Inizializza la logica
        self.game = MinesweeperLogic(rows, cols, mines)
        self.buttons = {}
        
        self.load_assets()
        self.create_widgets()
        self.center_window()

    def load_assets(self):
        try:
            base_path = os.path.dirname(__file__)
            self.bomb_image = tk.PhotoImage(file=os.path.join(base_path, "images", "bomb.png")).subsample(45, 45)
            self.flag_image = tk.PhotoImage(file=os.path.join(base_path, "images", "flag.png")).subsample(35, 35)
        except Exception:
            self.bomb_image = None
            self.flag_image = None
        self.pixel_virtual = tk.PhotoImage(width=1, height=1)

    def create_widgets(self):
        self.top_frame = tk.Frame(self.master)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(self.top_frame, text=f"Mines: {self.game.mines}")
        self.status_label.pack(side=tk.LEFT)
        
        self.restart_button = tk.Button(self.top_frame, text="Restart", command=self.restart_game)
        self.restart_button.pack(side=tk.RIGHT)

        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.pack(padx=10, pady=10)

        for r in range(self.game.rows):
            for c in range(self.game.cols):
                frame = tk.Frame(self.grid_frame, width=30, height=30)
                frame.pack_propagate(False)
                frame.grid(row=r, column=c)

                btn = tk.Button(
                    frame, width=30, height=30, image=self.pixel_virtual,
                    compound='c', font=('Arial', 12, 'bold'), bg="#dddddd"
                )
                btn.pack(fill=tk.BOTH, expand=True)
                # Binding agli eventi
                btn.bind('<Button-1>', lambda e, r=r, c=c: self.on_left_click(r, c))
                btn.bind('<Button-2>', lambda e, r=r, c=c: self.on_right_click(r, c))
                btn.bind('<Button-3>', lambda e, r=r, c=c: self.on_right_click(r, c))
                
                self.buttons[(r, c)] = btn

    def on_left_click(self, r, c):
        if self.game.game_over: return
        
        changed = self.game.reveal(r, c)
        if changed:
            self.update_gui()
            self.check_game_over()

    def on_right_click(self, r, c):
        if self.game.game_over: return
        
        self.game.toggle_flag(r, c)
        self.update_gui()

    def update_gui(self):
        """Sincronizza la griglia grafica con lo stato logico."""
        self.status_label.config(text=f"Mines: {self.game.mines - self.game.flag_count}")
        
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                cell = self.game.board[r][c]
                btn = self.buttons[(r, c)]
                
                if cell.is_revealed:
                    btn.config(relief=tk.SUNKEN, bg="#b0b0b0", image=self.pixel_virtual)
                    if cell.is_mine:
                        if self.bomb_image:
                            btn.config(image=self.bomb_image, bg='red')
                        else:
                            btn.config(text='💣', bg='red')
                    elif cell.adjacent_mines > 0:
                        colors = {1: 'blue', 2: 'green', 3: 'red', 4: 'darkblue', 
                                  5: 'darkred', 6: 'teal', 7: 'black', 8: 'gray'}
                        btn.config(text=str(cell.adjacent_mines), 
                                   fg=colors.get(cell.adjacent_mines, 'black'))
                    else:
                        btn.config(text='')
                elif cell.is_flagged:
                    if self.flag_image:
                        btn.config(image=self.flag_image)
                    else:
                        btn.config(text='🚩', fg='red')
                else:
                    # Stato hidden normale
                    btn.config(text='', image=self.pixel_virtual, bg="#dddddd", relief=tk.RAISED)

    def check_game_over(self):
        if self.game.game_over:
            # Rivela tutte le mine
            for (mr, mc) in self.game.mine_positions:
                cell = self.game.board[mr][mc]
                if not cell.is_revealed and not cell.is_flagged:
                    # Mostra bomba
                    btn = self.buttons[(mr, mc)]
                    if self.bomb_image:
                        btn.config(image=self.bomb_image, bg="#ffcccc")
                    else:
                        btn.config(text='💣', bg="#ffcccc")
            
            if self.game.victory:
                messagebox.showinfo("Victory", "Congratulations! You won!")
            else:
                messagebox.showinfo("Game Over", "BOOM! You hit a mine.")

    def restart_game(self):
        self.master.destroy()
        root = tk.Tk()
        MinesweeperGUI(root, self.game.rows, self.game.cols, self.game.mines)
        root.mainloop()

    def center_window(self):
        self.master.update_idletasks()
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (w // 2)
        y = (self.master.winfo_screenheight() // 2) - (h // 2)
        self.master.geometry(f'+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    app = MinesweeperGUI(root)
    root.mainloop()