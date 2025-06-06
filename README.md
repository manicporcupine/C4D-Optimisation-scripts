# 🧰 Cinema 4D Optimization & Cleanup Scripts

A humble collection of tools for cleaning, optimizing, and organizing Cinema 4D scenes — especially useful when dealing with imported OBJ/FBX/STEP geometry or preparing scenes for export.

Developed with the help of ChatGPT.

---

## 🔄 Converting to instances:

- **Convert Duplicates to Instances (via Point Cloud).py**  
  Converts only *duplicates of selected object(s)* into instances using vertex cloud comparison. Best chioce for messy CAD models.

- **Convert Duplicates to Instances.py**  
  Converts duplicates of selected object to instances using fast hash matching.

- **Swap Instances and Copy.py**  
  Copies selected objects to a new file without losing instances.

---

## 🎨 Materials & Tags

- **DELETE DUPLICATE REDSHIFT MATERIALS.py**  
  Merges Redshift node materials with identical node graphs. Updates tags and deletes duplicates. Works with Open PBR and standard RS shaders.

- **Delete Empty Material Tags.py**  
  Deletes unused texture tags from the scene.

- **Delete Material Tags from Selected Objects.py**  
  Deletes all texture tags from selected objects.

---

## 🧼 Scene Cleanup

- **Delete All Hidden Objects.py**  
  Removes all objects hidden in viewport or renderer. Ensures export-ready geometry. Doesn't delete anything linked to an instance.

- **Delete Red Instances.py**  
  Deletes orphaned Redshift instance objects (those with no valid reference).

- **Delete Empty Nulls.py**  
  Deletes nulls that have no children.

---

## 🧠 Hierarchy & Parenting Tools

- **MOVE ON TOP.py**  
  Moves selected object(s) to the top of the Object Manager. Because sometimes you wanna keep 'em close.

- **MOVE TO BOTTOM.py**  
  Moves selected object(s) to the bottom of the Object Manager.

- **Set Parent & Put into.py**  
  First button sets a parent; second button moves selected objects into that parent. No need to drag and drop into an already existing group across the scene tree.

- **Select Parent.py**  
  Selects the parent(s) of selected objects.

---

## 🧭 Object Selection Tools

- **Select Active Camera.py**  
  Selects the currently active camera in the viewport (like in 3ds Max).

- **Select Same Instances.py**  
  Selects all instance objects that reference the same master as the currently selected instance. *Does not select the master*.

- **Select Instances.py**  
  Selects both the selected object(s) and all instances that reference them. Works whether you select a master or one of its instances.

- **Select Duplicates.py**  
  (Also listed under Converting to instances—this can be used purely to pick out duplicates before conversion.)

- **Select Duplicates via Point Cloud.py**  
  (Also listed under Converting to instances—this is ideal for CAD imports where exact hash matching might fail.)

---

## ✍️ Naming & Renaming

- **Rename Instance as Reference.py**  
  Renames selected instances to match their reference object’s name + "_instance".

- **Rename all Instances as Reference.py**  
  Renames all instances in the scene to match their reference object’s name + "_instance".

- **Quick Rename.py**  
  Rename selected objects quickly with prefix, suffix, or auto-numbering. Faster than the built-in tool.

---

## 📦 Misc

- **Align Axis Rotation to World.py**  
  Realigns the pivot axis of selected objects to match world axes, fixing axis misalignments that occur after importing from other applications.

- **RS Lights Include-Exclude Manager.py**  
  Provides a dialog for adding or removing multiple objects from Redshift lights’ include/exclude lists at once, and remembers your selections until the window is closed.

- **README.md**  
  This file.

---
