# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
from c4d import gui

def get_all_objects(obj, obj_list):
    """Recursively collects all objects in the scene."""
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

def is_effectively_hidden(obj):
    """
    Returns True if the object itself or any of its parent objects
    is hidden in the viewport or renderer.
    """
    if obj is None:
        return False
    if obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] == c4d.OBJECT_OFF or \
       obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] == c4d.OBJECT_OFF:
        return True
    parent = obj.GetUp()
    while parent:
        if parent[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] == c4d.OBJECT_OFF or \
           parent[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] == c4d.OBJECT_OFF:
            return True
        parent = parent.GetUp()
    return False

def swap_hidden_referenced_instances(doc):
    """
    For each visible instance whose referenced object (master) is hidden,
    the script finds the first such instance for each unique hidden master,
    clones the hidden master, inserts the clone in the same hierarchy with its local
    matrix recalculated (so its world coordinates match the instance),
    and then removes that first instance.

    All subsequent visible instances referencing the same hidden master get updated
    to point to the clone. This ensures that only one converted (editable/blue) object
    remains as the master.
    """
    swapped_refs = {}  # Maps original hidden master objects to their visible clone
    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)

    for obj in all_objects:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            if ref and is_effectively_hidden(ref):
                if ref not in swapped_refs:
                    parent = obj.GetUp()
                    instance_world = obj.GetMg()  # Get the instance's world matrix
                    # Calculate new local matrix for the clone relative to parent's global matrix.
                    if parent:
                        new_local = ~parent.GetMg() * instance_world
                    else:
                        new_local = instance_world
                    # Clone the hidden master.
                    ref_clone = ref.GetClone()
                    ref_clone.SetMl(new_local)
                    # Insert the clone in the same hierarchy as the instance.
                    doc.InsertObject(ref_clone, parent=parent, pred=obj)
                    doc.AddUndo(c4d.UNDOTYPE_NEW, ref_clone)
                    swapped_refs[ref] = ref_clone
                    # Remove the first instance since its job is to swap.
                    doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                    obj.Remove()
                    continue  # Skip updating this instance since it was removed.
                else:
                    # For subsequent visible instances referencing the same hidden master,
                    # update their link to point to the clone.
                    new_ref = swapped_refs[ref]
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = new_ref

def delete_hidden_objects(doc):
    """
    Recursively collects and deletes all objects that are hidden in the viewport
    or renderer.
    """
    hidden_objects = []

    def collect_hidden_objects(obj):
        while obj:
            if obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] == c4d.OBJECT_OFF or \
               obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] == c4d.OBJECT_OFF:
                hidden_objects.append(obj)
            collect_hidden_objects(obj.GetDown())
            obj = obj.GetNext()

    collect_hidden_objects(doc.GetFirstObject())

    for obj in hidden_objects:
        doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
        obj.Remove()

    return len(hidden_objects)

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    if not gui.QuestionDialog("Are you sure you want to delete all hidden objects?"):
        return

    # Group all operations into a single undo step.
    doc.StartUndo()
    swap_hidden_referenced_instances(doc)
    num_hidden = delete_hidden_objects(doc)
    doc.EndUndo()

    c4d.EventAdd()
    gui.MessageDialog(f"Deleted {num_hidden} hidden objects.")

if __name__ == "__main__":
    main()
