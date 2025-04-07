import c4d

def get_all_objects(op, out):
    while op:
        out.append(op)
        get_all_objects(op.GetDown(), out)
        op = op.GetNext()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)

    doc.StartUndo()
    renamed = 0

    for obj in all_objs:
        if obj.GetType() == c4d.Oinstance:
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            if ref:
                new_name = ref.GetName() + "_instance"
                if obj.GetName() != new_name:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj.SetName(new_name)
                    renamed += 1

    doc.EndUndo()
    c4d.EventAdd()

    if renamed:
        c4d.gui.MessageDialog(f"Renamed {renamed} instance(s).")
    else:
        c4d.gui.MessageDialog("No instance names were changed.")

if __name__ == '__main__':
    main()
