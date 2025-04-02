import c4d

def get_last_object(obj):
    """ Recursively finds the last object in the hierarchy. """
    while obj.GetNext():
        obj = obj.GetNext()
    return obj

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    if not selected_objects:
        return

    doc.StartUndo()

    # Find the last top-level object
    last_obj = get_last_object(doc.GetFirstObject())

    for obj in selected_objects:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)

        # Store world transform
        mg = obj.GetMg()

        obj.Remove()  # Temporarily remove object
        doc.InsertObject(obj, None, last_obj)  # Insert after the last object
        last_obj = obj  # Update last_obj to maintain order

        obj.SetMg(mg)  # Restore world transform

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
