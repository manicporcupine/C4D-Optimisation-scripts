import c4d

def delete_empty_nulls(doc):
    """Recursively deletes all empty null objects in the document."""
    def search_and_delete(obj):
        while obj:
            next_obj = obj.GetNext()  # Store the next object before deleting
            if obj.GetType() == c4d.Onull and not obj.GetDown():  # Check if it's an empty null
                doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                obj.Remove()  # Correct method to remove the object
            else:
                search_and_delete(obj.GetDown())  # Check child objects
            obj = next_obj  # Move to the next object

    doc.StartUndo()  # Start undo group
    search_and_delete(doc.GetFirstObject())
    doc.EndUndo()  # End undo group
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    delete_empty_nulls(doc)

if __name__ == "__main__":
    main()
