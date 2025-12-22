import tkinter as tk
from tkinter import messagebox
import random
import os

class Minesweeper:
    def __init__(self, master, rows=9, cols=9, mines=10):
        self.master = master
        self.master.title("Minesweeper")
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.buttons = {}
        self.mine_positions = set()
        self.game_over = False
        self.flags = 0
        self.revealed_cells = 0

        try:
            base_path = os.path.dirname(__file__)
            self.bomb_image = tk.PhotoImage(file=os.path.join(base_path, "images", "bomb.png")).subsample(45, 45)
            self.flag_image = tk.PhotoImage(file=os.path.join(base_path, "images", "flag.png")).subsample(35, 35)
        except Exception as e:
            print(f"Error loading images: {e}")
            self.bomb_image = None
            self.flag_image = None
            
        self.pixel_virtual = tk.PhotoImage(width=1, height=1)

        self.create_widgets()
        self.place_mines()
        self.calculate_numbers()
        
        self.center_window()

    def create_widgets(self):
        self.top_frame = tk.Frame(self.master)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(self.top_frame, text=f"Mines: {self.mines}")
        self.status_label.pack(side=tk.LEFT)
        
        self.restart_button = tk.Button(self.top_frame, text="Restart", command=self.restart_game)
        self.restart_button.pack(side=tk.RIGHT)

        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.pack(padx=10, pady=10)

        for r in range(self.rows):
            for c in range(self.cols):
                frame = tk.Frame(self.grid_frame, width=30, height=30)
                frame.pack_propagate(False)
                frame.grid(row=r, column=c)

                btn = tk.Button(
                    frame, 
                    width=30, 
                    height=30, 
                    image=self.pixel_virtual,
                    compound='c',
                    font=('Arial', 12, 'bold'),
                    bg="#dddddd"
                )
                btn.pack(fill=tk.BOTH, expand=True)
                btn.bind('<Button-1>', lambda event, r=r, c=c: self.on_left_click(r, c))
                btn.bind('<Button-2>', lambda event, r=r, c=c: self.on_right_click(r, c)) # For Mac (sometimes)
                btn.bind('<Button-3>', lambda event, r=r, c=c: self.on_right_click(r, c)) # For Windows/Linux
                self.buttons[(r, c)] = {
                    'btn': btn, 
                    'mine': False, 
                    'value': 0, 
                    'state': 'hidden' # hidden, revealed, flagged
                }

    def place_mines(self):
        while len(self.mine_positions) < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) not in self.mine_positions:
                self.mine_positions.add((r, c))
                self.buttons[(r, c)]['mine'] = True

    def calculate_numbers(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.buttons[(r, c)]['mine']:
                    count = 0
                    for i in range(max(0, r-1), min(self.rows, r+2)):
                        for j in range(max(0, c-1), min(self.cols, c+2)):
                            if (i, j) in self.mine_positions:
                                count += 1
                    self.buttons[(r, c)]['value'] = count

    def on_left_click(self, r, c):
        if self.game_over:
            return
        
        cell = self.buttons[(r, c)]
        if cell['state'] == 'flagged' or cell['state'] == 'revealed':
            return

        if cell['mine']:
            self.game_over_loss()
        else:
            self.reveal_cell(r, c)
            if self.revealed_cells == (self.rows * self.cols) - self.mines:
                self.game_over_win()

    def on_right_click(self, r, c):
        if self.game_over:
            return

        cell = self.buttons[(r, c)]
        btn = cell['btn']

        if cell['state'] == 'hidden':
            cell['state'] = 'flagged'
            if self.flag_image:
                btn.config(image=self.flag_image, width=30, height=30) # Adjust size match
            else:
                btn.config(text='🚩', fg='red', image=self.pixel_virtual, width=30, height=30)
            self.flags += 1
        elif cell['state'] == 'flagged':
            cell['state'] = 'hidden'
            btn.config(image=self.pixel_virtual, width=30, height=30) # Reset to text mode dimensions
            btn.config(text='')
            self.flags -= 1
        
        self.status_label.config(text=f"Mines: {self.mines - self.flags}")

    def reveal_cell(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        
        cell = self.buttons[(r, c)]
        if cell['state'] != 'hidden':
            return
        
        cell['state'] = 'revealed'
        self.revealed_cells += 1
        btn = cell['btn']
        btn.config(relief=tk.SUNKEN, bg="#b0b0b0")

        val = cell['value']
        if val > 0:
            colors = {1: 'blue', 2: 'green', 3: 'red', 4: 'darkblue', 5: 'darkred', 6: 'teal', 7: 'black', 8: 'gray'}
            btn.config(text=str(val), fg=colors.get(val, 'black'))
        else:
            # Recursive reveal for empty cells
            for i in range(max(0, r-1), min(self.rows, r+2)):
                for j in range(max(0, c-1), min(self.cols, c+2)):
                    if i != r or j != c:
                        self.reveal_cell(i, j)

    def game_over_loss(self):
        self.game_over = True
        for (r, c) in self.mine_positions:
            btn = self.buttons[(r, c)]['btn']
            if self.bomb_image:
                btn.config(image=self.bomb_image, width=30, height=30, bg='red')
            else:
                btn.config(text='💣', bg='red', image=self.pixel_virtual, width=30, height=30)
        messagebox.showinfo("Game Over", "BOOM! You hit a mine.")

    def game_over_win(self):
        self.game_over = True
        messagebox.showinfo("Congratulations", "You won!")

    def restart_game(self):
        self.master.destroy()
        root = tk.Tk()
        Minesweeper(root, self.rows, self.cols, self.mines)
        root.mainloop()

    def center_window(self):
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()
