"""
Create Instances For Selection
==============================

This script iterates over all currently selected objects in the active Cinema 4D document and creates an `Instance` object for each one.  The newly created instance is linked to its source object, inserted right after the source in the Object Manager, and its global position, rotation, and scale are copied so that it appears at exactly the same spot.  If no objects are selected, the script does nothing.

Key features:

* Works with any object type (generators, deformers, primitives, etc.).
* Maintains a clean undo stack so that all instances can be undone with a single Ctrl+Z.
* Leaves the original objects untouched; you can delete or hide them manually if desired.

Usage:

Select one or more objects in your scene and run the script from the Script Manager or your custom menu.  An instance will appear for each object immediately after the original in the Object Manager.
"""

import c4d
from c4d import documents as docs


def main() -> None:
    """Entry point for the script."""
    doc = docs.GetActiveDocument()
    if doc is None:
        return

    # Get directly selected objects; we don't traverse children because each selected item
    # should get its own instance.
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    if not selection:
        return

    # Begin undo recording so the operation can be reverted cleanly.
    doc.StartUndo()
    try:
        for obj in selection:
            # Create a new Instance object.
            inst = c4d.BaseObject(c4d.Oinstance)
            if inst is None:
                # Skip if instance creation failed (should rarely happen).
                continue

            # Link the instance to the original object.
            inst[c4d.INSTANCEOBJECT_LINK] = obj

            # Insert the instance right after the source object in the Object Manager
            # for easier visibility and organization.
            inst.InsertAfter(obj)

            # Copy the global transformation matrix so the instance appears in the same
            # location and orientation as the original.
            inst.SetMg(obj.GetMg())

            # Register the creation with the undo system.
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, inst)

    finally:
        # End undo recording.
        doc.EndUndo()
        # Update the scene so the new objects appear immediately.
        c4d.EventAdd()


if __name__ == "__main__":
    main()
