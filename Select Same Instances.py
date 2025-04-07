import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    selection = doc.GetActiveObjects(0)
    
    if not selection or selection[0].GetType() != c4d.Oinstance:
        return

    ref_obj = selection[0][c4d.INSTANCEOBJECT_LINK]
    if not ref_obj:
        return

    instances = []
    def search(obj):
        while obj:
            if obj.GetType() == c4d.Oinstance and obj[c4d.INSTANCEOBJECT_LINK] == ref_obj:
                instances.append(obj)
            search(obj.GetDown())
            obj = obj.GetNext()
    
    search(doc.GetFirstObject())
    
    if instances:
        doc.SetActiveObject(None, c4d.SELECTION_NEW)  # Deselect everything
        for inst in instances:
            doc.SetActiveObject(inst, c4d.SELECTION_ADD)  # Select matching instances
        c4d.EventAdd()

if __name__ == "__main__":
    main()
