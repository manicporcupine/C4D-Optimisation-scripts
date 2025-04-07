# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d

def select_all_instances(doc, target_obj):
    """Selects all instances that reference the given target object, and also keeps the target object selected."""
    if not target_obj:
        return

    instances = []
    def search(obj):
        while obj:
            if obj.GetType() == c4d.Oinstance and obj[c4d.INSTANCEOBJECT_LINK] == target_obj:
                instances.append(obj)
            search(obj.GetDown())  # Search child objects
            obj = obj.GetNext()    # Move to the next object

    search(doc.GetFirstObject())

    # Clear current selection.
    doc.SetActiveObject(None, c4d.SELECTION_NEW)
    # First, add the master (target) object to the selection.
    doc.SetActiveObject(target_obj, c4d.SELECTION_ADD)
    # Then, add each found instance.
    for inst in instances:
        doc.SetActiveObject(inst, c4d.SELECTION_ADD)
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    selection = doc.GetActiveObjects(0)

    if not selection or len(selection) != 1:
        return  # Exit if no object or more than one object is selected

    target_obj = selection[0]
    select_all_instances(doc, target_obj)

if __name__ == "__main__":
    main()
