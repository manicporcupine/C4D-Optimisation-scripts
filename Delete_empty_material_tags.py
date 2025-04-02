import c4d

def delete_empty_material_tags(doc):
    """Deletes all empty material tags from objects in the document."""
    def search(obj):
        while obj:
            tags = obj.GetTags()
            for tag in tags:
                if tag.CheckType(c4d.Ttexture) and not tag[c4d.TEXTURETAG_MATERIAL]:
                    doc.AddUndo(c4d.UNDOTYPE_DELETE, tag)  # Add undo support
                    tag.Remove()  # Corrected: Use Remove() on the tag
            search(obj.GetDown())
            obj = obj.GetNext()

    doc.StartUndo()  # Begin undo operation
    search(doc.GetFirstObject())
    doc.EndUndo()    # End undo operation
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    delete_empty_material_tags(doc)

if __name__ == "__main__":
    main()
