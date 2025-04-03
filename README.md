A collection of Cinema 4D optimization scripts developed with assistance from ChatGPT. These scripts help clean up and optimize your scenes by converting duplicate objects into instances, managing materials (especially node-based Redshift materials), renaming objects, and cleaning scene hierarchies. They are especially useful when exporting heavy scenes to other applications or cleaning up imported files (such as STEP files).

Note: Some scripts (like "Delete_all_hidden_objects.py" and "Delete_ins-ces_inside_other_inst-ces.py") address very specific issues:

Delete_all_hidden_objects.py: Removes hidden objects to ensure that exported scenes do not contain overlapping duplicate geometry.

Delete_ins-ces_inside_other_inst-ces.py: Deletes instances that are nested inside other instances, which is particularly useful when cleaning up imported STEP files.

Scripts

1. Convert all same obj to instances.py
   
Replaces duplicate polygon objects with instances of the first found object sharing the same geometry. The script computes a geometry hash based on the object's points and polygons and replaces duplicates with instance objects.

2. Convert same obj as sel to instances.py
   
Replaces all polygon objects that are identical to the currently selected object with an instance of that object. The script preserves local transformations.

3. DELETE DUPLICATE REDSHIFT MATERIALS.py
   
Detects duplicate Redshift materials by analyzing their node graph signatures (using a normalized JSON representation and SHA256 hash). It updates texture tags to point to the unique material and then deletes duplicates.

4. Delete_all_hidden_objects.py
   
Recursively searches for objects hidden in the viewport or renderer and deletes them. This is useful for exporting a final scene to another application without unwanted hidden geometry.

5. Delete_empty_material_tags.py
    
Deletes empty material (texture) tags from objects in the scene to clean up unused tags.

6. Delete_empty_nulls.py
    
Recursively deletes empty null objects (nulls with no children) to reduce scene clutter.

7. Delete_material_tag_from_selected_objects.py
    
Deletes all material tags from the currently selected objects.

8. Delete_red_instances.py
    
Removes orphan Redshift instance objects (instances that have no valid reference) from the scene.

9. MOVE ON TOP.py
    
Moves the selected objects to the top of the object manager while preserving their world transforms (if they were in a null).

10. MOVE TO BOTTOM.py
    
Moves the selected objects to the bottom of the object manager, preserving their world transforms (if they were in a null).

11. Delete_ins-ces_inside_other_inst-ces.py
    
Recursively finds and deletes instance objects that are nested inside other instance objects. This is particularly useful for cleaning up imported STEP files where multiple instance layers can cause issues.

12. Quick Rename.py
    
Opens a dialog that allows you to quickly rename selected objects by adding a prefix, postfix, or by assigning numbered names. Quicker than a built-in tool.

13. Rename Instance as reference.py
    
For selected instance objects, renames them based on the name of their reference object, appending “_Instance” to the reference’s name.

14. Select active camera.py
    
Like in 3dsMax, selects the currently active camera (as determined by the active viewport) in the scene. 

15. Select parent.py
    
For the currently selected objects, selects their parent objects. If multiple objects share the same parent, only unique parents are selected. I feel a bit stupid, because it has to be a built-in function, but I didn't found it.

16. Select_all_instances_of_an_active_object.py
    
Similar to a 3ds Max, selects all instance objects in the scene that reference the currently active object. Useful for quickly gathering all instances of a particular object.

17. Select_same_instances_v1.py
    
Similar to the same 3ds Max function, when an instance is selected, this script selects all other instances that reference the same source object.

18. Set Parent & Put into.py
    
Opens a dialog that allows you to first set a parent object, then move (or “put”) selected objects under that parent while preserving their world coordinates.

Installation
Clone or Download:
Clone this repository or download it as a ZIP file.

Copy Scripts:
Place the script files into your Cinema 4D library/scripts folder.

Restart Cinema 4D:
Restart Cinema 4D or refresh the Script Manager to load the new scripts.

Usage
Open the Script Manager in Cinema 4D.

Run the desired script.

Follow on-screen instructions, dialogs, or check the console for feedback.

Requirements
Cinema 4D: Scripts have been tested with Cinema 4D 2025.x.

Redshift: Relevant scripts have been tested with Redshift 2025.x.

Some scripts are intended for specific workflows (e.g., cleaning up imported STEP files or preparing scenes for export).

Contributing
Contributions, bug reports, and suggestions are welcome. Please open an issue or submit a pull request with improvements or additional scripts.

License
This project is licensed under the MIT License.

Disclaimer
These scripts were developed with assistance from ChatGPT and are provided "as is" without any warranty. Use them at your own risk.

