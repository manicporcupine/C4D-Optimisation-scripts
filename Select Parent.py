import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    
    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    
    if not selected_objects:
        c4d.gui.MessageDialog("No object selected.")
        return

    parents = []
    
    for obj in selected_objects:
        parent = obj.GetUp()  # Get parent object
        if parent and parent not in parents:
            parents.append(parent)  # Store unique parent objects

    if parents:
        doc.StartUndo()
        doc.SetActiveObject(parents[0], c4d.SELECTION_NEW)  # Select first parent
        for parent in parents[1:]:
            doc.SetActiveObject(parent, c4d.SELECTION_ADD)  # Add remaining parents
        doc.EndUndo()
        c4d.EventAdd()
    else:
        c4d.gui.MessageDialog("Selected object has no parent.")

if __name__ == "__main__":
    main()
