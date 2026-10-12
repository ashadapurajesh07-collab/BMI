import tkinter as tk
from tkinter import messagebox
import sqlite3
import datetime
import matplotlib.pyplot as plt

DB_NAME = "bmi_tracker.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not set up database: {e}")

class BMICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced BMI Calculator & Tracker")
        self.root.geometry("400x460")
        self.root.resizable(False, False)

        # UI Layout
        tk.Label(root, text="User Name:").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.entry_name = tk.Entry(root, width=25)
        self.entry_name.grid(row=0, column=1, padx=15, pady=10)

        tk.Label(root, text="Weight (kg):").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.entry_weight = tk.Entry(root, width=25)
        self.entry_weight.grid(row=1, column=1, padx=15, pady=10)

        tk.Label(root, text="Height (feet):").grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.entry_feet = tk.Entry(root, width=25)
        self.entry_feet.grid(row=2, column=1, padx=15, pady=10)

        tk.Label(root, text="Height (inches/cm):").grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.entry_inches = tk.Entry(root, width=25)
        self.entry_inches.grid(row=3, column=1, padx=15, pady=10)

        # Main Action Button
        self.btn_calc = tk.Button(root, text="Calculate & Save", command=self.calculate_and_save, bg="#e1e1e1", width=20)
        self.btn_calc.grid(row=4, column=0, columnspan=2, pady=10)

        # Result Banner
        self.lbl_result = tk.Label(root, text="", font=("Arial", 11, "bold"))
        self.lbl_result.grid(row=5, column=0, columnspan=2, pady=10)

        # Analytics & Management Buttons
        self.btn_graph = tk.Button(root, text="View BMI Trend Chart", command=self.plot_trend, bg="#e1e1e1", width=20)
        self.btn_graph.grid(row=6, column=0, columnspan=2, pady=5)

        self.btn_clear = tk.Button(root, text="Clear User History", command=self.clear_history, bg="#ffcdd2", fg="#c62828", width=20)
        self.btn_clear.grid(row=7, column=0, columnspan=2, pady=5)

    def calculate_and_save(self):
        username = self.entry_name.get().strip()
        
        if not username:
            messagebox.showwarning("Input Error", "Please enter a user name.")
            return

        try:
            weight = float(self.entry_weight.get())
            if weight <= 0:
                raise ValueError

            feet_val = self.entry_feet.get().strip()
            inches_val = self.entry_inches.get().strip()

            feet = float(feet_val) if feet_val else 0.0
            inches = float(inches_val) if inches_val else 0.0

            if feet <= 0 and inches <= 0:
                messagebox.showerror("Input Error", "Please enter height in feet, inches, or centimeters.")
                return

            # Smart Height Conversion:
            # If user enters value > 100 in inches field without feet, treat it as Centimeters (e.g., 180 cm)
            if feet == 0 and inches > 100:
                height_m = inches / 100.0
            else:
                total_inches = (feet * 12) + inches
                height_m = total_inches * 0.0254

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for weight and height.")
            return

        bmi = weight / (height_m ** 2)
        category, color = self.get_category_and_color(bmi)

        # Display result
        self.lbl_result.config(text=f"BMI: {bmi:.2f} ({category})", fg=color)

        # Save to SQLite Database
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute('''
                INSERT INTO bmi_records (username, weight, height, bmi, category, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, weight, round(height_m, 2), round(bmi, 2), category, now))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save record: {e}")
            return

        # Clear input fields
        self.entry_weight.delete(0, tk.END)
        self.entry_feet.delete(0, tk.END)
        self.entry_inches.delete(0, tk.END)

    def get_category_and_color(self, bmi):
        if bmi < 18.5:
            return "Underweight", "#1e88e5"
        elif 18.5 <= bmi <= 24.9:
            return "Normal", "#2e7d32"
        elif 25.0 <= bmi <= 29.9:
            return "Overweight", "#f57c00"
        else:
            return "Obese", "#c62828"

    def plot_trend(self):
        username = self.entry_name.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Enter a user name to view history chart.")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, bmi FROM bmi_records 
                WHERE username = ? ORDER BY id ASC
            ''', (username,))
            records = cursor.fetchall()
            conn.close()

            if not records:
                messagebox.showinfo("No Records", f"No saved history found for '{username}'.")
                return

            dates = [r[0] for r in records]
            bmis = [r[1] for r in records]

            plt.figure(figsize=(7, 4))
            plt.plot(dates, bmis, marker='o', linestyle='-', color='#1f77b4', linewidth=2)
            plt.title(f"BMI History for {username}")
            plt.xlabel("Date & Time")
            plt.ylabel("BMI Value")
            plt.xticks(rotation=30, ha='right')
            plt.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()
            plt.show()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch data: {e}")

    def clear_history(self):
        username = self.entry_name.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Enter a user name to clear history.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete all records for '{username}'?")
        if confirm:
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM bmi_records WHERE username = ?', (username,))
                conn.commit()
                conn.close()
                self.lbl_result.config(text="History cleared!", fg="black")
                messagebox.showinfo("Success", f"All records for '{username}' have been deleted.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to delete records: {e}")

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()