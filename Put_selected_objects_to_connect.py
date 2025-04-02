import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    doc.StartUndo()  # Start undo recording

    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)  # Get selected objects

    if not selected_objects:
        c4d.gui.MessageDialog("No objects selected.")
        return

    for obj in selected_objects:
        # Create a Connect Object
        connect = c4d.BaseObject(c4d.Oconnector)
        connect.SetName(f"{obj.GetName()}_Connect")  # Name it after the original object
        doc.InsertObject(connect, parent=obj.GetUp(), pred=obj)  # Insert at the same hierarchy level

        # Move the object under the Connect Object
        doc.AddUndo(c4d.UNDOTYPE_NEW, connect)
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
        obj.InsertUnder(connect)

    doc.EndUndo()  # End undo recording
    c4d.EventAdd()  # Refresh the scene

if __name__ == "__main__":
    main()