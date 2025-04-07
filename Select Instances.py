import c4d

def get_instance_master(obj):
    """Returns the ultimate reference of an instance or the object itself if not an instance."""
    while obj and obj.GetType() == c4d.Oinstance:
        obj = obj[c4d.INSTANCEOBJECT_LINK]
    return obj

def collect_all_instances(doc, master_objs):
    """Finds all instances in the document referencing any of the given master objects."""
    masters_set = set(master_objs)
    instances = []

    def search(obj):
        while obj:
            if obj.GetType() == c4d.Oinstance:
                ref = obj[c4d.INSTANCEOBJECT_LINK]
                if ref in masters_set:
                    instances.append(obj)
            search(obj.GetDown())
            obj = obj.GetNext()

    search(doc.GetFirstObject())
    return instances

def main():
    doc = c4d.documents.GetActiveDocument()
    selection = doc.GetActiveObjects(0)

    if not selection:
        return

    # Step 1: Resolve unique masters from selection
    master_objs = []
    seen = set()
    for obj in selection:
        master = get_instance_master(obj)
        if master and master not in seen:
            master_objs.append(master)
            seen.add(master)

    if not master_objs:
        return

    # Step 2: Find all matching instances
    instances = collect_all_instances(doc, master_objs)

    # Step 3: Select everything
    doc.SetActiveObject(None, c4d.SELECTION_NEW)
    for m in master_objs:
        doc.SetActiveObject(m, c4d.SELECTION_ADD)
    for inst in instances:
        doc.SetActiveObject(inst, c4d.SELECTION_ADD)

    c4d.EventAdd()

if __name__ == '__main__':
    main()
