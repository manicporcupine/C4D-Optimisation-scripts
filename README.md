# Cinema 4D Optimization Scripts

A collection of Cinema 4D optimization scripts developed with assistance from ChatGPT. These tools help clean and optimize your scenes by converting duplicate objects into instances, managing materials (including Redshift node-based materials), renaming objects, and cleaning scene hierarchies.

They are especially useful when exporting heavy scenes to other applications or cleaning up imported files (e.g. STEP files).

---

## Special Notes

Some scripts address very specific problems, such as:

- **Delete All Hidden Objects** – Ensures exported scenes don’t contain overlapping or unused geometry by removing all hidden objects.
- **Delete Instances Inside Other Instances** – Removes nested instances (instances placed inside other instances), often found in imported STEP files.

---

## Scripts

### 1. **Convert All Same Objects to Instances**
Replaces all duplicate polygon objects with instances of the first found object that shares the same geometry (based on a geometry hash of points and polygons).

### 2. **Convert Duplicates of Selected Object to Instances**
Replaces all polygon objects that are identical to the currently selected object with instances of that object. Local/world transformations and hierarchy are preserved.

### 3. **Delete Duplicate Redshift Materials**
Detects and removes duplicate Redshift materials by analyzing node graph data. Works well with Redshift Open PBR materials. Texture tags are updated to reference the unique material.

### 4. **Delete All Hidden Objects**
Recursively removes objects hidden in the viewport or renderer. Useful when exporting scenes to eliminate invisible geometry.

### 5. **Delete Empty Material Tags**
Deletes material tags that are not assigned to any material, helping clean up the scene.

### 6. **Delete Empty Nulls**
Removes null objects with no children (recursively), reducing clutter in the Object Manager.

### 7. **Delete Material Tags from Selected Objects**
Removes all material tags from currently selected objects.

### 8. **Delete Red Instances**
Deletes broken or orphaned Redshift instances (instances with missing or invalid reference objects).

### 9. **Delete Instances Inside Other Instances**
Recursively finds and deletes instance objects that are placed inside other instance objects (common in STEP imports).

### 10. **Move On Top**
Moves the selected object(s) to the top of the Object Manager hierarchy without changing world position.

### 11. **Move To Bottom**
Moves the selected object(s) to the bottom of the Object Manager hierarchy while preserving world transforms.

### 12. **Quick Rename**
Opens a simple dialog to batch rename selected objects with prefix, suffix, or numbering options. Quicker than the built-in rename tool.

### 13. **Rename Instance to Match Reference**
Renames selected instance objects to match the name of their reference/master object, appending `_instance`.

### 14. **Select Active Camera**
Selects the active camera based on the currently active viewport (similar to 3ds Max).

### 15. **Select Parent**
Selects the parent of the currently selected object(s). If multiple selected objects share the same parent, only one instance of the parent is selected.

### 16. **Select All Instances of Active Object**
Selects all instance objects that reference the currently selected object (works like "Select Similar" in 3ds Max).

### 17. **Select Same Instances**
When one instance is selected, this selects all other instances that reference the same source object.

### 18. **Set Parent & Put Into**
Opens a dialog with two options:  
- **Set Parent** – Stores the currently selected object as a parent.  
- **Put Into** – Puts other selected objects under the stored parent, preserving world coordinates.

---

## Requirements

- **Cinema 4D** – Scripts tested with Cinema 4D 2025.x  
- **Redshift** – Relevant scripts tested with Redshift 2025.x

Some scripts are tailored for specific workflows (e.g., cleaning imported STEP files, preparing scenes for export, Redshift cleanup, etc.).

> These scripts were developed with the help of ChatGPT and are provided **“as is”** without warranty. Use them at your own risk.
