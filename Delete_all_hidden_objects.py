import c4d
from c4d import gui

def main():
    doc = c4d.documents.GetActiveDocument()  # Get the active Cinema 4D document
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    doc.StartUndo()  # Start recording undo actions
    hidden_objects = []  # List to collect hidden objects

    # Iterate through all objects in the document
    def collect_hidden_objects(obj):
        while obj:
            # Check if the object is hidden in the viewport or renderer
            if obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] == c4d.OBJECT_OFF or obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] == c4d.OBJECT_OFF:
                hidden_objects.append(obj)  # Add to the list if hidden
            collect_hidden_objects(obj.GetDown())  # Check child objects
            obj = obj.GetNext()  # Move to the next object

    collect_hidden_objects(doc.GetFirstObject())  # Start with the first object in the scene

    # Delete all collected hidden objects
    for obj in hidden_objects:
        doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)  # Add undo step
        obj.Remove()  # Remove the object

    doc.EndUndo()  # End undo recording
    c4d.EventAdd()  # Refresh the scene

    gui.MessageDialog(f"Deleted {len(hidden_objects)} hidden objects.")

if __name__ == "__main__":
    main()
