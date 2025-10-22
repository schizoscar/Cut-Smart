import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
import math

def apply_global_styles(root):
    root.title("Steel Sheet Calculation")
    root.state("zoomed")
    root.configure(bg="#FAF9F6")

    button_font = ("System", 14)
    label_font = ("System", 12)
    entry_font = ("System", 12)

    accent_blue = "#A2D5F2"
    hover_color = "#D6EAF8"
    accent_purple = "#C3B1E1"
    unseen_logs_color = "#FF6F61"
    entry_bg = "#FAF9F6"
    entry_fg = "black"
    label_fg = "#1F3B4D"
    entry_border = "#A2D5F2"

    root.option_add("*Button.Font", button_font)
    root.option_add("*Button.Background", accent_blue)
    root.option_add("*Button.Foreground", "#1F3B4D")
    root.option_add("*Button.activeBackground", hover_color)
    root.option_add("*Button.activeForeground", "#FAF9F6")
    root.option_add("*Button.relief", "raised")
    root.option_add("*Button.borderWidth", 2)
    root.option_add("*Button.padX", 10)
    root.option_add("*Button.padY", 5)
    root.option_add("*Label.Font", label_font)
    root.option_add("*Label.Background", "#FAF9F6")
    root.option_add("*Label.Foreground", label_fg)
    root.option_add("*Entry.Font", entry_font)
    root.option_add("*Entry.Background", entry_bg)
    root.option_add("*Entry.Foreground", entry_fg)
    root.option_add("*Entry.borderWidth", 1)
    root.option_add("*Entry.highlightThickness", 1)
    root.option_add("*Entry.highlightBackground", entry_border)
    root.option_add("*Entry.highlightColor", entry_border)
    root.option_add("*Button.anchor", "center")
    root.option_add("*Label.anchor", "w")

    def on_hover(event):
        if event.widget.cget("bg") != unseen_logs_color:
            event.widget.config(bg=hover_color)

    def on_leave(event):
        if event.widget.cget("bg") != unseen_logs_color:
            event.widget.config(bg=accent_blue)

    def on_click(event):
        if event.widget.cget("bg") != unseen_logs_color:
            event.widget.config(bg=accent_purple)
        event.widget.invoke()

    root.bind_class("Button", "<Enter>", on_hover)
    root.bind_class("Button", "<Leave>", on_leave)
    root.bind_class("Button", "<Button-1>", on_click)

def calculate_layouts(parts, sheet_sizes, mix_parts):
    results = []
    if mix_parts:
        # Mixed parts mode - use improved bin packing algorithm
        mixed_results = []
        
        for sheet_w, sheet_h in sheet_sizes:
            # Use improved bin packing to calculate actual layout
            packing_result = pack_mixed_parts(parts, sheet_w, sheet_h)
            
            if packing_result:
                needed_sheets = packing_result['needed_sheets']
                wastage_area = packing_result['wastage_area']
                layouts = packing_result['layouts']
                
                mixed_layout = {
                    'sheet_w': sheet_w,
                    'sheet_h': sheet_h,
                    'needed_sheets': needed_sheets,
                    'wastage_area': wastage_area,
                    'parts': parts,
                    'layouts': layouts,  # Store actual packing layouts
                    'total_area_needed': sum([p[0] * p[1] * p[3] for p in parts])
                }
                mixed_results.append(mixed_layout)
        
        return mixed_results
    else:
        # Individual parts mode (original code)
        for part in parts:
            width, height, thickness, qty = part
            best_fit = []
            for sheet_w, sheet_h in sheet_sizes:
                across = math.floor(sheet_w / width)
                down = math.floor(sheet_h / height)
                pieces_per_sheet = across * down
                if pieces_per_sheet == 0:
                    continue
                needed_sheets = math.ceil(qty / pieces_per_sheet)
                total_area = sheet_w * sheet_h * needed_sheets
                used_area = width * height * qty
                wastage_area = total_area - used_area
                best_fit.append((sheet_w, sheet_h, across, down, needed_sheets, wastage_area))
            results.append((width, height, thickness, qty, best_fit))
        return results

def pack_mixed_parts(parts, sheet_w, sheet_h):
    """
    Improved mixed parts packing that prioritizes keeping same-sized pieces together
    and ensures tight packing without gaps between parts
    """
    # Convert to integers
    sheet_w = int(sheet_w)
    sheet_h = int(sheet_h)
    
    # First, calculate optimal orientation and packing for each part type
    part_data = []
    
    for part_idx, (width, height, thickness, qty) in enumerate(parts):
        width = int(width)
        height = int(height)
        
        best_orientation = None
        best_pieces_per_sheet = 0
        best_across = 0
        best_down = 0
        
        # Find best orientation
        for orientation in [(width, height), (height, width)]:
            part_w, part_h = orientation
            
            if part_w > sheet_w or part_h > sheet_h:
                continue
            
            across = math.floor(sheet_w / part_w)
            down = math.floor(sheet_h / part_h)
            pieces_per_sheet = across * down
            
            if pieces_per_sheet > best_pieces_per_sheet:
                best_pieces_per_sheet = pieces_per_sheet
                best_orientation = (part_w, part_h)
                best_across = across
                best_down = down
        
        if best_orientation:
            part_w, part_h = best_orientation
            part_data.append({
                'part_idx': part_idx,
                'width': width,
                'height': height,
                'thickness': thickness,
                'qty': qty,
                'pack_width': part_w,
                'pack_height': part_h,
                'across': best_across,
                'down': best_down,
                'pieces_per_sheet': best_pieces_per_sheet,
                'area': part_w * part_h
            })
    
    if not part_data:
        return None
    
    # Sort parts by area (largest first) for better packing
    part_data.sort(key=lambda x: x['area'], reverse=True)
    
    all_sheets = []
    remaining_parts = {part['part_idx']: part['qty'] for part in part_data}
    
    # First pass: Create dedicated sheets for each part type to ensure same parts stay together
    for part in part_data:
        part_idx = part['part_idx']
        part_w = part['pack_width']
        part_h = part['pack_height']
        across = part['across']
        down = part['down']
        pieces_per_sheet = part['pieces_per_sheet']
        
        # Calculate how many full sheets we need for this part
        full_sheets_needed = remaining_parts[part_idx] // pieces_per_sheet
        
        # Create full sheets dedicated to this part
        for _ in range(full_sheets_needed):
            sheet = {
                'parts_placed': [],
                'used_area': 0,
                'primary_part': part_idx
            }
            
            # Fill the entire sheet with this part type in grid layout
            for i in range(pieces_per_sheet):
                row = i // across
                col = i % across
                x = col * part_w
                y = row * part_h
                
                sheet['parts_placed'].append({
                    'x': int(x), 'y': int(y), 'width': int(part_w), 'height': int(part_h),
                    'original_width': part['width'], 'original_height': part['height'],
                    'thickness': part['thickness'], 'part_idx': part_idx
                })
                sheet['used_area'] += part_w * part_h
            
            remaining_parts[part_idx] -= pieces_per_sheet
            all_sheets.append(sheet)
    
    # Second pass: Create mixed sheets with tight packing
    while any(remaining_parts[part_idx] > 0 for part_idx in remaining_parts):
        # Create a new sheet
        new_sheet = {
            'parts_placed': [],
            'used_area': 0,
            'primary_part': None
        }
        
        # Try to pack parts tightly using bottom-left packing strategy
        changed = True
        while changed and any(remaining_parts[part_idx] > 0 for part_idx in remaining_parts):
            changed = False
            
            # Try each part type in order of size (largest first)
            for part in part_data:
                part_idx = part['part_idx']
                
                if remaining_parts[part_idx] <= 0:
                    continue
                
                # Try both orientations
                for orientation in [(part['pack_width'], part['pack_height']), 
                                   (part['pack_height'], part['pack_width'])]:
                    part_w, part_h = orientation
                    
                    if part_w > sheet_w or part_h > sheet_h:
                        continue
                    
                    # Find the best position using bottom-left packing
                    best_position = find_tight_packing_position(new_sheet, part_w, part_h, sheet_w, sheet_h)
                    
                    if best_position:
                        x, y = best_position
                        new_sheet['parts_placed'].append({
                            'x': int(x), 'y': int(y), 'width': int(part_w), 'height': int(part_h),
                            'original_width': part['width'], 'original_height': part['height'],
                            'thickness': part['thickness'], 'part_idx': part_idx
                        })
                        new_sheet['used_area'] += part_w * part_h
                        remaining_parts[part_idx] -= 1
                        changed = True
                        break  # Break orientation loop
                
                if changed:
                    break  # Break part loop if we placed something
        
        # If we managed to place at least one part, add the sheet
        if new_sheet['parts_placed']:
            # Determine primary part for this sheet
            part_counts = {}
            for placement in new_sheet['parts_placed']:
                part_idx = placement['part_idx']
                part_counts[part_idx] = part_counts.get(part_idx, 0) + 1
            
            if part_counts:
                new_sheet['primary_part'] = max(part_counts.items(), key=lambda x: x[1])[0]
            
            all_sheets.append(new_sheet)
        else:
            # If we can't place anything, break to avoid infinite loop
            break
    
    # Calculate total metrics
    total_sheets = len(all_sheets)
    total_sheet_area = total_sheets * sheet_w * sheet_h
    total_used_area = sum(sheet['used_area'] for sheet in all_sheets)
    wastage_area = total_sheet_area - total_used_area
    
    return {
        'needed_sheets': total_sheets,
        'wastage_area': wastage_area,
        'layouts': all_sheets
    }

def find_tight_packing_position(sheet, part_w, part_h, sheet_w, sheet_h):
    """
    Find the best position for tight packing using bottom-left strategy
    Returns position where the part touches existing parts or boundaries
    """
    placed_parts = sheet['parts_placed']
    
    # If sheet is empty, place at bottom-left
    if not placed_parts:
        return (0, 0)
    
    # Generate candidate positions along the edges of existing parts
    candidate_positions = []
    
    # Consider positions along the top and right edges of all placed parts
    for placed in placed_parts:
        # Right edge positions
        candidate_positions.append((placed['x'] + placed['width'], placed['y']))
        candidate_positions.append((placed['x'] + placed['width'], placed['y'] + placed['height'] - part_h))
        
        # Top edge positions
        candidate_positions.append((placed['x'], placed['y'] + placed['height']))
        candidate_positions.append((placed['x'] + placed['width'] - part_w, placed['y'] + placed['height']))
    
    # Also consider bottom-left corner and positions along sheet boundaries
    candidate_positions.append((0, 0))
    
    # Add positions along the top boundary of the sheet
    max_y = max([p['y'] + p['height'] for p in placed_parts], default=0)
    if max_y + part_h <= sheet_h:
        for x in range(0, sheet_w - part_w + 1, max(1, part_w // 2)):
            candidate_positions.append((x, max_y))
    
    # Add positions along the right boundary of the sheet  
    max_x = max([p['x'] + p['width'] for p in placed_parts], default=0)
    if max_x + part_w <= sheet_w:
        for y in range(0, sheet_h - part_h + 1, max(1, part_h // 2)):
            candidate_positions.append((max_x, y))
    
    # Remove duplicates and invalid positions
    candidate_positions = list(set(candidate_positions))
    valid_candidates = []
    
    for x, y in candidate_positions:
        # Check if position is within sheet boundaries
        if x < 0 or y < 0 or x + part_w > sheet_w or y + part_h > sheet_h:
            continue
        
        # Check for overlaps with existing parts
        overlap = False
        for placed in placed_parts:
            if (x < placed['x'] + placed['width'] and 
                x + part_w > placed['x'] and 
                y < placed['y'] + placed['height'] and 
                y + part_h > placed['y']):
                overlap = True
                break
        
        if not overlap:
            valid_candidates.append((x, y))
    
    if not valid_candidates:
        return None
    
    # Sort candidates by Y then X (bottom-left packing)
    valid_candidates.sort(key=lambda pos: (pos[1], pos[0]))
    
    # Return the best candidate (lowest Y, then lowest X)
    return valid_candidates[0]

def find_space_for_part_in_grid(sheet, part_w, part_h, across, down, sheet_w, sheet_h):
    """
    Find space for a part in a grid layout (for same part types)
    """
    placed_positions = [(p['x'], p['y']) for p in sheet['parts_placed']]
    
    for row in range(down):
        for col in range(across):
            x = col * part_w
            y = row * part_h
            
            # Check if this grid position is empty
            if (x, y) not in placed_positions:
                # Check if it fits without overlapping
                if x + part_w <= sheet_w and y + part_h <= sheet_h:
                    overlap = False
                    for placed in sheet['parts_placed']:
                        px, py = placed['x'], placed['y']
                        pw, ph = placed['width'], placed['height']
                        
                        if not (x + part_w <= px or x >= px + pw or y + part_h <= py or y >= py + ph):
                            overlap = True
                            break
                    
                    if not overlap:
                        return (x, y)
    
    return None

def find_space_for_part(sheet, part_w, part_h, sheet_w, sheet_h):
    """
    Find space for an additional part on a partially filled sheet
    """
    placed_parts = sheet['parts_placed']
    
    # Try bottom-left packing strategy
    for y in range(0, sheet_h - part_h + 1, max(1, part_h // 2)):
        for x in range(0, sheet_w - part_w + 1, max(1, part_w // 2)):
            overlap = False
            for placed in placed_parts:
                px = int(placed['x'])
                py = int(placed['y'])
                pw = int(placed['width'])
                ph = int(placed['height'])
                
                if not (x + part_w <= px or x >= px + pw or y + part_h <= py or y >= py + ph):
                    overlap = True
                    break
            
            if not overlap:
                return (x, y)
    
    return None

def draw_layout(ax, width, height, thickness, qty, layout):
    sheet_w, sheet_h, across, down, needed_sheets, wastage_area = layout
    ax.set_aspect('equal')
    ax.set_xlim(0, sheet_w)
    ax.set_ylim(0, sheet_h)
    ax.set_title(f"{sheet_w}×{sheet_h} mm | Wastage: {int(wastage_area)} mm²")
    for i in range(across):
        for j in range(down):
            ax.add_patch(plt.Rectangle((i*width, j*height), width, height, fill=False, color='black', linewidth=0.5))
    ax.text(sheet_w/2, -height*0.3, f"{width}×{height}×{thickness} mm × {qty} nos", ha='center', va='top')

def generate_pdf(all_layouts):
    pdf = FPDF("L", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    counter = 0
    for layout in all_layouts:
        if counter % 4 == 0:
            pdf.add_page()
        fig, ax = plt.subplots(figsize=(8.27, 5.8))
        draw_layout(ax, *layout)
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        fig.savefig("temp.png", dpi=200)
        plt.close(fig)
        pdf.image("temp.png", x=10 + (counter % 2) * 140, y=20 + ((counter // 2) % 2) * 100, w=130)
        counter += 1
    pdf.output("SheetCalculation_Output.pdf")
    messagebox.showinfo("Export Complete", "Saved as SheetCalculation_Output.pdf")

class SheetCalculationApp:
    def __init__(self, root):
        self.root = root
        # Set window icon/logo
        try:
            self.root.iconbitmap("logo.png")  

        except:
            print("Logo file not found, running without logo")

        apply_global_styles(root)
        self.parts = []
        self.current_index = 0
        self.layouts = []
        self.sheet_sizes = [(3000, 1500), (2500, 1250), (2400, 1200)]
        self.mix_parts = tk.BooleanVar()
        self.build_home()

    def build_home(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, bg="#FAF9F6")
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="Steel Plate Cutting Calculator", font=("System", 18, "bold")).pack(pady=20)
        self.part_frame = tk.Frame(main_frame, bg="#FAF9F6")
        self.part_frame.pack(pady=10, fill="x")

        self.part_entries = []
        self.add_part_row()

        tk.Button(main_frame, text="Add Another Size", command=self.add_part_row).pack(pady=10)
        tk.Checkbutton(main_frame, text="Mix different dimensions on the same sheet", variable=self.mix_parts, bg="#FAF9F6").pack()

        tk.Label(main_frame, text="Standard Sheet Sizes (mm)", font=("System", 14, "bold")).pack(pady=(20, 5))
    
        # Create a frame for the table to control its width
        table_frame = tk.Frame(main_frame, bg="#FAF9F6")
        table_frame.pack(pady=10)
    
        self.table = ttk.Treeview(table_frame, columns=("Width", "Height"), show="headings", height=5)
        self.table.heading("Width", text="Width (mm)")
        self.table.heading("Height", text="Height (mm)")
    
        # Configure column widths to be smaller
        self.table.column("Width", width=100, anchor="center")
        self.table.column("Height", width=100, anchor="center")
    
        self.table.pack()
    
        # Bind events for editing
        self.table.bind('<<TreeviewSelect>>', self.on_table_edit)
        self.table.bind('<FocusOut>', self.on_table_edit)
        self.table.bind('<Return>', self.on_table_edit)
    
        # Load saved sheet sizes
        self.load_sheet_sizes()
    
        btn_frame = tk.Frame(main_frame, bg="#FAF9F6")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Add", command=self.add_sheet_row).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_sheet_row).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Revert to Default", command=self.reset_default_sheets).grid(row=0, column=2, padx=5)
        tk.Button(main_frame, text="Calculate", command=self.show_layouts).pack(pady=20)

    def add_part_row(self):
        row = tk.Frame(self.part_frame, bg="#FAF9F6")
        row.pack(pady=5, anchor="center")

        w = tk.Entry(row, width=10, justify="center")
        h = tk.Entry(row, width=10, justify="center")
        t = tk.Entry(row, width=10, justify="center")
        q = tk.Entry(row, width=10, justify="center")

        tk.Label(row, text="Width (mm):").grid(row=0, column=0, padx=5)
        w.grid(row=0, column=1, padx=5)
        tk.Label(row, text="Height (mm):").grid(row=0, column=2, padx=5)
        h.grid(row=0, column=3, padx=5)
        tk.Label(row, text="Thickness (mm):").grid(row=0, column=4, padx=5)
        t.grid(row=0, column=5, padx=5)
        tk.Label(row, text="Quantity (nos):").grid(row=0, column=6, padx=5)
        q.grid(row=0, column=7, padx=5)

        delete_btn = tk.Button(row, text="Delete", command=lambda r=row: self.delete_part_row(r))
        delete_btn.grid(row=0, column=8, padx=10)

        self.part_entries.append((w, h, t, q, row, delete_btn))

        if len(self.part_entries) == 1:
            delete_btn.grid_remove()

    def add_sheet_row(self):
        """Add a new editable sheet size row (numeric-only validation on edit)."""
        new_item = self.table.insert("", "end", values=("", ""))
        self.table.focus(new_item)
        self.table.selection_set(new_item)

        # Bind double-click editing if not already bound
        if not hasattr(self, "_edit_binding_set"):
            self.table.bind("<Double-1>", self.edit_sheet_cell)
            self._edit_binding_set = True


    def edit_sheet_cell(self, event):
        """Allow numeric-only editing for sheet size cells."""
        region = self.table.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.table.identify_row(event.y)
        col_id = self.table.identify_column(event.x)
        if not row_id or not col_id:
            return

        x, y, width, height = self.table.bbox(row_id, col_id)
        column_index = int(col_id.replace("#", "")) - 1
        old_values = list(self.table.item(row_id, "values"))
        old_value = old_values[column_index]

        # Create entry overlay for editing
        entry = tk.Entry(self.table, justify="center")
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, old_value)
        entry.focus()

        def validate_and_save(event=None):
            new_value = entry.get().strip()
            if not new_value.replace('.', '', 1).isdigit():
                tk.messagebox.showerror("Invalid Input", "Please enter a valid number.")
                entry.focus()
                return

            # Save new value and update JSON
            old_values[column_index] = new_value
            self.table.item(row_id, values=old_values)
            entry.destroy()
            self.save_sheet_sizes()

        entry.bind("<Return>", validate_and_save)
        entry.bind("<FocusOut>", lambda e: entry.destroy())


    def on_table_edit(self, event):
        """Handle when user finishes editing a cell"""
        # Save the sheet sizes after a brief delay to ensure the edit is complete
        self.root.after(100, self.save_sheet_sizes)

    def delete_part_row(self, row):
        # Find and remove the entry from part_entries
        for i, (w, h, t, q, r, btn) in enumerate(self.part_entries):
            if r == row:
                self.part_entries.pop(i)
                break
    
        # Destroy the row
        row.destroy()
    
        # Ensure at least one row remains and update delete button visibility
        if len(self.part_entries) == 1:
            # Hide delete button for the first row
            w, h, t, q, r, btn = self.part_entries[0]
            btn.grid_remove()  # Changed from pack_forget to grid_remove

    def delete_sheet_row(self):
        selected = self.table.selection()
        for sel in selected:
            self.table.delete(sel)
        self.save_sheet_sizes()  # Auto-save after deletion

    def reset_default_sheets(self):
        for i in self.table.get_children():
            self.table.delete(i)
        self.sheet_sizes = [(3000, 1500), (2500, 1250), (2400, 1200)]
        for s in self.sheet_sizes:
            self.table.insert("", "end", values=s)
        self.save_sheet_sizes()  # Auto-save after reset

    def load_sheet_sizes(self):
        """Load saved sheet sizes from file"""
        try:
            import json
            import os
        
            config_file = os.path.join(os.path.expanduser("~/.steel_calculator"), "sheet_sizes.json")
        
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_sizes = json.load(f)
            
                # Clear current table and load saved sizes
                for i in self.table.get_children():
                    self.table.delete(i)
            
                for size in saved_sizes:
                    if len(size) >= 2:
                        self.table.insert("", "end", values=(size[0], size[1]))
            
                # Update the internal sheet_sizes list
                self.sheet_sizes = [(size[0], size[1]) for size in saved_sizes if len(size) >= 2]
            else:
                # Load default sizes if no saved file exists
                for s in self.sheet_sizes:
                    self.table.insert("", "end", values=s)
                
        except Exception as e:
            print(f"Error loading sheet sizes: {e}")
            # Load default sizes if error occurs
            for s in self.sheet_sizes:
                self.table.insert("", "end", values=s)

    def save_sheet_sizes(self):
        """Save current sheet sizes to a file, only saving valid numerical values"""
        try:
            sheet_sizes = []
            for i in self.table.get_children():
                values = self.table.item(i, "values")
                if values and len(values) >= 2:
                    try:
                        width = float(values[0])
                        height = float(values[1])
                        if width > 0 and height > 0:
                            sheet_sizes.append((width, height))
                    except ValueError:
                        continue  # Skip invalid entries
        
            # Only save if we have valid sizes
            if sheet_sizes:
                import json
                import os
            
                # Save to user's home directory
                config_dir = os.path.expanduser("~/.steel_calculator")
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, "sheet_sizes.json")
            
                with open(config_file, 'w') as f:
                    json.dump(sheet_sizes, f)
            
                # Update internal sheet_sizes
                self.sheet_sizes = sheet_sizes
            
        except Exception as e:
            print(f"Error saving sheet sizes: {e}")

    def show_layouts(self):
        parts = []
        for w, h, t, q, row, btn in self.part_entries:
            try:
                width = float(w.get())
                height = float(h.get())
                thickness = float(t.get())
                qty = int(q.get())
                if width > 0 and height > 0 and thickness > 0 and qty > 0:
                    parts.append((width, height, thickness, qty))
                else:
                    messagebox.showerror("Invalid Input", "Please enter positive values for all fields.")
                    return
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid dimensions, thickness, and quantity.")
                return

        if not parts:
            messagebox.showerror("Invalid Input", "Please enter at least one part.")
            return

        # Get sheet sizes directly from the table and validate
        self.sheet_sizes = []
        for i in self.table.get_children():
            values = self.table.item(i, "values")
            if values and len(values) >= 2:
                try:
                    sheet_w = float(values[0])
                    sheet_h = float(values[1])
                    if sheet_w > 0 and sheet_h > 0:
                        self.sheet_sizes.append((sheet_w, sheet_h))
                except ValueError:
                    continue

        if not self.sheet_sizes:
            messagebox.showerror("Invalid Input", "Please enter valid sheet sizes.")
            return

        self.layouts = calculate_layouts(parts, self.sheet_sizes, self.mix_parts.get())
        self.current_index = 0
        self.display_layout()

    def display_layout(self):
        # Remove any previous result frame
        if hasattr(self, "result_frame") and self.result_frame:
            self.result_frame.destroy()

        # Main result frame
        self.result_frame = tk.Frame(self.root, bg="#FAF9F6")
        self.result_frame.pack(expand=True, fill="both")

        # Handle mixed parts
        if self.mix_parts.get():
            if not self.layouts:
                messagebox.showerror("No Results", "No suitable sheet layouts found for the mixed parts.")
                return
            self.display_mixed_layout(self.layouts)
            return

        if not self.layouts:
            messagebox.showerror("No Results", "No suitable sheet layouts found.")
            return

        # === Main container ===
        main_container = tk.Frame(self.result_frame, bg="#FAF9F6")
        main_container.pack(expand=True, fill="both")
    
        # === Title ===
        title_frame = tk.Frame(main_container, bg="#FAF9F6")
        title_frame.pack(fill="x", pady=(20, 30))
        tk.Label(
            title_frame,
            text="Layout Options",
            font=("System", 20, "bold"),
            bg="#FAF9F6"
        ).pack(anchor="center")

        # === Simple scrollable frame ===
        canvas = tk.Canvas(main_container, bg="#FAF9F6", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar_y.set)

        # Layout canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=100)  # Equal padding on both sides
        scrollbar_y.pack(side="right", fill="y")

        # === Scrollable frame ===
        scrollable_frame = tk.Frame(canvas, bg="#FAF9F6")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="n")

        def configure_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Center the content by setting the window width to match canvas
            canvas_width = event.width
            canvas.itemconfig(canvas.find_all()[0], width=canvas_width)

        canvas.bind("<Configure>", configure_scrollregion)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # === Center container for all content ===
        center_container = tk.Frame(scrollable_frame, bg="#FAF9F6")
        center_container.pack(expand=True, fill="both")

        # === Layout entries ===
        for part_idx, layout_data in enumerate(self.layouts):
            width, height, thickness, qty, best_fits = layout_data
            if not best_fits:
                continue

            # Create container for each part
            part_container = tk.Frame(center_container, bg="#FAF9F6")
            part_container.pack(fill="x", pady=25)

            part_frame = tk.Frame(part_container, bg="#FAF9F6", relief="groove", bd=2)
            part_frame.pack(anchor="center", padx=20, pady=10, ipadx=30, ipady=20)

            part_info = f"Part {part_idx + 1}: {width}×{height}×{thickness}mm - {qty}nos"
            tk.Label(
                part_frame,
                text=part_info,
                font=("System", 16, "bold"),
                bg="#FAF9F6"
            ).pack(pady=15, anchor="center")

            smallest_sheet = min(best_fits, key=lambda x: x[0] * x[1])
            least_wastage = min(best_fits, key=lambda x: x[5])
        
            # Format wastage with commas
            smallest_wastage_formatted = "{:,}".format(int(smallest_sheet[5]))
            least_wastage_formatted = "{:,}".format(int(least_wastage[5]))

            tk.Label(
                part_frame,
                text="Select Layout to View",
                font=("System", 14, "bold"),
                bg="#FAF9F6"
            ).pack(pady=15, anchor="center")

            # Button container
            btn_container = tk.Frame(part_frame, bg="#FAF9F6")
            btn_container.pack(pady=20)

            smallest_btn = tk.Button(
                btn_container,
                text=f"Smallest Sheet Fit\n{int(smallest_sheet[0])}×{int(smallest_sheet[1])}mm\nWastage: {smallest_wastage_formatted} mm²",
                command=lambda w=width, h=height, t=thickness, q=qty, l=smallest_sheet, idx=part_idx:
                    self.show_drawing_window(w, h, t, q, l, f"Part{idx+1}_Smallest"),
                font=("System", 12),
                width=40,
                height=2
            )
            smallest_btn.pack(side="left", padx=40)

            least_btn = tk.Button(
                btn_container,
                text=f"Least Wastage\n{int(least_wastage[0])}×{int(least_wastage[1])}mm\nWastage: {least_wastage_formatted} mm²",
                command=lambda w=width, h=height, t=thickness, q=qty, l=least_wastage, idx=part_idx:
                    self.show_drawing_window(w, h, t, q, l, f"Part{idx+1}_LeastWastage"),
                font=("System", 12),
                width=40,
                height=2
            )
            least_btn.pack(side="left", padx=40)

    def display_mixed_layout(self, mixed_layouts):
        # Create main container
        main_container = tk.Frame(self.result_frame, bg="#FAF9F6")
        main_container.pack(expand=True, fill="both")
    
        # Title - centered at the top
        title_frame = tk.Frame(main_container, bg="#FAF9F6")
        title_frame.pack(fill="x", pady=(20, 30))
        tk.Label(
            title_frame, 
            text="Mixed Parts Layout Options", 
            font=("System", 20, "bold"), 
            bg="#FAF9F6"
        ).pack(anchor="center")

        # Create a simple scrollable frame
        canvas = tk.Canvas(main_container, bg="#FAF9F6", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Layout canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=100)  # Equal padding on both sides
        scrollbar.pack(side="right", fill="y")

        # Create scrollable frame
        scrollable_frame = tk.Frame(canvas, bg="#FAF9F6")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="n")

        def configure_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Center the content by setting the window width to match canvas
            canvas_width = event.width
            canvas.itemconfig(canvas.find_all()[0], width=canvas_width)

        canvas.bind("<Configure>", configure_scrollregion)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Center container for all buttons
        center_container = tk.Frame(scrollable_frame, bg="#FAF9F6")
        center_container.pack(expand=True, fill="both")

        # mixed_layouts should be a list of dictionaries
        for layout in mixed_layouts:
            sheet_w = layout['sheet_w']
            sheet_h = layout['sheet_h']
            needed_sheets = layout['needed_sheets']
            wastage_area = layout['wastage_area']
        
            # Format wastage with commas
            formatted_wastage = "{:,}".format(int(wastage_area))
    
            # Create each button and center it
            btn = tk.Button(
                center_container,
                text=f"Sheet {sheet_w}×{sheet_h} mm\n{needed_sheets} sheets | Total Wastage: {formatted_wastage} mm²",
                command=lambda l=layout: self.show_mixed_drawing_window(l, f"Mixed_{sheet_w}x{sheet_h}"),
                font=("System", 12),
                width=50,
                height=2
            )
            btn.pack(pady=15, anchor="center")

    def next_layout(self):
        if self.current_index < len(self.layouts) - 1:
            self.current_index += 1
            self.display_layout()

    def previous_layout(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_layout()

    def save_layout(self, layout_data):
        from tkinter import filedialog
        import io
        import os

        # Get filename from user
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile="SheetCalculation.pdf",
            title="Save PDF As"
        )

        if not filename:
            return  # User cancelled

        # Check if it's mixed layout data (list of dictionaries) or individual layout data
        if isinstance(layout_data, list) and len(layout_data) > 0 and isinstance(layout_data[0], dict):
            # Mixed layout - take the first layout for saving
            layout = layout_data[0] if layout_data else {}
            if not layout:
                messagebox.showerror("Error", "No valid mixed layout data to save.")
                return
            
            sheet_w = layout['sheet_w']
            sheet_h = layout['sheet_h']
            needed_sheets = layout['needed_sheets']
            wastage_area = layout['wastage_area']
            parts = layout['parts']

            # Create PDF for mixed layout
            pdf = FPDF("L", "mm", "A4")
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Mixed Parts Layout Summary", 0, 1, "C")
            pdf.set_font("Arial", "", 12)

            # Add parts information
            pdf.cell(0, 10, "Parts List:", 0, 1, "L")
            for i, (width, height, thickness, qty) in enumerate(parts, 1):
                pdf.cell(0, 8, f"  {i}. {width}×{height}×{thickness}mm - {qty} nos", 0, 1, "L")

            pdf.ln(5)
            pdf.cell(0, 10, f"Sheet Size: {sheet_w}×{sheet_h} mm", 0, 1, "L")
            pdf.cell(0, 10, f"Sheets Needed: {needed_sheets}", 0, 1, "L")
            pdf.cell(0, 10, f"Total Wastage: {int(wastage_area)} mm²", 0, 1, "L")

            pdf.output(filename)
            messagebox.showinfo("Save Complete", f"Mixed layout saved as {filename}")
        
        else:  # Individual layout
            # For individual layouts, we need to recreate the visualization
            width, height, thickness, qty, best_fits = layout_data
        
            if not best_fits:
                messagebox.showerror("Error", "No valid layouts to save.")
                return
        
            # Use the least wastage layout for saving
            layout = min(best_fits, key=lambda x: x[5])
            sheet_w, sheet_h, across, down, needed_sheets, wastage_area = layout
        
            # Create PDF
            pdf = FPDF("L", "mm", "A4")
            pdf.set_auto_page_break(auto=False)
        
            # Calculate pages needed
            drawings_per_page = 4
            total_pages = (needed_sheets + drawings_per_page - 1) // drawings_per_page
        
            for page_idx in range(total_pages):
                pdf.add_page()
            
                # Calculate sheets for this PDF page
                start_sheet = page_idx * drawings_per_page
                end_sheet = min((page_idx + 1) * drawings_per_page, needed_sheets)
                sheets_on_page = end_sheet - start_sheet
            
                # Determine grid layout
                if sheets_on_page == 1:
                    rows, cols = 1, 1
                    figsize = (11.69, 8.27)
                elif sheets_on_page == 2:
                    rows, cols = 1, 2
                    figsize = (11.69, 5)
                else:  # 3 or 4 sheets
                    rows, cols = 2, 2
                    figsize = (11.69, 8.27)
            
                # Create figure
                fig, axes = plt.subplots(rows, cols, figsize=figsize)
            
                # Title with wastage information
                part_title = f"{width}×{height}×{thickness}mm-{qty}nos | Total Wastage: {int(wastage_area)} mm²"
                if total_pages > 1:
                    fig.suptitle(f"{part_title} - Page {page_idx+1} of {total_pages}", fontsize=12)
                else:
                    fig.suptitle(part_title, fontsize=12)
            
                # Handle axes
                if sheets_on_page == 1:
                    axes_flat = [axes]
                elif rows == 1 and cols > 1:
                    axes_flat = [axes[0], axes[1]]
                else:
                    axes_flat = axes.flatten()
            
                # Draw each sheet
                for i, sheet_num in enumerate(range(start_sheet, end_sheet)):
                    if sheets_on_page == 1:
                        ax = axes
                    elif sheets_on_page == 2 and rows == 1:
                        ax = axes[i]
                    else:
                        ax = axes_flat[i]
                
                    # Draw the sheet
                    ax.set_aspect('equal')
                    ax.set_xlim(0, sheet_w)
                    ax.set_ylim(0, sheet_h)
                    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
                
                    # Draw sheet boundary
                    ax.add_patch(plt.Rectangle((0, 0), sheet_w, sheet_h, 
                                             fill=False, color='black', linewidth=2))
                
                    # Draw parts
                    parts_drawn = 0
                    for row in range(down):
                        for col in range(across):
                            if parts_drawn < (qty - (sheet_num * across * down)):
                                x_pos = col * width
                                y_pos = row * height
                                ax.add_patch(plt.Rectangle((x_pos, y_pos), width, height, 
                                                         fill=False, color='black', linewidth=0.5))
                                parts_drawn += 1
                
                    # Add annotations
                    annotation_spacing = sheet_h * 0.08
                    ax.text(sheet_w/2, -annotation_spacing, f"Sheet {sheet_num+1}/{needed_sheets}", 
                           ha='center', va='top', fontsize=8)
                    ax.text(sheet_w/2, -annotation_spacing * 2, f"Wastage: {int(wastage_area)} mm²", 
                           ha='center', va='top', fontsize=8)
                    ax.set_ylim(-annotation_spacing * 2.5, sheet_h * 1.02)
            
                # Hide unused subplots
                if sheets_on_page == 3:
                    axes_flat[3].set_visible(False)
            
                # Adjust layout
                plt.tight_layout(rect=[0, 0.02, 1, 0.96])
            
                # Save to temporary PNG
                temp_png = f"temp_page_{page_idx}.png"
                fig.savefig(temp_png, dpi=150, bbox_inches='tight', format='png')
                plt.close(fig)
            
                # Add PNG image to PDF
                pdf.image(temp_png, x=0, y=0, w=297, h=210)
            
                # Clean up temporary file
                try:
                    os.remove(temp_png)
                except:
                    pass
        
            pdf.output(filename)
            messagebox.showinfo("Save Complete", f"Layout saved as {filename}")

    def _create_save_function(self, total_pages, needed_sheets, drawings_per_page, sheet_w, sheet_h,
                              width, height, thickness, qty, across, down, wastage_area, title,
                              parts=None, layouts=None, is_mixed=False):
        """Create a unified save function for both individual and mixed layouts"""
        def save_current_layout():
            from tkinter import filedialog
            import os

            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile="SheetCalculation.pdf",
                title="Save PDF As"
            )

            if not filename:
                return

            # Create landscape A4 PDF
            pdf = FPDF("L", "mm", "A4")
            pdf.set_auto_page_break(auto=False)

            # Define A4 dimensions in mm
            a4_w, a4_h = 297, 210
            a4_aspect = a4_w / a4_h

            for page_idx in range(total_pages):
                pdf.add_page()

                # Determine how many sheets fit on this page
                start_sheet = page_idx * drawings_per_page
                end_sheet = min((page_idx + 1) * drawings_per_page, needed_sheets)
                count_on_page = end_sheet - start_sheet

                # Sheet aspect ratio
                sheet_aspect = sheet_w / sheet_h

                # Auto-fit layout depending on count
                if count_on_page == 1:
                    rows, cols = 1, 1
                elif count_on_page == 2:
                    rows, cols = 1, 2
                else:
                    rows, cols = 2, 2

                # Determine subplot figure size maintaining sheet proportions
                fig_w_in = 11.69  # 297 mm / 25.4
                fig_h_in = 8.27   # 210 mm / 25.4
                pdf_fig, pdf_axes = plt.subplots(rows, cols, figsize=(fig_w_in, fig_h_in))

                # Flatten axes for easier iteration
                if count_on_page > 1:
                    pdf_axes = pdf_axes.flatten()
                else:
                    pdf_axes = [pdf_axes]

                # Title text
                if is_mixed:
                    parts_info = " + ".join([f"{w}×{h}×{t}mm-{q}nos" for w, h, t, q in parts])
                    part_title = f"Mixed Parts: {parts_info}"
                else:
                    part_title = f"{width}×{height}×{thickness}mm - {qty}nos | Total Wastage: {int(wastage_area)} mm²"

                pdf_fig.suptitle(part_title, fontsize=10)

                # Draw each sheet
                for i, sheet_num in enumerate(range(start_sheet, end_sheet)):
                    ax = pdf_axes[i]
                    ax.set_aspect('equal')

                    # Define padding to match screen view
                    x_pad = sheet_w * 0.05
                    y_pad = sheet_h * 0.10

                    ax.set_xlim(-x_pad, sheet_w + x_pad)
                    ax.set_ylim(-y_pad, sheet_h + y_pad)

                    if is_mixed:
                        if sheet_num < len(layouts):
                            layout = layouts[sheet_num]
                            self._draw_single_mixed_sheet(ax, layout, sheet_num, needed_sheets, sheet_w, sheet_h, parts)
                    else:
                        self._draw_single_sheet(ax, sheet_w, sheet_h, width, height, thickness,
                                                across, down, qty, sheet_num, needed_sheets, wastage_area)

                # Hide unused subplots
                for j in range(len(pdf_axes)):
                    if j >= count_on_page:
                        pdf_axes[j].set_visible(False)

                plt.tight_layout(rect=[0, 0, 1, 0.95], pad=2.0)

                # Save as PNG at correct DPI (ensures visual match)
                temp_png = f"temp_page_{page_idx}.png"
                pdf_fig.savefig(temp_png, dpi=200, bbox_inches='tight', facecolor='white')
                plt.close(pdf_fig)

                # Load PNG dimensions to preserve ratio
                from PIL import Image
                img = Image.open(temp_png)
                img_w, img_h = img.size
                img_aspect = img_w / img_h

                # Compute correct PDF placement to avoid stretch
                if img_aspect >= a4_aspect:
                    w_mm = a4_w - 10
                    h_mm = w_mm / img_aspect
                    x = 5
                    y = (a4_h - h_mm) / 2
                else:
                    h_mm = a4_h - 10
                    w_mm = h_mm * img_aspect
                    y = 5
                    x = (a4_w - w_mm) / 2

                pdf.image(temp_png, x=x, y=y, w=w_mm, h=h_mm)
                img.close()

                os.remove(temp_png)

            pdf.output(filename)
            messagebox.showinfo("Save Complete", f"All {needed_sheets} sheet(s) saved as {filename}")

        return save_current_layout


    def _draw_single_sheet(self, ax, sheet_w, sheet_h, width, height, thickness, across, down, 
                          qty, sheet_num, needed_sheets, wastage_area):
        """Draw a single sheet for individual parts"""
        ax.set_aspect('equal')
        ax.set_xlim(0, sheet_w)
        ax.set_ylim(0, sheet_h)
    
        # Remove axis labels but keep the box
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    
        # Draw the sheet boundary (black line)
        ax.add_patch(plt.Rectangle((0, 0), sheet_w, sheet_h, 
                                 fill=False, color='black', linewidth=2))
    
        # Draw the parts (starting from bottom-left) - all black lines
        parts_drawn = 0
        for row in range(down):
            for col in range(across):
                if parts_drawn < (qty - (sheet_num * across * down)):
                    # Calculate position from bottom-left
                    x_pos = col * width
                    y_pos = row * height
                
                    # Draw the part with black lines
                    ax.add_patch(plt.Rectangle((x_pos, y_pos), width, height, 
                                             fill=False, color='black', linewidth=0.5))
                    parts_drawn += 1
    
        # Add sheet information at the bottom (outside the drawing)
        sheet_info = f"Sheet {sheet_num+1}/{needed_sheets} | {sheet_w}×{sheet_h} mm"
        wastage_info = f"Wastage: {int(wastage_area)} mm²"
        parts_per_sheet = across * down
        total_parts_this_sheet = min(parts_per_sheet, qty - (sheet_num * parts_per_sheet))
        parts_info = f"Parts: {across}×{down} = {total_parts_this_sheet} nos"
    
        # Position annotations below the sheet with proper spacing
        annotation_spacing = sheet_h * 0.08
        ax.text(sheet_w/2, -annotation_spacing, sheet_info, 
               ha='center', va='top', fontsize=9)
        ax.text(sheet_w/2, -annotation_spacing * 2, wastage_info, 
               ha='center', va='top', fontsize=9)
        ax.text(sheet_w/2, -annotation_spacing * 3, parts_info, 
               ha='center', va='top', fontsize=9)
    
        # Adjust y-limits to include annotations
        ax.set_ylim(-annotation_spacing * 3.5, sheet_h * 1.02)

    def _draw_single_mixed_sheet(self, ax, sheet_layout, sheet_num, needed_sheets, sheet_w, sheet_h, parts):
        """Draw a single sheet for mixed parts"""
        ax.set_aspect('equal')
        ax.set_xlim(0, sheet_w)
        ax.set_ylim(0, sheet_h)
    
        # Remove axis labels but keep the box
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    
        # Draw the sheet boundary (black line)
        ax.add_patch(plt.Rectangle((0, 0), sheet_w, sheet_h, 
                                 fill=False, color='black', linewidth=2))
    
        # Draw all placed parts
        colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
    
        part_counts = {}
        for placement in sheet_layout['parts_placed']:
            x, y = placement['x'], placement['y']
            width, height = placement['width'], placement['height']
            part_idx = placement['part_idx']
        
            # Count parts by type
            part_key = (placement['original_width'], placement['original_height'], placement['thickness'])
            part_counts[part_key] = part_counts.get(part_key, 0) + 1
        
            # Draw the part
            color = colors[part_idx % len(colors)]
            ax.add_patch(plt.Rectangle((x, y), width, height, 
                                     fill=False, color=color, linewidth=0.5))
    
        # Add sheet information at the bottom
        sheet_info = f"Sheet {sheet_num+1}/{needed_sheets} | {sheet_w}×{sheet_h} mm"
        wastage_info = f"Wastage: {int(sheet_w * sheet_h - sheet_layout['used_area'])} mm²"
    
        # Add parts count information
        parts_info = "Parts: "
        part_details = []
        for (w, h, t), count in part_counts.items():
            part_details.append(f"{w}×{h}×{t}mm: {count}")
        parts_info += " | ".join(part_details)
    
        # Position annotations below the sheet with proper spacing
        annotation_spacing = sheet_h * 0.08
        ax.text(sheet_w/2, -annotation_spacing, sheet_info, 
               ha='center', va='top', fontsize=8)
        ax.text(sheet_w/2, -annotation_spacing * 2, wastage_info, 
               ha='center', va='top', fontsize=8)
        ax.text(sheet_w/2, -annotation_spacing * 3, parts_info, 
               ha='center', va='top', fontsize=7)
    
        # Adjust y-limits to include annotations
        ax.set_ylim(-annotation_spacing * 4, sheet_h * 1.02)

    def show_drawing_window(self, width, height, thickness, qty, layout, title):
        # Create a new top-level window in full screen
        drawing_window = tk.Toplevel(self.root)
        drawing_window.title(f"Layout Visualization - {title}")
        drawing_window.state("zoomed")  # Full screen
        drawing_window.configure(bg="#FAF9F6")
    
        # Extract layout data
        sheet_w, sheet_h, across, down, needed_sheets, wastage_area = layout
    
        # Calculate how many pages we need (4 drawings per page max)
        drawings_per_page = 4
        total_pages = (needed_sheets + drawings_per_page - 1) // drawings_per_page
    
        # Create main container
        main_frame = tk.Frame(drawing_window, bg="#FAF9F6")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        def create_page(page_index):
            # Clear previous content
            for widget in main_frame.winfo_children():
                widget.destroy()
        
            # Create frame for plots
            plots_frame = tk.Frame(main_frame, bg="#FAF9F6")
            plots_frame.pack(fill="both", expand=True)
        
            # Calculate which sheets to show on this page
            start_sheet = page_index * drawings_per_page
            end_sheet = min((page_index + 1) * drawings_per_page, needed_sheets)
            sheets_on_this_page = end_sheet - start_sheet
        
            # Determine optimal grid layout to maximize drawing size
            if sheets_on_this_page == 1:
                rows, cols = 1, 1
                figsize = (11.69, 8.27)  # Full A4 for single sheet
            elif sheets_on_this_page == 2:
                rows, cols = 1, 2
                figsize = (11.69, 5)     # Wider for side-by-side
            elif sheets_on_this_page == 3:
                rows, cols = 2, 2
                figsize = (11.69, 8.27)  # Use 2x2 grid (one empty)
            else:  # 4 sheets
                rows, cols = 2, 2
                figsize = (11.69, 8.27)  # Full 2x2 grid
        
            # Create subplots with optimized size
            fig, axes = plt.subplots(rows, cols, figsize=figsize)
        
            # Add main title with part dimensions and total quantity
            part_title = f"{width}×{height}×{thickness}mm-{qty}nos | Total Wastage: {int(wastage_area)} mm² - {title}"
            if total_pages > 1:
                full_title = f"{part_title} - Page {page_index+1} of {total_pages} | Sheets {start_sheet+1} to {end_sheet} of {needed_sheets}"
            else:
                full_title = f"{part_title} | {needed_sheets} Sheet(s) Needed"
        
            fig.suptitle(full_title, fontsize=14, y=0.98)
        
            # Handle different axes configurations
            if sheets_on_this_page == 1:
                axes_flat = [axes]
            elif rows == 1 and cols > 1:
                axes_flat = [axes[0], axes[1]] if sheets_on_this_page == 2 else axes
            else:
                axes_flat = axes.flatten()
        
            # Draw each sheet on this page
            for i, sheet_num in enumerate(range(start_sheet, end_sheet)):
                if sheets_on_this_page == 1:
                    ax = axes
                elif sheets_on_this_page == 2 and rows == 1:
                    ax = axes[i]
                else:
                    ax = axes_flat[i]
            
                self._draw_single_sheet(ax, sheet_w, sheet_h, width, height, thickness, across, down, 
                                      qty, sheet_num, needed_sheets, wastage_area)
        
            # Hide unused subplots for 3-sheet case
            if sheets_on_this_page == 3:
                axes_flat[3].set_visible(False)
        
            # Adjust layout to maximize space usage
            if sheets_on_this_page == 1:
                plt.tight_layout(rect=[0, 0.02, 1, 0.96])
            elif sheets_on_this_page == 2:
                plt.tight_layout(rect=[0, 0.02, 1, 0.96], h_pad=3.0, w_pad=3.0)
            else:
                plt.tight_layout(rect=[0, 0.02, 1, 0.96], h_pad=2.0, w_pad=2.0)
        
            # Embed the plot in tkinter
            canvas = FigureCanvasTkAgg(fig, master=plots_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        
            # Create navigation and button frame
            nav_frame = tk.Frame(main_frame, bg="#FAF9F6")
            nav_frame.pack(pady=10)
        
            # Navigation buttons for multiple pages
            if total_pages > 1:
                nav_btn_frame = tk.Frame(nav_frame, bg="#FAF9F6")
                nav_btn_frame.pack(pady=5)
            
                tk.Button(nav_btn_frame, text="Previous Page", 
                         command=lambda: create_page(page_index - 1),
                         state="normal" if page_index > 0 else "disabled").pack(side="left", padx=5)
            
                page_label = tk.Label(nav_btn_frame, text=f"Page {page_index+1} of {total_pages}", 
                                     font=("System", 10), bg="#FAF9F6")
                page_label.pack(side="left", padx=10)
            
                tk.Button(nav_btn_frame, text="Next Page", 
                         command=lambda: create_page(page_index + 1),
                         state="normal" if page_index < total_pages - 1 else "disabled").pack(side="left", padx=5)
        
            # Action buttons
            action_frame = tk.Frame(nav_frame, bg="#FAF9F6")
            action_frame.pack(pady=5)

            # Use the unified save function
            save_func = self._create_save_function(
                total_pages, needed_sheets, drawings_per_page, sheet_w, sheet_h,
                width, height, thickness, qty, across, down, wastage_area, title,
                is_mixed=False
            )
        
            tk.Button(action_frame, text="Save All as PDF", command=save_func).pack(side="left", padx=10)
            tk.Button(action_frame, text="Close", command=drawing_window.destroy).pack(side="left", padx=10)
        
            return fig
    
        # Initialize with first page
        current_fig = create_page(0)
    
        def on_close():
            plt.close(current_fig)
            drawing_window.destroy()
    
        drawing_window.protocol("WM_DELETE_WINDOW", on_close)

    def show_mixed_drawing_window(self, layout_data, title):
        # Create a new top-level window in full screen
        drawing_window = tk.Toplevel(self.root)
        drawing_window.title(f"Mixed Layout Visualization - {title}")
        drawing_window.state("zoomed")
        drawing_window.configure(bg="#FAF9F6")
    
        # Extract mixed layout data
        sheet_w = layout_data['sheet_w']
        sheet_h = layout_data['sheet_h']
        needed_sheets = layout_data['needed_sheets']
        wastage_area = layout_data['wastage_area']
        parts = layout_data['parts']
        layouts = layout_data.get('layouts', [])
    
        # Calculate how many pages we need (4 drawings per page max)
        drawings_per_page = 4
        total_pages = (needed_sheets + drawings_per_page - 1) // drawings_per_page
    
        # Create main container
        main_frame = tk.Frame(drawing_window, bg="#FAF9F6")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        def create_page(page_index):
            # Clear previous content
            for widget in main_frame.winfo_children():
                widget.destroy()
        
            # Create frame for plots
            plots_frame = tk.Frame(main_frame, bg="#FAF9F6")
            plots_frame.pack(fill="both", expand=True)
        
            # Calculate which sheets to show on this page
            start_sheet = page_index * drawings_per_page
            end_sheet = min((page_index + 1) * drawings_per_page, needed_sheets)
            sheets_on_this_page = end_sheet - start_sheet
        
            # Determine optimal grid layout to maximize drawing size
            if sheets_on_this_page == 1:
                rows, cols = 1, 1
                figsize = (11.69, 8.27)
            elif sheets_on_this_page == 2:
                rows, cols = 1, 2
                figsize = (11.69, 5)
            elif sheets_on_this_page == 3:
                rows, cols = 2, 2
                figsize = (11.69, 8.27)
            else:  # 4 sheets
                rows, cols = 2, 2
                figsize = (11.69, 8.27)
        
            # Create subplots with optimized size
            fig, axes = plt.subplots(rows, cols, figsize=figsize)
        
            # Add main title with all parts information
            parts_info = " + ".join([f"{w}×{h}×{t}mm-{q}nos" for w, h, t, q in parts])
            part_title = f"Mixed Parts: {parts_info} | Total Wastage: {int(wastage_area)} mm²"
            if total_pages > 1:
                full_title = f"{part_title} - Page {page_index+1} of {total_pages} | Sheets {start_sheet+1} to {end_sheet} of {needed_sheets}"
            else:
                full_title = f"{part_title} | {needed_sheets} Sheet(s) Needed"
        
            fig.suptitle(full_title, fontsize=12, y=0.98)
        
            # Handle different axes configurations
            if sheets_on_this_page == 1:
                axes_flat = [axes]
            elif rows == 1 and cols > 1:
                axes_flat = [axes[0], axes[1]] if sheets_on_this_page == 2 else axes
            else:
                axes_flat = axes.flatten()
        
            # Draw each sheet on this page
            for i, sheet_num in enumerate(range(start_sheet, end_sheet)):
                if sheets_on_this_page == 1:
                    ax = axes
                elif sheets_on_this_page == 2 and rows == 1:
                    ax = axes[i]
                else:
                    ax = axes_flat[i]
            
                if sheet_num < len(layouts):
                    self._draw_single_mixed_sheet(ax, layouts[sheet_num], sheet_num, needed_sheets, sheet_w, sheet_h, parts)
        
            # Hide unused subplots for 3-sheet case
            if sheets_on_this_page == 3:
                axes_flat[3].set_visible(False)
        
            # Adjust layout
            plt.tight_layout(rect=[0, 0.02, 1, 0.96])
        
            # Embed the plot in tkinter
            canvas = FigureCanvasTkAgg(fig, master=plots_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        
            # Create navigation and button frame
            nav_frame = tk.Frame(main_frame, bg="#FAF9F6")
            nav_frame.pack(pady=10)
        
            # Navigation buttons for multiple pages
            if total_pages > 1:
                nav_btn_frame = tk.Frame(nav_frame, bg="#FAF9F6")
                nav_btn_frame.pack(pady=5)
            
                tk.Button(nav_btn_frame, text="Previous Page", 
                         command=lambda: create_page(page_index - 1),
                         state="normal" if page_index > 0 else "disabled").pack(side="left", padx=5)
            
                page_label = tk.Label(nav_btn_frame, text=f"Page {page_index+1} of {total_pages}", 
                                     font=("System", 10), bg="#FAF9F6")
                page_label.pack(side="left", padx=10)
            
                tk.Button(nav_btn_frame, text="Next Page", 
                         command=lambda: create_page(page_index + 1),
                         state="normal" if page_index < total_pages - 1 else "disabled").pack(side="left", padx=5)
        
            # Action buttons
            action_frame = tk.Frame(nav_frame, bg="#FAF9F6")
            action_frame.pack(pady=5)
        
            # Use the unified save function
            save_func = self._create_save_function(
                total_pages, needed_sheets, drawings_per_page, sheet_w, sheet_h,
                None, None, None, None, None, None, wastage_area, title,
                parts=parts, layouts=layouts, is_mixed=True
            )
        
            tk.Button(action_frame, text="Save All as PDF", command=save_func).pack(side="left", padx=10)
            tk.Button(action_frame, text="Close", command=drawing_window.destroy).pack(side="left", padx=10)
        
            return fig
    
        # Initialize with first page
        current_fig = create_page(0)
    
        def on_close():
            plt.close(current_fig)
            drawing_window.destroy()
    
        drawing_window.protocol("WM_DELETE_WINDOW", on_close)

if __name__ == "__main__":
    root = tk.Tk()
    app = SheetCalculationApp(root)
    root.mainloop()