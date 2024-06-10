import csv
import os
import tkinter as tk
from tkinter import messagebox

# Define the file name
filename = "manualValDataset.csv"

# Define the headers
headers = ["Comment", "isToxic", "Reason for Toxicity", "Context/Notes"]

def initialize_csv():
    """Function to initialize the CSV file with headers if it does not exist."""
    if not os.path.isfile(filename):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def save_data():
    """Function to save the data to the CSV file."""
    comment = entry_comment.get()
    is_toxic = var_toxic.get()
    reason_for_toxicity = entry_reason.get()
    context_notes = entry_context.get()

    # Validate inputs
    if is_toxic not in [0, 1]:
        messagebox.showerror("Input Error", "Toxic field must be 0 (No) or 1 (Yes)")
        return

    # Write the row to the CSV file
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([comment, is_toxic, reason_for_toxicity, context_notes])

    # Clear the input fields
    entry_comment.delete(0, tk.END)
    var_toxic.set(0)
    entry_reason.delete(0, tk.END)
    entry_context.delete(0, tk.END)
    messagebox.showinfo("Success", "Data saved successfully")

def count_entries():
    """Function to count the number of toxic and non-toxic entries in the CSV file."""
    toxic_count = 0
    non_toxic_count = 0

    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip headers
        for row in reader:
            if row[1] == '1':
                toxic_count += 1
            elif row[1] == '0':
                non_toxic_count += 1

    messagebox.showinfo("Entry Count", f"Toxic Entries: {toxic_count}\nNon-Toxic Entries: {non_toxic_count}")

# Initialize the CSV file
initialize_csv()

# Create the main window
root = tk.Tk()
root.title("Toxic Text Data Entry")

# Create and place the input fields
tk.Label(root, text="Comment").grid(row=0, column=0, padx=10, pady=5)
entry_comment = tk.Entry(root, width=50)
entry_comment.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="isToxic (0/1)").grid(row=1, column=0, padx=10, pady=5)
var_toxic = tk.IntVar()
tk.Radiobutton(root, text="0 (No)", variable=var_toxic, value=0).grid(row=1, column=1, sticky='w', padx=10)
tk.Radiobutton(root, text="1 (Yes)", variable=var_toxic, value=1).grid(row=1, column=1, sticky='e', padx=10)

tk.Label(root, text="Reason for Toxicity").grid(row=2, column=0, padx=10, pady=5)
entry_reason = tk.Entry(root, width=50)
entry_reason.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Context/Notes").grid(row=3, column=0, padx=10, pady=5)
entry_context = tk.Entry(root, width=50)
entry_context.grid(row=3, column=1, padx=10, pady=5)

# Create and place the Save button
tk.Button(root, text="Save", command=save_data).grid(row=4, column=0, columnspan=2, pady=10)

# Create and place the Count button
tk.Button(root, text="Count Entries", command=count_entries).grid(row=5, column=0, columnspan=2, pady=10)

# Start the main event loop
root.mainloop()

# Data was extracted from Facebook posts, Love Island posts, Boxing controversies, and MaltaDaily comments.
