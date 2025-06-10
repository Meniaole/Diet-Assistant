import json
import os
import tkinter as tk
from tkinter import messagebox, ttk, font
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
import csv
import random
import seaborn as sns
import sys
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError as e:
    print(f"Error importing PIL: {e}")
    raise

# Ensure matplotlib uses the TkAgg backend
import matplotlib
matplotlib.use('TkAgg')

# Function to get the correct path for bundled resources
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # When running in development (not bundled)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Define global directories
APPDATA_DIR = os.path.join(os.getenv('APPDATA', os.path.dirname(os.path.abspath(__file__))), 'DietAssistant')
os.makedirs(APPDATA_DIR, exist_ok=True)

# Define directory for saving PNG charts in My Documents
DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Diatrofi")
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

FOOD_FILE = os.path.join(APPDATA_DIR, "foods_expanded.json")
MEAT_FISH_FILE = os.path.join(APPDATA_DIR, "meat_fish.json")
Q_FILE = os.path.join(APPDATA_DIR, "q_values.json")
ICON_DIR = resource_path("icons")
os.makedirs(ICON_DIR, exist_ok=True)

# Global variables
T = None
last_selected_foods = None
weekly_menu_data = None
Q_VALUES = None
foods = []

# Define the specific nutrients
NUTRIENTS = [
    "Υδατάνθρακες",
    "Πρωτεΐνες",
    "Λίπη",
    "Εδώδιμες ίνες",
    "Ασβέστιο",
    "Σίδηρος"
]

# Categories and number of foods per category for each day
CATEGORIES_PER_DAY = {
    "Φρούτα": 1,
    "Λαχανικά": 2,
    "Όσπρια": 1,
    "Κρέας": 1,
    "Αλεύρι/Ψωμί": 1,
    "Ψάρια": 0,
    "Ξηροί Καρποί": 1
}

# Font selection
def get_available_font(preferred_fonts=["Roboto", "Segoe UI", "Arial"]):
    print("Getting available font")
    try:
        available_fonts = font.families()
        for preferred in preferred_fonts:
            if preferred in available_fonts:
                print(f"Font found: {preferred}")
                return preferred
        print("Defaulting to Arial")
        return "Arial"
    except Exception as e:
        print(f"Error in get_available_font: {e}")
        return "Arial"

# Gradient background creation (used in popups)
def create_gradient(width, height, start_color, end_color):
    print(f"Creating gradient: {width}x{height}")
    try:
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        r1, g1, b1 = int(start_color[1:3], 16), int(start_color[3:5], 16), int(start_color[5:7], 16)
        r2, g2, b2 = int(end_color[1:3], 16), int(end_color[3:5], 16), int(end_color[5:7], 16)
        for y in range(height):
            r = int(r1 + (r2 - r1) * y / height)
            g = int(g1 + (g2 - g1) * y / height)
            b = int(b1 + (b2 - b1) * y / height)
            draw.line((0, y, width, y), fill=(r, g, b))
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error in create_gradient: {e}")
        raise

# Custom button class with image-only support (χωρίς hover effect)
class CustomButton(tk.Button):
    def __init__(self, parent, image_path, command, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            command=command,
            bg="#FFFFFF",
            activebackground="#FFFFFF",
            relief="flat",
            borderwidth=0
        )
        print(f"Creating CustomButton with image: {image_path}")
        try:
            # Use resource_path to locate the image
            image_path = resource_path(image_path)
            if os.path.exists(image_path):
                img = Image.open(image_path).resize((200, 100), Image.LANCZOS)
                self.icon = ImageTk.PhotoImage(img)
                self.config(image=self.icon)
                print(f"Icon loaded successfully: {image_path}")
            else:
                print(f"Icon file does not exist: {image_path}")
                self.config(text="Button", fg="#000000", font=(get_available_font(), 10, "bold"))
        except Exception as e:
            print(f"Error loading icon {image_path}: {e}")
            self.config(text="Button", fg="#000000", font=(get_available_font(), 10, "bold"))

# Splash screen function with support for animated GIF
def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)  # Remove window borders
    splash.geometry("300x300+810+390")  # 300x300, centered on 1920x1080 screen

    # Load and display the logo (GIF or static image)
    try:
        logo_path = resource_path("logo.gif")
        if os.path.exists(logo_path):
            # Open the GIF and extract frames
            img = Image.open(logo_path)
            frames = []
            try:
                # Extract all frames from the GIF
                while True:
                    frame = img.copy()
                    frame = frame.resize((300, 300), Image.LANCZOS)  # 300x300
                    frames.append(ImageTk.PhotoImage(frame))
                    img.seek(len(frames))  # Move to the next frame
            except EOFError:
                pass  # End of frames

            # Display the GIF with animation
            logo_label = tk.Label(splash, bg="#2E2E2E")
            logo_label.pack()

            # Animation function
            def animate(frame_idx=0, total_duration=0):
                if total_duration >= 3000:  # Stop after 3 seconds
                    splash.destroy()
                    return
                logo_label.config(image=frames[frame_idx])
                frame_idx = (frame_idx + 1) % len(frames)
                # Get frame duration (default to 100ms if not specified)
                try:
                    frame_duration = img.info.get('duration', 100)
                except:
                    frame_duration = 100
                splash.after(frame_duration, animate, frame_idx, total_duration + frame_duration)

            # Start animation
            animate()
        else:
            # Fallback if logo.gif is not found
            tk.Label(splash, text="Diet Assistant", font=(get_available_font(), 24, "bold"), fg="#FFFFFF", bg="#2E2E2E").pack(expand=True)
            splash.after(3000, splash.destroy)
    except Exception as e:
        print(f"Error loading logo: {e}")
        tk.Label(splash, text="Diet Assistant", font=(get_available_font(), 24, "bold"), fg="#FFFFFF", bg="#2E2E2E").pack(expand=True)
        splash.after(3000, splash.destroy)

    splash.mainloop()

# Data management
def load_foods():
    global foods
    print("Loading foods")
    foods_list = []
    
    if not os.path.exists(FOOD_FILE):
        print(f"No food file found at {FOOD_FILE}, skipping.")
    else:
        try:
            with open(FOOD_FILE, "r", encoding="utf-8") as f:
                foods_expanded = json.load(f)
            foods_list.extend(foods_expanded)
            print(f"Loaded {len(foods_expanded)} foods from foods_expanded.json")
        except Exception as e:
            print(f"Error loading foods_expanded.json: {e}")
            messagebox.showwarning("Προσοχή", f"Σφάλμα φόρτωσης foods_expanded.json: {e}")
    
    if not os.path.exists(MEAT_FISH_FILE):
        print(f"No meat_fish file found at {MEAT_FISH_FILE}, skipping.")
    else:
        try:
            with open(MEAT_FISH_FILE, "r", encoding="utf-8") as f:
                meat_fish = json.load(f)
            foods_list.extend(meat_fish)
            print(f"Loaded {len(meat_fish)} foods from meat_fish.json")
        except Exception as e:
            print(f"Error loading meat_fish.json: {e}")
            messagebox.showwarning("Προσοχή", f"Σφάλμα φόρτωσης meat_fish.json: {e}")
    
    for food in foods_list:
        if set(food['nutrients'].keys()) != set(NUTRIENTS):
            raise ValueError(f"Η τροφή '{food['name']}' δεν έχει τα σωστά θρεπτικά συστατικά: {NUTRIENTS}")
        if food['cost'] <= 0:
            raise ValueError(f"Το κόστος για την τροφή '{food['name']}' πρέπει να είναι θετικό.")
        if 'category' not in food:
            raise ValueError(f"Η τροφή '{food['name']}' δεν έχει πεδίο κατηγορίας.")
        if food['category'] not in CATEGORIES_PER_DAY:
            raise ValueError(f"Η κατηγορία '{food['category']}' της τροφής '{food['name']}' δεν είναι έγκυρη.")
    
    foods = foods_list
    print(f"Total foods loaded: {len(foods)} items")
    return foods

def save_foods(foods):
    print("Saving foods")
    try:
        with open(FOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(foods, f, indent=4, ensure_ascii=False)
        print("Foods saved successfully")
    except Exception as e:
        print(f"Error saving foods: {e}")

def load_q_values():
    global Q_VALUES
    print(f"Attempting to load Q values from {Q_FILE}")
    if not os.path.exists(Q_FILE):
        print("No Q file found, initializing with zeros.")
        Q_VALUES = {nutrient: 0 for nutrient in NUTRIENTS}
        save_q_values()
        return Q_VALUES
    try:
        with open(Q_FILE, "r", encoding="utf-8") as f:
            Q_VALUES = json.load(f)
        if set(Q_VALUES.keys()) != set(NUTRIENTS):
            raise ValueError(f"Το ΣΗΠ δεν έχει τιμές για όλα τα θρεπτικά συστατικά: {NUTRIENTS}")
        print(f"Successfully loaded Q values: {Q_VALUES}")
        return Q_VALUES
    except Exception as e:
        print(f"Error loading Q values: {e}")
        messagebox.showwarning("Προσοχή", f"Σφάλμα φόρτωσης ΣΗΠ: {e}. Θα χρησιμοποιηθούν μηδενικές τιμές.")
        Q_VALUES = {nutrient: 0 for nutrient in NUTRIENTS}
        save_q_values()
        return Q_VALUES

def save_q_values():
    global Q_VALUES
    print(f"Attempting to save Q values to {Q_FILE}: {Q_VALUES}")
    try:
        with open(Q_FILE, "w", encoding="utf-8") as f:
            json.dump(Q_VALUES, f, indent=4, ensure_ascii=False)
        print(f"Q values saved successfully to {Q_FILE}")
        with open(Q_FILE, "r", encoding="utf-8") as f:
            saved_content = json.load(f)
            print(f"Verified saved Q values: {saved_content}")
    except Exception as e:
        print(f"Error saving Q values: {e}")
        messagebox.showerror("Σφάλμα", f"Αποτυχία αποθήκευσης ΣΗΠ: {e}")

def set_q_values():
    global Q_VALUES
    print("Opening Q values editor")
    popup = tk.Toplevel(root)
    popup.title("Ορισμός ΣΗΠ")
    popup.geometry("400x400")
    popup.configure(bg="#FFFFFF")
    try:
        gradient = create_gradient(400, 400, "#4CAF50", "#81C784")
        bg_label = tk.Label(popup, image=gradient)
        bg_label.image = gradient
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error setting popup background: {e}")

    style_frame = ttk.Frame(popup)
    style_frame.pack(pady=10)

    selected_font = get_available_font()
    ttk.Label(style_frame, text="Ορίστε το ΣΗΠ:", font=(selected_font, 10, "bold"), foreground="#000000").pack(pady=2)
    q_entries = {}
    for nutrient in NUTRIENTS:
        frame = ttk.Frame(style_frame)
        frame.pack(pady=2)
        ttk.Label(frame, text=f"{nutrient}:", foreground="#000000").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=10)
        entry.insert(0, str(Q_VALUES[nutrient]) if Q_VALUES else "0")
        entry.pack(side=tk.LEFT, padx=5)
        q_entries[nutrient] = entry

    def save_and_close():
        try:
            new_Q = {}
            for nutrient, entry in q_entries.items():
                value = entry.get().strip()
                if not value:
                    raise ValueError(f"Η τιμή ΣΗΠ για το {nutrient} δεν μπορεί να είναι κενή.")
                new_Q[nutrient] = float(value)
                if new_Q[nutrient] < 0:
                    raise ValueError(f"Η τιμή ΣΗΠ για το {nutrient} πρέπει να είναι μη αρνητική.")
            global Q_VALUES
            Q_VALUES = new_Q
            print(f"New Q_VALUES before saving: {Q_VALUES}")
            save_q_values()
            popup.destroy()
            messagebox.showinfo("Επιτυχία", "Το ΣΗΠ αποθηκεύτηκε επιτυχώς.")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Μη έγκυρα δεδομένα: {e}")
            print(f"Error in save_and_close: {e}")

    ttk.Button(style_frame, text="Αποθήκευση", command=save_and_close).pack(pady=10)

def load_custom_json():
    global foods
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_foods = json.load(f)
            for food in new_foods:
                if set(food['nutrients'].keys()) != set(NUTRIENTS):
                    raise ValueError(f"Η τροφή '{food['name']}' δεν έχει τα σωστά θρεπτικά συστατικά: {NUTRIENTS}")
                if food['cost'] <= 0:
                    raise ValueError(f"Το κόστος για την τροφή '{food['name']}' πρέπει να είναι θετικό.")
                if 'category' not in food:
                    raise ValueError(f"Η τροφή '{food['name']}' δεν έχει πεδίο κατηγορίας.")
                if food['category'] not in CATEGORIES_PER_DAY:
                    raise ValueError(f"Η κατηγορία '{food['category']}' της τροφής '{food['name']}' δεν είναι έγκυρη.")
            foods = new_foods
            save_foods(foods)
            refresh_food_list()
            messagebox.showinfo("Επιτυχία", "Το JSON αρχείο φορτώθηκε με επιτυχία.")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία φόρτωσης JSON: {e}")

# Συνάρτηση για εύρεση τροφής με τη μέγιστη τιμή θρεπτικού συστατικού
def find_max_nutrient_food():
    # Έλεγχος αν η λίστα τροφών είναι κενή
    if not foods:
        messagebox.showwarning("Προσοχή", "Δεν υπάρχουν τροφές.")
        return
    # Λίστα για αποθήκευση των τροφών με μέγιστη τιμή ανά συστατικό
    max_foods = []
    # Επανάληψη για κάθε θρεπτικό συστατικό
    for nutrient in NUTRIENTS:
        # Εύρεση μέγιστης τιμής του συστατικού μεταξύ όλων των τροφών
        max_val = max(food['nutrients'][nutrient] for food in foods)
        # Επιλογή τροφών με τη μέγιστη τιμή και το κόστος τους
        max_food_entries = [(food['name'], food['cost']) for food in foods if food['nutrients'][nutrient] == max_val]
        # Προσθήκη των τροφών στη λίστα αποτελεσμάτων
        for name, cost in max_food_entries:
            max_foods.append((nutrient, name, cost))
    # Δημιουργία συμβολοσειράς αποτελεσμάτων για εμφάνιση
    result = "Κόστος τροφών με μέγιστη αξία ανά συστατικό:\n" + "\n".join(
        [f"- {nutrient}: {cost:.2f} € (Τροφή: {name})" for nutrient, name, cost in max_foods]
    )
    # Εμφάνιση αποτελεσμάτων σε παράθυρο διαλόγου
    messagebox.showinfo("Μέγιστη Αξία", result)

# Συνάρτηση για εύρεση τροφής με το ελάχιστο κόστος ανά μονάδα θρεπτικού συστατικού
def find_min_cost_per_nutrient():
    # Έλεγχος αν η λίστα τροφών είναι κενή
    if not foods:
        messagebox.showwarning("Προσοχή", "Δεν υπάρχουν τροφές.")
        return
    # Λίστα για αποθήκευση των τροφών με ελάχιστο κόστος ανά συστατικό
    min_cost_foods = []
    # Επανάληψη για κάθε θρεπτικό συστατικό
    for nutrient in NUTRIENTS:
        # Λίστα για αποθήκευση κόστους ανά μονάδα συστατικού
        cost_per_nutrient = []
        for food in foods:
            nutrient_value = food['nutrients'][nutrient]
            # Αποφυγή διαίρεσης με το μηδέν
            if nutrient_value > 0:   
                cost_per_unit = food['cost'] / nutrient_value
                cost_per_nutrient.append((food['name'], cost_per_unit))
        # Εύρεση τροφής με το ελάχιστο κόστος ανά μονάδα
        if cost_per_nutrient:
            cheapest = min(cost_per_nutrient, key=lambda x: x[1])
            min_cost_foods.append((nutrient, cheapest[0], cheapest[1]))
        else:
            # Αν δεν υπάρχουν έγκυρες τροφές, προσθήκη προεπιλεγμένης τιμής
            min_cost_foods.append((nutrient, "Καμία τροφή", 0.0))
    # Δημιουργία συμβολοσειράς αποτελεσμάτων για εμφάνιση
    result = "Τροφές με το ελάχιστο κόστος πρόσληψης ανά θρεπτικό συστατικό:\n" + "\n".join(
        [f"- {nutrient}: {cost:.2f} €/μονάδα (Τροφή: {name})" for nutrient, name, cost in min_cost_foods]
    )
    # Εμφάνιση αποτελεσμάτων σε παράθυρο διαλόγου
    messagebox.showinfo("Ελάχιστο Κόστος Πρόσληψης", result)

# Συνάρτηση για υπολογισμό της ιδανικής διατροφής με βάση το ΣΗΠ και τις προτεραιότητες
def calculate_optimal_diet():
    global T, last_selected_foods, Q_VALUES
    # Έλεγχος αν υπάρχουν τροφές
    if not foods:
        messagebox.showwarning("Προσοχή", "Δεν υπάρχουν καταχωρημένες τροφές.")
        return
    # Έλεγχος αν το ΣΗΠ είναι ορισμένο
    if Q_VALUES is None or all(value == 0 for value in Q_VALUES.values()):
        messagebox.showwarning("Προσοχή", "Πρέπει να ορίσετε το ΣΗΠ πρώτα.")
        return
    # Δημιουργία παραθύρου επιλογής
    popup = tk.Toplevel(root)
    popup.title("Επιλογή Τροφών")
    popup.geometry("600x400")
    # Δημιουργία παραθύρου για επιλογή τροφών
    list_frame = ttk.Frame(popup)
    list_frame.pack(pady=10, fill="both", expand=True)
    # Αριστερό listbox για επιλογή τροφών
    listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, bg="#FFFFFF", fg="#000000", height=10)
    for i, food in enumerate(foods):
        listbox.insert(tk.END, food['name'])
    listbox.pack(side=tk.LEFT, padx=10, fill="both", expand=True)
    # Δημιουργία πλαισίου για το δεξί listbox
    selection_frame = ttk.Frame(popup)
    selection_frame.pack(pady=10, fill="both", expand=True)
    selected_foods_label = ttk.Label(selection_frame, text="Επιλεγμένες Τροφές:")
    selected_foods_label.pack(pady=5)
    # Δεξί listbox για εμφάνιση επιλεγμένων τροφών
    selected_foods_listbox = tk.Listbox(selection_frame, bg="#FFFFFF", fg="#000000", height=10)
    selected_foods_listbox.pack(fill="both", expand=True)
    selected_foods_list = []
    # Συνάρτηση για ενημέρωση του δεξιού listbox
    def update_selected_foods(event=None):
        try:
            selected_foods_listbox.delete(0, tk.END)
            current_indices = listbox.curselection()
            selected_foods_list.clear()
            selected_foods_list.extend([foods[i] for i in current_indices])
            for priority, food in enumerate(selected_foods_list, 1):
                selected_foods_listbox.insert(tk.END, f"{priority}. {food['name']}")
        except Exception as e:
            print(f"Error updating selected foods: {e}")
    # Δέσμευση συμβάντος επιλογής στο αριστερό listbox
    listbox.bind("<<ListboxSelect>>", update_selected_foods)
    # Συνάρτηση για επιβεβαίωση επιλογής
    def confirm_selection():
        if not selected_foods_list:
            messagebox.showwarning("Προσοχή", "Πρέπει να επιλέξετε τουλάχιστον μία τροφή.")
            return
        popup.destroy()
        perform_calculation()
    # Δημιουργία ενός και μόνο κουμπιού επιβεβαίωσης
    confirm_button = ttk.Button(popup, text="Επιβεβαίωση Επιλογής", command=confirm_selection)
    confirm_button.pack(pady=5)

    # Συνάρτηση για τον υπολογισμό της ιδανικής διατροφής
    def perform_calculation():
        if not selected_foods_list:
            messagebox.showwarning("Προσοχή", "Πρέπει να επιλέξετε τουλάχιστον μία τροφή.")
            return
        # Ορισμός προτεραιοτήτων για τις επιλεγμένες τροφές
        priorities = list(range(1, len(selected_foods_list) + 1))
        try:
            n = len(selected_foods_list)
            m = len(NUTRIENTS)
            # Έλεγχος αν ο αριθμός επιλεγμένων τροφών είναι έγκυρος
            if n < 1 or n > m:
                messagebox.showwarning("Προσοχή", f"Επιλέξτε από 1 έως {m} τροφές.")
                return
            # Δημιουργία πίνακα Q με τις απαιτήσεις του ΣΗΠ
            Q = np.array([Q_VALUES[nutrient] for nutrient in NUTRIENTS])
            # Δημιουργία πίνακα A με τις θρεπτικές τιμές των επιλεγμένων τροφών
            A = np.array([[food['nutrients'][nutrient] for food in selected_foods_list] for nutrient in NUTRIENTS])
             # Υπολογισμός ποσοτήτων με ελάχιστα τετράγωνα
            T_new, residuals, rank, s = np.linalg.lstsq(A, Q, rcond=None)
            T_new = np.maximum(T_new, 0)  # Αποτροπή αρνητικών ποσοτήτων
            # Καθορισμός ποσοστών κατανομής με βάση τις προτεραιότητες 
            priority_percentages = {1: 0.30, 2: 0.20, 3: 0.15, 4: 0.15, 5: 0.10, 6: 0.10}
            total_quantity = np.sum(T_new)
            distributed_quantities = np.zeros(n)
            for i, priority in enumerate(priorities):
                percentage = priority_percentages.get(priority, 0.10)
                distributed_quantities[i] = total_quantity * percentage
            # Εφαρμογή ορίων στις ποσότητες
            T_new = distributed_quantities
            T_new = np.maximum(T_new, 0.1)  # Ελάχιστο όριο ποσότητας
            T_new = np.minimum(T_new, 10)   # Μέγιστο όριο ποσότητας
            # Έλεγχος αν το σύστημα είναι υποκαθορισμένο
            if rank < min(m, n):
                messagebox.showwarning("Προσοχή", "Το σύστημα είναι υποκαθορισμένο.")
            # Υπολογισμός συνολικού κόστους
            C = np.array([food['cost'] for food in selected_foods_list])
            total_cost = np.dot(C, T_new)
            # Έλεγχος για μη έγκυρο κόστος
            if any(cost <= 0 for cost in C):
                messagebox.showwarning("Προσοχή", "Μη έγκυρο κόστος σε κάποια τροφή.")
                return
            # Έλεγχος για υπερβολικό κόστος
            if total_cost > 100:
                messagebox.showwarning("Προσοχή", f"Το συνολικό κόστος ({total_cost:.2f} €) φαίνεται υπερβολικό.")
            # Δημιουργία συμβολοσειράς αποτελεσμάτων
            result = "Ιδανική ποσότητα ανά τροφή (με βάση το ΣΗΠ και τις προτεραιότητες):\n"
            for i, amount in enumerate(T_new):
                cost = amount * selected_foods_list[i]['cost']
                result += f"- {selected_foods_list[i]['name']} (Προτεραιότητα: {priorities[i]}): {amount:.2f} μονάδες (Κόστος: {cost:.2f} €)\n"
            result += f"\nΣυνολικό κόστος: {total_cost:.2f} €"
           # Εμφάνιση αποτελεσμάτων 
            messagebox.showinfo("Αποτέλεσμα", result)
            # Ενημέρωση παγκόσμιων μεταβλητών
            global T, last_selected_foods
            T = T_new  # Update global T
            last_selected_foods = selected_foods_list
            # Κλήση συνάρτησης για γραφική απεικόνιση
            plot_cost_vs_total_cost()
        except np.linalg.LinAlgError as e:
            messagebox.showerror("Σφάλμα", f"Πρόβλημα στο λογισμικό: {e}.")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία υπολογισμού: {e}")

def calculate_weekly_menu():
    global T, last_selected_foods, Q_VALUES, weekly_menu_data
    # Λειτουργία 1: Έλεγχος Εισόδων
    # Ελέγχει αν η λίστα τροφίμων είναι κενή
    if not foods:
        messagebox.showwarning("Προσοχή", "Δεν υπάρχουν καταχωρημένες τροφές.")
        return
    # Εμφανίζει και ελέγχει τις τιμές Q_VALUES (διατροφικές απαιτήσεις)
    print(f"Checking Q_VALUES before calculating weekly menu: {Q_VALUES}")
    if Q_VALUES is None:
        messagebox.showwarning("Προσοχή", "Πρέπει να ορίσετε το ΣΗΠ πρώτα από το μενού 'Αρχείο' > 'Ορισμός ΣΗΠ'.")
        return
    # Ελέγχει αν όλες οι τιμές του Q_VALUES είναι μηδέν
    if all(value == 0 for value in Q_VALUES.values()):
        messagebox.showwarning("Προσοχή", "Το ΣΗΠ περιέχει μόνο μηδενικές τιμές. Ορίστε σωστές τιμές από το μενού 'Αρχείο' > 'Ορισμός ΣΗΠ'.")
        return
    

    # Λειτουργία 2: Αρχικοποίηση
    # Καθορίζει τον αριθμό των θρεπτικών συστατικών και τις ημέρες της εβδομάδαςm = len(NUTRIENTS)
    days = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
    MAX_COST_PER_DAY = 20.0    # Μέγιστο επιτρεπόμενο κόστος ανά ημέρα
    # Μετατρέπει το Q_VALUES σε πίνακα NumPy για υπολογισμούς
    original_Q = np.array([Q_VALUES[nutrient] for nutrient in NUTRIENTS])
    print(f"Original ΣΗΠ for weekly menu: {original_Q}")
    # Αρχικοποιεί λίστες και σύνολα για αποθήκευση του εβδομαδιαίου μενού
    weekly_menu = []
    used_food_indices = set()

    # Λειτουργία 3: Οργάνωση Τροφίμων ανά Κατηγορία
    # Ομαδοποιεί τις τροφές ανά κατηγορία για ευκολότερη επιλογή
    foods_by_category = {}
    for idx, food in enumerate(foods):
        category = food["category"]
        if category not in foods_by_category:
            foods_by_category[category] = []
        foods_by_category[category].append((food, idx))

    # Λειτουργία 4: Υπολογισμός Ημερήσιου Μενού
    for day_idx, day in enumerate(days):
        # Προσαρμόζει τις απαιτήσεις κατηγοριών για συγκεκριμένες ημέρες (ψάρια Τετάρτη/Κυριακή)
        daily_categories = CATEGORIES_PER_DAY.copy()
        if day in ["Τετάρτη", "Κυριακή"]:
            daily_categories["Ψάρια"] = 1
            daily_categories["Κρέας"] = 0
        else:
            daily_categories["Ψάρια"] = 0
            daily_categories["Κρέας"] = 1

        # Υπολογίζει τον συνολικό αριθμό τροφίμων που χρειάζονται ανά ημέρα
        k = sum(daily_categories.values())

        # Αρχικοποιεί μεταβλητές για επιλογή τροφίμων και έλεγχο κόστους
        selected_food_indices = set()
        selected_foods_list = []
        cost_within_limit = False
        Q_scale = 1.0   # Ξεκινά με πλήρεις διατροφικές απαιτήσεις

        # Λειτουργία 5: Επιλογή Τροφίμων και Βελτιστοποίηση
        # Επαναλαμβάνεται μέχρι το κόστος να είναι εντός ορίων ή το Q_scale να πέσει πολύ
        while Q_scale >= 0.7 and not cost_within_limit:
            Q = original_Q * Q_scale    # Κλιμακώνει τις διατροφικές απαιτήσεις
            selected_food_indices.clear()
            selected_foods_list = []

            # Επιλέγει τροφές για κάθε κατηγορία με βάση τις απαιτήσεις
            for category, count in daily_categories.items():
                if count == 0:
                    continue
                # Προτιμά τροφές που δεν έχουν χρησιμοποιηθεί σε άλλες ημέρες
                available_foods = [(food, idx) for food, idx in foods_by_category[category] if idx not in used_food_indices and idx not in selected_food_indices]
                if len(available_foods) < count:
                    # Εναλλακτικά, επιλέγει οποιαδήποτε διαθέσιμη τροφή στην κατηγορία
                    available_foods = [(food, idx) for food, idx in foods_by_category[category] if idx not in selected_food_indices]
                if len(available_foods) < count:
                    messagebox.showwarning("Προσοχή", f"Δεν υπάρχουν αρκετές τροφές στην κατηγορία '{category}' για την {day}. Χρειάζονται {count}, βρέθηκαν {len(available_foods)}.")
                    return

                # Επιλέγει τυχαία τον απαιτούμενο αριθμό τροφίμων 
                random.shuffle(available_foods)
                for i in range(count):
                    if available_foods:
                        food, idx = available_foods[i]
                        selected_food_indices.add(idx)
                        selected_foods_list.append(food)
                        print(f"{day}: Selected {food['name']} (index {idx}) from category {category}")

            # Ελέγχει αν επιλέχθηκαν αρκετές τροφές
            if len(selected_foods_list) != k:
                messagebox.showwarning("Προσοχή", f"Δεν βρέθηκε αρκετός αριθμός τροφών για την {day} για να καλύψει τις κατηγορίες.")
                return

            # Λειτουργία 6: Διατροφική Βελτιστοποίηση
            # Δημιουργεί πίνακα θρεπτικών συστατικών για τις επιλεγμένες τροφές
            A = np.array([[food['nutrients'][nutrient] for food in selected_foods_list] for nutrient in NUTRIENTS])
            # Υπολογίζει τις ποσότητες (T) για να ικανοποιηθούν οι κλιμακωμένες απαιτήσεις (Q)
            T, residuals, rank, s = np.linalg.lstsq(A, Q, rcond=None)
            T = np.maximum(T, 0)          # Εξασφαλίζει μη αρνητικές ποσότητες
            T = np.maximum(T, 0.1)        # Εξασφαλίζει ελάχιστη ποσότητα 0.1
            T = np.minimum(T, 20)         # Περιορίζει τη μέγιστη ποσότητα σε 20

            # Ελέγχει αν τα υπολείμματα είναι υπερβολικά υψηλά (κακή διατροφική προσαρμογή)
            if residuals.size > 0 and residuals[0] > sum(Q) * 0.5:
                print(f"{day}: Residuals too high with Q scale {Q_scale}, trying a lower scale.")
                Q_scale -= 0.05    # Μειώνει τις διατροφικές απαιτήσεις
                continue

            # Λειτουργία 7: Υπολογισμός και Έλεγχος Κόστους
            # Υπολογίζει το συνολικό κόστος της ημέρας
            C = np.array([food['cost'] for food in selected_foods_list])
            total_cost = np.dot(C, T)
            print(f"{day}: Costs from selected foods: {C}")
            print(f"{day}: Calculated T: {T}")

            # Ελέγχει αν τα κόστη είναι έγκυρα (θετικά)
            if any(cost <= 0 for cost in C):
                messagebox.showwarning("Προσοχή", f"Μη έγκυρο κόστος σε κάποια τροφή για την {day}. Ελέγξτε τα JSON αρχεία.")
                return

            # Ελέγχει αν το συνολικό κόστος είναι εντός του ημερήσιου ορίου
            if total_cost <= MAX_COST_PER_DAY:
                cost_within_limit = True
            else:
                print(f"{day}: Cost {total_cost:.2f} exceeds limit {MAX_COST_PER_DAY:.2f} with Q scale {Q_scale}, trying a lower scale.")
                Q_scale -= 0.05    # Μειώνει τις διατροφικές απαιτήσεις αν το κόστος είναι υψηλό

        # Λειτουργία 8: Διαχείριση Αποτυχίας Κόστους
        if not cost_within_limit:
            messagebox.showwarning("Προσοχή", f"Δεν ήταν δυνατόν να βρεθεί μενού για την {day} με κόστος κάτω από {MAX_COST_PER_DAY:.2f} €, ακόμα και με ΣΗΠ μειωμένο στο 70%. Προσθέστε φθηνότερες τροφές.")
            return

        # Αποθηκεύει το ημερήσιο μενού
        daily_menu = (selected_foods_list, T, total_cost, Q_scale)
        weekly_menu.append((day, daily_menu))
        used_food_indices.update(selected_food_indices)

    # Λειτουργία 9: Δημιουργία και Εμφάνιση Αποτελεσμάτων
    # Δημιουργεί συμβολοσειρά για το εβδομαδιαίο μενού
    result = "Εβδομαδιαίο Μενού (Βάσει ΣΗΠ):\n\n"
    weekly_total_cost = 0
    for day, (selected_foods_list, T, total_cost, Q_scale) in weekly_menu:
        result += f"{day} (ΣΗΠ στο {Q_scale*100:.0f}%):\n"
        for i, amount in enumerate(T):
            cost = amount * selected_foods_list[i]['cost']
            result += f"- {selected_foods_list[i]['name']} ({selected_foods_list[i]['category']}): {amount:.2f} μονάδες (Κόστος: {cost:.2f} €)\n"
        result += f"Συνολικό Κόστος {day}: {total_cost:.2f} €\n\n"
        weekly_total_cost += total_cost

    result += f"Συνολικό Κόστος Εβδομάδας: {weekly_total_cost:.2f} €"
    # Εμφανίζει το μενού σε πλαίσιο μηνύματος
    messagebox.showinfo("Εβδομαδιαίο Μενού", result)

    # Λειτουργία 10: Αποθήκευση Αποτελεσμάτων και Οπτικοποίηση
    # Αποθηκεύει τις τελευταίες επιλεγμένες τροφές και τα δεδομένα του μενού
    last_selected_foods = selected_foods_list
    weekly_menu_data = weekly_menu
    # Καλεί συνάρτηση για οπτικοποίηση κόστους (υποτίθεται ότι ορίζεται αλλού)
    plot_cost_vs_total_cost()

def run_sensitivity_analysis():
    global Q_VALUES
    if not foods:
        messagebox.showwarning("Προσοχή", "Δεν υπάρχουν τροφές για ανάλυση.")
        return
    print(f"Checking Q_VALUES before sensitivity analysis: {Q_VALUES}")
    if Q_VALUES is None:
        messagebox.showwarning("Προσοχή", "Πρέπει να ορίσετε το ΣΗΠ πρώτα από το μενού 'Αρχείο' > 'Ορισμός ΣΗΠ'.")
        return
    if all(value == 0 for value in Q_VALUES.values()):
        messagebox.showwarning("Προσοχή", "Το ΣΗΠ περιέχει μόνο μηδενικές τιμές. Ορίστε σωστές τιμές από το μενού 'Αρχείο' > 'Ορισμός ΣΗΠ'.")
        return
    
    popup = tk.Toplevel(root)
    popup.title("Επιλογή Τροφών για Ανάλυση Ευαισθησίας")
    popup.geometry("300x400")
    popup.configure(bg="#FFFFFF")
    try:
        gradient = create_gradient(300, 400, "#4CAF50", "#81C784")
        bg_label = tk.Label(popup, image=gradient)
        bg_label.image = gradient
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error setting popup background: {e}")
    
    ttk.Label(popup, text="Επιλέξτε τροφές για σύγκριση:", font=(get_available_font(), 10, "bold"), foreground="#000000").pack(pady=10)
    listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE, bg="#3A3A3A", fg="#FFFFFF", height=10)
    for food in foods:
        listbox.insert(tk.END, food['name'])
    listbox.pack(pady=10)

    # Add distribution selection
    ttk.Label(popup, text="Επιλέξτε κατανομή:", font=(get_available_font(), 10, "bold"), foreground="#000000").pack(pady=5)
    distribution_var = tk.StringVar(value="Ομοιόμορφη")
    distribution_menu = ttk.OptionMenu(popup, distribution_var, "Ομοιόμορφη", "Ομοιόμορφη", "Κανονική")
    distribution_menu.pack(pady=5)
    
    def confirm_selection():
        selected_indices = listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Προσοχή", "Πρέπει να επιλέξετε τουλάχιστον μία τροφή.")
            return
        selected_foods = [foods[i] for i in selected_indices]
        distribution = distribution_var.get()
        popup.destroy()
        
        try:
            print(f"Starting sensitivity analysis for {len(selected_foods)} foods: {[food['name'] for food in selected_foods]}")
            m = len(NUTRIENTS)
            n = len(foods)
            A = np.array([[food['nutrients'][nutrient] for food in foods] for nutrient in NUTRIENTS])
            
            Q = np.array([Q_VALUES[nutrient] for nutrient in NUTRIENTS])
            print(f"Using global ΣΗΠ for sensitivity analysis: {Q}")
            
            T_base, residuals, rank, s = np.linalg.lstsq(A, Q, rcond=None)
            if rank < m:
                messagebox.showwarning("Προσοχή", "Το σύστημα είναι υποκαθορισμένο ή προβληματικό. Δοκιμάστε διαφορετικές τροφές.")
                return
            T_base = np.maximum(T_base, 0)
            base_cost = sum(T_base[i] * foods[i]['cost'] for i in range(n))
            print(f"Base T: {T_base}, Base Cost: {base_cost}")
            
            food_sensitivities = {}
            for selected_food in selected_foods:
                sensitivities = []
                idx = foods.index(selected_food)
                for _ in range(10):
                    perturbed_A = A.copy()
                    # Use selected distribution for perturbation
                    if distribution == "Ομοιόμορφη":
                        perturbation = np.random.uniform(0.95, 1.05, size=(m, 1))  # ±5% uniform
                    else:  # Κανονική
                        perturbation = np.random.normal(1.0, 0.015, size=(m, 1))  # Mean 1.0, std 0.015 (~±5% in 2 std)
                        perturbation = np.clip(perturbation, 0.95, 1.05)  # Ensure within reasonable bounds
                    perturbed_A[:, idx] *= perturbation.flatten()
                    T_new, residuals_new, rank_new, s_new = np.linalg.lstsq(perturbed_A, Q, rcond=None)
                    T_new = np.maximum(T_new, 0)
                    delta_quantity = abs(T_new[idx] - T_base[idx])
                    new_cost = sum(T_new[i] * foods[i]['cost'] for i in range(n))
                    delta_cost = abs(new_cost - base_cost)
                    sensitivities.append((delta_quantity, delta_cost))
                    print(f"{selected_food['name']} Iteration: Delta Quantity={delta_quantity:.4f}, Delta Cost={delta_cost:.4f}")
                
                avg_delta_quantity = sum(d[0] for d in sensitivities) / len(sensitivities)
                avg_delta_cost = sum(d[1] for d in sensitivities) / len(sensitivities)
                
                if T_base[idx] > 0:
                    avg_delta_quantity = (avg_delta_quantity / T_base[idx]) * 100
                if base_cost > 0:
                    avg_delta_cost = (avg_delta_cost / base_cost) * 100
                
                food_sensitivities[selected_food['name']] = (avg_delta_quantity, avg_delta_cost)
            
            result = f"Αποτελέσματα Ανάλυσης Ευαισθησίας (Κατανομή: {distribution}):\n\n"
            for food_name, (avg_delta_quantity, avg_delta_cost) in food_sensitivities.items():
                result += f"Τροφή: {food_name}\n"
                result += f"  Επίδραση στην ποσότητα: {avg_delta_quantity:.2f}% (ποσοστιαία αλλαγή)\n"
                result += f"  Επίδραση στο κόστος: {avg_delta_cost:.2f}% (ποσοστιαία αλλαγή)\n\n"
            messagebox.showinfo("Ανάλυση Ευαισθησίας", result)
            
            plot_window = tk.Toplevel(root)
            plot_window.title("Σύγκριση Ανάλυσης Ευαισθησίας")
            plot_window.geometry(f"{max(800, len(selected_foods) * 200)}x500")
            fig, ax = plt.subplots(figsize=(max(10, len(selected_foods) * 2), 5))
            plt.style.use('dark_background')
            
            food_names = list(food_sensitivities.keys())
            delta_quantities = [food_sensitivities[name][0] for name in food_names]
            delta_costs = [food_sensitivities[name][1] for name in food_names]
            
            bar_width = 0.35
            index = np.arange(len(food_names))
            
            ax.bar(index, delta_quantities, bar_width, label="Επίδραση στην Ποσότητα (%)", color="#4CAF50")
            ax.bar(index + bar_width, delta_costs, bar_width, label="Επίδραση στο Κόστος (%)", color="#FF5722")
            
            ax.set_xlabel("Τροφές", color="#FFFFFF")
            ax.set_ylabel("Αλλαγή (%)", color="#FFFFFF")
            ax.set_title("Σύγκριση Ευαισθησίας Τροφών", color="#FFFFFF")
            ax.set_xticks(index + bar_width / 2)
            ax.set_xticklabels(food_names, rotation=45, ha='right')
            ax.legend()
            ax.tick_params(colors="#FFFFFF")
            
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack()
            # Save the sensitivity analysis chart to DOCUMENTS_DIR
            sensitivity_path = os.path.join(DOCUMENTS_DIR, "sensitivity_analysis_comparison.png")
            plt.savefig(sensitivity_path)
            plt.close(fig)
        except np.linalg.LinAlgError as e:
            messagebox.showerror("Σφάλμα", f"Πρόβλημα στο λογισμικό: {e}. Ελέγξτε τις εισαγόμενες τροφές.")
            print(f"Linear algebra error: {e}")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία ανάλυσης: {e}")
            print(f"General error in sensitivity: {e}")

    ttk.Button(popup, text="Επιβεβαίωση Επιλογής", command=confirm_selection).pack(pady=10)

def plot_cost_vs_total_cost():
    global T, last_selected_foods, weekly_menu_data
    print("Attempting to plot cost vs total cost")
    if not foods or (T is None and weekly_menu_data is None):
        print("No data available for plotting: T or weekly_menu_data is None")
        messagebox.showwarning("Προσοχή", "Υπολογίστε πρώτα την ιδανική διατροφή ή το εβδομαδιαίο μενού για να δείτε το διάγραμμα.")
        return

    try:
        if weekly_menu_data:
            print("Plotting in weekly menu mode")
            # Weekly menu mode: Aggregate costs by category across all days
            category_costs = {category: 0 for category in CATEGORIES_PER_DAY.keys()}
            for day, (selected_foods_list, T, total_cost, Q_scale) in weekly_menu_data:
                for i, food in enumerate(selected_foods_list):
                    category = food['category']
                    cost = T[i] * food['cost']
                    category_costs[category] += cost

            labels = list(category_costs.keys())
            individual_costs = [category_costs[category] for category in labels]
            total_cost = sum(individual_costs)
            n = len(labels)
        else:
            print("Plotting in optimal diet mode")
            # Optimal diet mode: Aggregate by category
            category_costs = {category: 0 for category in CATEGORIES_PER_DAY.keys()}
            for i, food in enumerate(last_selected_foods):
                category = food['category']
                cost = T[i] * food['cost']
                category_costs[category] += cost

            labels = list(category_costs.keys())
            individual_costs = [category_costs[category] for category in labels]
            total_cost = sum(individual_costs)
            n = len(labels)

        # Check for invalid values in individual_costs
        if any(np.isnan(cost) or np.isinf(cost) for cost in individual_costs):
            print("Invalid values in individual_costs:", individual_costs)
            messagebox.showerror("Σφάλμα", "Τα δεδομένα για το διάγραμμα περιέχουν μη έγκυρες τιμές (NaN ή inf).")
            return

        print(f"Labels: {labels}")
        print(f"Individual Costs: {individual_costs}")
        print(f"Total Cost: {total_cost}")

        # Bar chart (grouped by category)
        plot_window_bar = tk.Toplevel(root)
        plot_window_bar.title("Κόστος vs Συνολικό Κόστος ανά Κατηγορία")
        plot_window_bar.geometry(f"{max(800, n * 50)}x500")
        fig, ax = plt.subplots(figsize=(max(10, n * 0.5), 5))
        plt.style.use('dark_background')
        index = np.arange(n)
        ax.bar(index, individual_costs, color="#4CAF50", label="Κόστος Κατηγορίας")
        ax.axhline(y=total_cost, color="#FF5722", linestyle="--", label=f"Συνολικό Κόστος: {total_cost:.2f} €")
        ax.set_xlabel("Κατηγορία", color="#FFFFFF")
        ax.set_ylabel("Κόστος (€)", color="#FFFFFF")
        ax.set_title("Κόστος vs Συνολικό Κόστος", color="#FFFFFF")
        ax.set_xticks(index)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.tick_params(axis='x', labelsize=8)
        ax.set_ylim(0)
        ax.legend()
        canvas = FigureCanvasTkAgg(fig, master=plot_window_bar)
        canvas.draw()
        canvas.get_tk_widget().pack()
        # Save the bar chart to DOCUMENTS_DIR
        bar_chart_path = os.path.join(DOCUMENTS_DIR, "cost_vs_total_cost.png")
        plt.savefig(bar_chart_path)

        # Heatmap for cost distribution
        plot_window_heatmap = tk.Toplevel(root)
        plot_window_heatmap.title("Κατανομή Κόστους Διατροφής (Heatmap)")
        plot_window_heatmap.geometry("800x800")
        fig_heatmap, ax_heatmap = plt.subplots(figsize=(8, 8))
        plt.style.use('dark_background')

        # Prepare data for heatmap
        days = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
        categories = list(CATEGORIES_PER_DAY.keys())
        cost_matrix = np.zeros((len(categories), len(days)))

        if weekly_menu_data:
            print("Preparing heatmap data for weekly menu")
            for day_idx, (day, (selected_foods_list, T, total_cost, Q_scale)) in enumerate(weekly_menu_data):
                for i, food in enumerate(selected_foods_list):
                    category = food['category']
                    cost = T[i] * food['cost']
                    category_idx = categories.index(category)
                    cost_matrix[category_idx, day_idx] += cost
        else:
            print("Preparing heatmap data for optimal diet")
            day_costs = {category: 0 for category in CATEGORIES_PER_DAY.keys()}
            for i, food in enumerate(last_selected_foods):
                category = food['category']
                cost = T[i] * food['cost']
                day_costs[category] += cost
            for category_idx, category in enumerate(categories):
                cost_matrix[category_idx, :] = day_costs[category]

        # Check for invalid values in cost_matrix
        if np.any(np.isnan(cost_matrix)) or np.any(np.isinf(cost_matrix)):
            print("Invalid values in cost_matrix:", cost_matrix)
            messagebox.showerror("Σφάλμα", "Τα δεδομένα για το heatmap περιέχουν μη έγκυρες τιμές (NaN ή inf).")
            plt.close(fig_heatmap)
            return

        print(f"Cost Matrix for Heatmap:\n{cost_matrix}")

        # Create heatmap
        sns.heatmap(cost_matrix, annot=True, fmt=".2f", cmap="YlOrRd", xticklabels=days, yticklabels=categories, ax=ax_heatmap, cbar_kws={'label': 'Κόστος (€)'})
        ax_heatmap.set_xlabel("Ημέρα", color="#FFFFFF")
        ax_heatmap.set_ylabel("Κατηγορία", color="#FFFFFF")
        ax_heatmap.set_title("Κατανομή Κόστους Διατροφής (Heatmap)", color="#FFFFFF")
        ax_heatmap.tick_params(colors="#FFFFFF")
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        canvas_heatmap = FigureCanvasTkAgg(fig_heatmap, master=plot_window_heatmap)
        canvas_heatmap.draw()
        canvas_heatmap.get_tk_widget().pack()
        # Save the heatmap to DOCUMENTS_DIR
        heatmap_path = os.path.join(DOCUMENTS_DIR, "cost_distribution_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close(fig)
        plt.close(fig_heatmap)
        print("Plots generated successfully")
        # Inform the user where the charts are saved
        messagebox.showinfo("Διαγράμματα", f"Τα διαγράμματα αποθηκεύτηκαν στον κατάλογο:\n{DOCUMENTS_DIR}")
    except Exception as e:
        print(f"Error in plot_cost_vs_total_cost: {e}")
        messagebox.showerror("Σφάλμα", f"Αποτυχία δημιουργίας διαγραμμάτων: {e}")

def export_diet_results():
    global T, last_selected_foods
    if T is None or last_selected_foods is None:
        messagebox.showwarning("Προσοχή", "Υπολογίστε πρώτα την ιδανική διατροφή για να εξάγετε τα αποτελέσματα.")
        return
    try:
        # Save the CSV to DOCUMENTS_DIR
        export_path = os.path.join(DOCUMENTS_DIR, "diet_results.csv")
        with open(export_path, "w", newline='', encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Τροφή", "Ποσότητα (μονάδες)", "Κόστος (€)"])
            for i, food in enumerate(last_selected_foods):
                writer.writerow([food['name'], f"{T[i]:.2f}", f"{T[i] * food['cost']:.2f}"])
            total_cost = sum(T[i] * food['cost'] for i, food in enumerate(last_selected_foods))
            writer.writerow(["", "Συνολικό Κόστος", f"{total_cost:.2f}"])
        messagebox.showinfo("Επιτυχία", f"Τα αποτελέσματα εξήχθησαν στο {export_path}.")
    except Exception as e:
        messagebox.showerror("Σφάλμα", f"Αποτυχία εξαγωγής: {e}")

def refresh_food_list():
    print("Refreshing food list")
    tree.delete(*tree.get_children())
    for i, food in enumerate(foods):
        nutrient_values = [food['nutrients'][nutrient] for nutrient in NUTRIENTS]
        tree.insert("", "end", iid=i, values=([food['name'], food['category']] + nutrient_values + [f"{food['cost']:.2f} €"]))
        if i % 2 == 0:
            tree.item(i, tags=("evenrow",))
        else:
            tree.item(i, tags=("oddrow",))

def update_status(message):
    status_var.set(message)
    root.after(3000, lambda: status_var.set(""))

def add_food():
    open_food_editor()
    update_status("Νέα τροφή προστέθηκε.")

def edit_food():
    selected = tree.selection()
    if not selected:
        return
    index = int(selected[0])
    open_food_editor(index)
    update_status("Τροφή ενημερώθηκε.")

def open_food_editor(index=None):
    is_edit = index is not None
    popup = tk.Toplevel(root)
    popup.title("Επεξεργασία τροφής" if is_edit else "Προσθήκη τροφής")
    popup.geometry("400x450")
    popup.configure(bg="#FFFFFF")
    try:
        gradient = create_gradient(400, 450, "#4CAF50", "#81C784")
        bg_label = tk.Label(popup, image=gradient)
        bg_label.image = gradient
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error setting popup background: {e}")

    food = foods[index] if is_edit else {"name": "", "nutrients": {nutrient: 0 for nutrient in NUTRIENTS}, "cost": 0.0, "category": ""}

    style_frame = ttk.Frame(popup)
    style_frame.pack(pady=10)

    selected_font = get_available_font()
    ttk.Label(style_frame, text="Όνομα τροφής:", font=(selected_font, 10, "bold"), foreground="#000000").pack(pady=2)
    name_entry = ttk.Entry(style_frame, width=40)
    name_entry.insert(0, food["name"])
    name_entry.pack(pady=2)

    ttk.Label(style_frame, text="Κατηγορία:", font=(selected_font, 10, "bold"), foreground="#000000").pack(pady=2)
    category_var = tk.StringVar(value=food.get("category", ""))
    category_menu = ttk.OptionMenu(style_frame, category_var, category_var.get() or "Επιλέξτε κατηγορία", *CATEGORIES_PER_DAY.keys())
    category_menu.pack(pady=2)

    ttk.Label(style_frame, text="Θρεπτικά Συστατικά:", font=(selected_font, 10, "bold"), foreground="#000000").pack(pady=2)
    nutrient_entries = {}
    for nutrient in NUTRIENTS:
        frame = ttk.Frame(style_frame)
        frame.pack(pady=2)
        ttk.Label(frame, text=f"{nutrient}:", foreground="#000000").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=10)
        entry.insert(0, str(food["nutrients"][nutrient]))
        entry.pack(side=tk.LEFT, padx=5)
        nutrient_entries[nutrient] = entry

    ttk.Label(style_frame, text="Κόστος ανά μονάδα (σε ευρώ):", font=(selected_font, 10, "bold"), foreground="#000000").pack(pady=2)
    cost_entry = ttk.Entry(style_frame, width=40)
    cost_entry.insert(0, str(food["cost"]))
    cost_entry.pack(pady=2)

    def save_and_close():
        try:
            name = name_entry.get().strip()
            if not name:
                raise ValueError("Το όνομα δεν μπορεί να είναι κενό.")
            category = category_var.get()
            if not category or category == "Επιλέξτε κατηγορία":
                raise ValueError("Πρέπει να επιλέξετε κατηγορία.")
            nutrients = {}
            for nutrient, entry in nutrient_entries.items():
                value = entry.get().strip()
                if not value:
                    raise ValueError(f"Η τιμή για το {nutrient} δεν μπορεί να είναι κενή.")
                nutrients[nutrient] = float(value)
                if nutrients[nutrient] < 0:
                    raise ValueError(f"Η τιμή για το {nutrient} πρέπει να είναι μη αρνητική.")
            cost = float(cost_entry.get())
            if cost <= 0:
                raise ValueError("Το κόστος πρέπει να είναι θετικό.")
            food_data = {"name": name, "nutrients": nutrients, "cost": cost, "category": category}
            if is_edit:
                foods[index] = food_data
            else:
                foods.append(food_data)
            save_foods(foods)
            refresh_food_list()
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Μη έγκυρα δεδομένα: {e}")

    ttk.Button(style_frame, text="Αποθήκευση", command=save_and_close).pack(pady=10)

def delete_food():
    selected = tree.selection()
    if not selected:
        return
    index = int(selected[0])
    del foods[index]
    save_foods(foods)
    refresh_food_list()
    update_status("Τροφή διαγράφηκε.")

def setup_main_window():
    print("Setting up main window")
    try:
        root.title("FOOD COMPANION")
        root.geometry("960x600")
        root.configure(bg="#FFFFFF")

        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Φόρτωση JSON", command=load_custom_json)
        filemenu.add_command(label="Ορισμός ΣΗΠ", command=set_q_values)
        filemenu.add_command(label="Εξαγωγή Αποτελεσμάτων", command=export_diet_results)
        filemenu.add_command(label="Έξοδος", command=confirm_exit)
        menubar.add_cascade(label="Αρχείο", menu=filemenu)
        root.config(menu=menubar)

        # Create a frame to ensure the background behind the logo is white
        title_container = tk.Frame(root, bg="#FFFFFF")
        title_container.pack(fill="x", pady=10)

        title_frame = tk.Frame(title_container, bg="#FFFFFF")
        title_frame.pack()

        # Load and display the header logo
        try:
            logo_path = resource_path("header_logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((300, 100), Image.LANCZOS)
                header_logo = ImageTk.PhotoImage(img)
                title_label = tk.Label(title_frame, image=header_logo, bg="#FFFFFF")
                title_label.image = header_logo  # Keep a reference to avoid garbage collection
                title_label.pack()
            else:
                messagebox.showwarning("Προσοχή", "Το αρχείο header_logo.png δεν βρέθηκε. Θα χρησιμοποιηθεί το προεπιλεγμένο κείμενο.")
                title_label = tk.Label(title_frame, text="FOOD COMPANION", font=(get_available_font(), 24, "bold"), fg="#000000", bg="#FFFFFF")
                title_label.pack()
        except Exception as e:
            print(f"Error loading header logo: {e}")
            messagebox.showerror("Σφάλμα", f"Σφάλμα φόρτωσης header_logo.png: {e}")
            title_label = tk.Label(title_frame, text="FOOD COMPANION", font=(get_available_font(), 24, "bold"), fg="#000000", bg="#FFFFFF")
            title_label.pack()

        style = ttk.Style()
        style.theme_use("clam")
        selected_font = get_available_font()
        style.configure("Treeview.Heading", font=(selected_font, 11, "bold"), background="#4CAF50", foreground="#FFFFFF")
        style.configure("Treeview", font=(selected_font, 10), rowheight=28, background="#3A3A3A", foreground="#FFFFFF", fieldbackground="#3A3A3A")
        style.map("Treeview", background=[("selected", "#2196F3")])
        style.configure("Treeview", tagconfigure="evenrow", background="#333333")
        style.configure("Treeview", tagconfigure="oddrow", background="#2E2E2E")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)

        global tree
        tree = ttk.Treeview(frame, columns=("Όνομα", "Κατηγορία", "Υδατάνθρακες", "Πρωτεΐνες", "Λίπη", "Εδώδιμες ίνες", "Ασβέστιο", "Σίδηρος", "Κόστος"), show="headings", style="Treeview")
        tree.heading("Όνομα", text="Όνομα")
        tree.heading("Κατηγορία", text="Κατηγορία")
        tree.heading("Υδατάνθρακες", text="Υδατάνθρακες")
        tree.heading("Πρωτεΐνες", text="Πρωτεΐνες")
        tree.heading("Λίπη", text="Λίπη")
        tree.heading("Εδώδιμες ίνες", text="Εδώδιμες ίνες")
        tree.heading("Ασβέστιο", text="Ασβέστιο")
        tree.heading("Σίδηρος", text="Σίδηρος")
        tree.heading("Κόστος", text="Κόστος (€)")
        tree.column("Όνομα", width=150, minwidth=100)
        tree.column("Κατηγορία", width=100, minwidth=50)
        tree.column("Υδατάνθρακες", width=100, minwidth=50)
        tree.column("Πρωτεΐνες", width=100, minwidth=50)
        tree.column("Λίπη", width=100, minwidth=50)
        tree.column("Εδώδιμες ίνες", width=100, minwidth=50)
        tree.column("Ασβέστιο", width=100, minwidth=50)
        tree.column("Σίδηρος", width=100, minwidth=50)
        tree.column("Κόστος", width=100, minwidth=50)
        tree.pack(fill="both", expand=True, pady=10)

        tree.bind("<Double-1>", lambda e: edit_food())

        btn_frame = ttk.Frame(root, padding=10)
        btn_frame.configure(style="Custom.TFrame")
        btn_frame.pack()

        style = ttk.Style()
        style.configure("Custom.TFrame", background="#FFFFFF")

        buttons = [
            (os.path.join("icons", "add.png"), add_food),
            (os.path.join("icons", "edit.png"), edit_food),
            (os.path.join("icons", "delete.png"), delete_food),
            (os.path.join("icons", "refresh.png"), refresh_food_list),
            (os.path.join("icons", "max.png"), find_max_nutrient_food),
            (os.path.join("icons", "min.png"), find_min_cost_per_nutrient),
            (os.path.join("icons", "diet.png"), calculate_optimal_diet),
            (os.path.join("icons", "analysis.png"), run_sensitivity_analysis),
            (os.path.join("icons", "meal.png"), calculate_weekly_menu),
            (os.path.join("icons", "cost.png"), plot_cost_vs_total_cost),
        ]

        for idx, (icon_path, cmd) in enumerate(buttons):
            row = idx // 5
            col = idx % 5
            btn = CustomButton(btn_frame, image_path=icon_path, command=cmd)
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        global status_var
        status_var = tk.StringVar()
        status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w", padding=5, background="#FFFFFF", foreground="#000000")
        status_bar.pack(side="bottom", fill="x")

        refresh_food_list()
        print("Main window setup complete")
    except Exception as e:
        print(f"Error in main window setup: {e}")
        messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εγκατάσταση: {e}\nΗ εφαρμογή θα συνεχίσει να λειτουργεί.")
        status_var.set("Σφάλμα κατά την εγκατάσταση - Επικοινωνήστε με τον διαχειριστή")

def test_tkinter():
    print("Testing Tkinter functionality")
    try:
        test_root = tk.Tk()
        test_root.title("Tkinter Test")
        test_root.geometry("200x100")
        tk.Label(test_root, text="Tkinter is working!").pack(pady=20)
        test_root.update()
        test_root.after(1000, test_root.destroy)
        test_root.mainloop()
        print("Tkinter test completed successfully")
    except Exception as e:
        print(f"Error in Tkinter test: {e}")
        raise

def confirm_exit():
    if messagebox.askyesno("Έξοδος", "Είστε σίγουροι ότι θέλετε να κλείσετε την εφαρμογή;"):
        root.quit()

def main():
    global root, tree, foods, last_selected_foods, Q_VALUES
    print("Starting main function")

    # Show splash screen before starting the main application
    show_splash_screen()

    try:
        test_tkinter()
    except Exception as e:
        print(f"Error in Tkinter test: {e}")
        messagebox.showerror("Σφάλμα", f"Αποτυχία δοκιμής Tkinter: {e}\nΗ εφαρμογή θα προσπαθήσει να συνεχίσει.")
        status_var.set("Πρόβλημα με Tkinter - Ελέγξτε την εγκατάσταση")

    root = tk.Tk()
    root.withdraw()
    print("Root window created and withdrawn")

    foods = load_foods()
    Q_VALUES = load_q_values()
    print(f"Loaded Q_VALUES at startup: {Q_VALUES}")

    try:
        setup_main_window()
    except Exception as e:
        print(f"Error setting up main window: {e}")
        messagebox.showerror("Σφάλμα", f"Αποτυχία εγκατάστασης παραθύρου: {e}\nΗ εφαρμογή θα συνεχίσει με περιορισμένη λειτουργικότητα.")
        status_var.set("Πρόβλημα με το παράθυρο - Επικοινωνήστε με τον διαχειριστή")

    root.deiconify()
    print("Main window deiconified")

    try:
        print("Starting mainloop")
        root.mainloop()
        print("Mainloop started")
    except Exception as e:
        print(f"Error in mainloop: {e}")
        messagebox.showerror("Σφάλμα", f"Απροσδόκητο σφάλμα: {e}\nΗ εφαρμογή θα παραμείνει ανοιχτή.")
        status_var.set("Απροσδόκητο σφάλμα - Επικοινωνήστε με τον διαχειριστή")

if __name__ == "__main__":
    main()
