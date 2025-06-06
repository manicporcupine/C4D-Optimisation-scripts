import c4d

def is_ancestor(potential_ancestor, obj):
    """Check if 'potential_ancestor' is an ancestor of 'obj'."""
    parent = obj.GetUp()
    while parent:
        if parent == potential_ancestor:
            return True
        parent = parent.GetUp()
    return False

def get_topmost_parent(obj):
    """Return the topmost parent of an object (or itself if at root)."""
    while obj.GetUp():
        obj = obj.GetUp()
    return obj

def has_conflicting_hierarchy(objs):
    """Check for parent-child conflicts or different top parents."""
    # Check for parent-child overlap
    for obj in objs:
        for other in objs:
            if obj != other and is_ancestor(obj, other):
                return True
    # Check for topmost parent consistency
    top_parents = {get_topmost_parent(obj) for obj in objs}
    return len(top_parents) > 1

def get_children(obj):
    """Returns direct children of obj."""
    children = []
    child = obj.GetDown()
    while child:
        children.append(child)
        child = child.GetNext()
    return children

def main():
    doc = c4d.documents.GetActiveDocument()
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

    if not selection:
        c4d.gui.MessageDialog("No objects selected.")
        return

    # If only one object selected → use its children
    if len(selection) == 1:
        children = get_children(selection[0])
        if not children:
            c4d.gui.MessageDialog("Selected object has no children to sort.")
            return
        selection = children

    if has_conflicting_hierarchy(selection):
        c4d.gui.MessageDialog("⚠️ Please avoid selecting both parents and children, or objects from different groups.")
        return

    def get_pos(obj):
        return obj.GetMg().off

    # Sort: Y → Z → X
    sorted_objs = sorted(selection, key=lambda o: (
        round(get_pos(o).y, 4),
        round(get_pos(o).z, 4),
        round(get_pos(o).x, 4)
    ))

    parent = sorted_objs[0].GetUp()

    for obj in sorted_objs:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
        obj.Remove()

    for obj in sorted_objs:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
        doc.InsertObject(obj, parent=parent)

    c4d.EventAdd()

if __name__ == '__main__':
    main()
