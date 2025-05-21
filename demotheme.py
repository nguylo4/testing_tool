import tkinter as tk
import customtkinter as ctk

# Gradient background frame using canvas
class GradientFrame(tk.Canvas):
    def __init__(self, parent, color1, color2, **kwargs):
        super().__init__(parent, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        (r1, g1, b1) = self.winfo_rgb(self.color1)
        (r2, g2, b2) = self.winfo_rgb(self.color2)

        r_ratio = float(r2 - r1) / height
        g_ratio = float(g2 - g1) / height
        b_ratio = float(b2 - b1) / height

        for i in range(height):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = "#%04x%04x%04x" % (nr, ng, nb)
            self.create_line(0, i, width, i, tags=("gradient",), fill=color)

        self.lower("gradient")


# App structure
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("dark-blue")  # You can change to "green", "blue", etc.

root = ctk.CTk()
root.title("🌌 Galaxy Gradient UI")
root.geometry("700x500")
root.minsize(600, 400)

# Gradient background
gradient_bg = GradientFrame(root, "#654ea3", "#eaafc8")
gradient_bg.pack(fill="both", expand=True)

# Center frame
main_frame = ctk.CTkFrame(master=gradient_bg, fg_color="white", corner_radius=20)
main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.5)

# Title
title = ctk.CTkLabel(
    master=main_frame,
    text="🚀 Welcome to Galaxy UI",
    text_color="#333333",
    font=("Segoe UI", 22, "bold")
)
title.pack(pady=(20, 10))

# Subtitle
subtitle = ctk.CTkLabel(
    master=main_frame,
    text="Modern tkinter with gradient style",
    text_color="#666666",
    font=("Segoe UI", 14)
)
subtitle.pack(pady=(0, 20))

# Buttons
button1 = ctk.CTkButton(master=main_frame, text="Start", corner_radius=15, width=120, height=40)
button1.pack(pady=10)

button2 = ctk.CTkButton(master=main_frame, text="Settings", corner_radius=15, width=120, height=40, fg_color="#cccccc", text_color="black", hover_color="#aaaaaa")
button2.pack(pady=10)

# Run
root.mainloop()
