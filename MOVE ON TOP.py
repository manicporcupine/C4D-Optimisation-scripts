import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    if not selected_objects:
        return

    doc.StartUndo()

    for obj in reversed(selected_objects):  # Reverse to keep order
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)

        # Store world transform
        mg = obj.GetMg()

        obj.Remove()  # Temporarily remove object
        doc.InsertObject(obj, None, None)  # Reinsert at top level

        obj.SetMg(mg)  # Restore world transform

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
