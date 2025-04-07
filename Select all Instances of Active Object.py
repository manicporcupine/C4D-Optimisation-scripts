import c4d

def select_all_instances(doc, target_obj):
    """Selects all instances that reference the given target object."""
    if not target_obj:
        return

    instances = []
    def search(obj):
        while obj:
            if obj.GetType() == c4d.Oinstance and obj[c4d.INSTANCEOBJECT_LINK] == target_obj:
                instances.append(obj)
            search(obj.GetDown())  # Search child objects
            obj = obj.GetNext()  # Move to the next object
    
    search(doc.GetFirstObject())
    
    if instances:
        doc.SetActiveObject(None, c4d.SELECTION_NEW)  # Deselect everything
        for inst in instances:
            doc.SetActiveObject(inst, c4d.SELECTION_ADD)  # Add each instance to the selection
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
