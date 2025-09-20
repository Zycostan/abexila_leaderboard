import tkinter as tk
from tkinter import messagebox
from scraper import StoneworksDataScraper  # put your scraper class in scraper.py

def run_scraper():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a markers.json URL")
        return
    
    try:
        scraper = StoneworksDataScraper()
        scraper.markers_url = url  # override default
        scraper.run_full_scrape()
        messagebox.showinfo("Success", "Scraping completed! Files saved in current folder.")
    except Exception as e:
        messagebox.showerror("Error", f"Scraping failed: {e}")

# GUI setup
root = tk.Tk()
root.title("Stoneworks Data Scraper")

tk.Label(root, text="Enter markers.json URL:").pack(pady=5)
url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=5)
url_entry.insert(0, "https://map.stoneworks.gg/abex1/maps/abexilas/live/markers.json?331762")  # default

tk.Button(root, text="Run Scraper", command=run_scraper).pack(pady=10)

root.mainloop()
