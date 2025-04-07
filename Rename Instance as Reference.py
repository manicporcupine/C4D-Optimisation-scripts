import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    
    doc.StartUndo()  # Start undo recording

    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)  # Get selected objects
    
    for obj in selected_objects:
        if obj.GetType() == c4d.Oinstance:  # Check if object is an instance
            ref = obj[c4d.INSTANCEOBJECT_LINK]  # Get reference object
            if ref:  # If reference exists
                new_name = f"{ref.GetName()}_Instance"
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)  # Add undo step
                obj.SetName(new_name)  # Rename instance

    doc.EndUndo()  # End undo recording
    c4d.EventAdd()  # Refresh scene

if __name__ == "__main__":
    main()
