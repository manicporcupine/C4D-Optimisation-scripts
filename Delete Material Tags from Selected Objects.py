import c4d

def delete_material_tags(obj):
    """Deletes all material tags from the given object."""
    tag = obj.GetFirstTag()
    while tag:
        next_tag = tag.GetNext()  # Store the next tag before removing
        if tag.CheckType(c4d.Ttexture):  # Check if it's a material tag
            tag.Remove()  # Correct way to remove the tag
        tag = next_tag

def main():
    doc = c4d.documents.GetActiveDocument()
    selection = doc.GetActiveObjects(0)
    
    if not selection:
        return

    doc.StartUndo()  # Start undo group
    for obj in selection:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)  # Add undo step for each object
        delete_material_tags(obj)
    doc.EndUndo()  # End undo group
    c4d.EventAdd()

if __name__ == "__main__":
    main()
