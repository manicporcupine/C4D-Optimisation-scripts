import c4d
from c4d import gui

def get_all_objects(op, out):
    """Recursively collects all objects in the scene."""
    while op:
        out.append(op)
        get_all_objects(op.GetDown(), out)
        op = op.GetNext()

def clear_selection(doc):
    """Clears the active selection flag from all objects."""
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)
    for obj in all_objs:
        obj.DelBit(c4d.BIT_ACTIVE)

def get_centered_points(obj):
    """
    Returns a list of world-space points centered on the object's centroid.
    This ignores pivot position.
    """
    points = obj.GetAllPoints()
    if not points:
        return []
    mg = obj.GetMg()
    world_pts = [mg * p for p in points]
    center = c4d.Vector(0)
    for p in world_pts:
        center += p
    center /= len(world_pts)
    return [p - center for p in world_pts]

def points_match(p_list1, p_list2, tolerance):
    """
    Checks if every point in p_list1 has at least one point in p_list2 within tolerance,
    and vice versa.
    """
    for p1 in p_list1:
        if not any((p1 - p2).GetLength() <= tolerance for p2 in p_list2):
            return False
    for p2 in p_list2:
        if not any((p2 - p1).GetLength() <= tolerance for p1 in p_list1):
            return False
    return True

def are_shapes_equal_by_vertices(obj_a, obj_b, tolerance):
    """
    Compares two polygon objects via their centered vertex clouds.
    Returns True if both objects have the same number of points and each point in one
    finds a match in the other within the specified tolerance.
    """
    if obj_a.GetPointCount() != obj_b.GetPointCount():
        return False
    pts_a = get_centered_points(obj_a)
    pts_b = get_centered_points(obj_b)
    return points_match(pts_a, pts_b, tolerance)

def get_master_object(op):
    """Traces instance links until it retrieves the underlying master object."""
    while op and op.CheckType(c4d.Oinstance):
        op = op[c4d.INSTANCEOBJECT_LINK]
    return op

def relink_instances(doc, all_objs, master, tolerance, dup_obj=None):
    """
    Reassigns any instance objects that reference a duplicate (dup_obj, if provided)
    or are identical (by vertex check within tolerance) to 'master'.
    """
    for obj in all_objs:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            real_master = get_master_object(ref)
            if dup_obj:
                if real_master == dup_obj:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = master
                    obj.SetName(master.GetName() + "_instance")
            else:
                if real_master and are_shapes_equal_by_vertices(master, real_master, tolerance):
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = master
                    obj.SetName(master.GetName() + "_instance")

def transfer_children(doc, old_obj, new_parent):
    """
    Transfers all child objects from old_obj to new_parent,
    preserving their world-space transforms.
    """
    child = old_obj.GetDown()
    while child:
        next_child = child.GetNext()
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, child)
        world_mtx = child.GetMg()
        child.Remove()
        doc.InsertObject(child, parent=new_parent)
        child.SetMl(~new_parent.GetMg() * world_mtx if new_parent else world_mtx)
        child = next_child

def replace_duplicates(doc, all_objs, master, masters, tolerance):
    """
    Converts any duplicate object (scene-wide) that is identical to 'master'
    (as determined by vertex cloud check within tolerance) into an instance of master.
    Prior to deletion, any instances referencing the duplicate are re-linked to master.
    
    Returns the number of duplicates converted.
    """
    converted = 0
    for obj in list(all_objs):
        if obj == master or obj in masters:
            continue
        if obj.CheckType(c4d.Opolygon) and are_shapes_equal_by_vertices(master, obj, tolerance):
            parent = obj.GetUp()
            world_mtx = obj.GetMg()
            local_mtx = (~parent.GetMg() * world_mtx) if parent else world_mtx

            relink_instances(doc, all_objs, master, tolerance, dup_obj=obj)

            instance = c4d.BaseObject(c4d.Oinstance)
            instance[c4d.INSTANCEOBJECT_LINK] = master
            instance.SetName(master.GetName() + "_instance")
            instance.SetMl(local_mtx)
            doc.InsertObject(instance, parent=parent, pred=obj)

            transfer_children(doc, obj, instance)

            for inst in all_objs:
                if inst.CheckType(c4d.Oinstance) and inst[c4d.INSTANCEOBJECT_LINK] == obj:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, inst)
                    inst[c4d.INSTANCEOBJECT_LINK] = master
                    inst.SetName(master.GetName() + "_instance")

            tag = obj.GetFirstTag()
            while tag:
                if tag.CheckType(c4d.Ttexture):
                    instance.InsertTag(tag.GetClone())
                tag = tag.GetNext()

            doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
            doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
            obj.Remove()
            converted += 1
            # Continue checking for more duplicates
    return converted

def deduplicate_selection(selection, tolerance):
    """
    From the selected polygon objects, returns a list of unique master objects.
    If two selected objects are identical by vertex cloud comparison (within tolerance),
    only one is kept.
    """
    unique = []
    for obj in selection:
        if not any(are_shapes_equal_by_vertices(obj, u, tolerance) for u in unique):
            unique.append(obj)
    return unique

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    # Step 1: Process selection (multi-select, polygon objects)
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    selected_polys = [obj for obj in selection if obj.CheckType(c4d.Opolygon)]
    if not selected_polys:
        gui.MessageDialog("Please select one or more polygon objects to use as reference.")
        return

    # Ask for tolerance from the user.
    input_str = gui.InputDialog("Enter tolerance (e.g. 0.01):", "0.01")
    if not input_str:
        return
    try:
        tolerance = float(input_str)
    except ValueError:
        gui.MessageDialog("Invalid number.")
        return

    # Deduplicate selected objects.
    masters = deduplicate_selection(selected_polys, tolerance)
    # (No dialog if duplicates found; dialog will appear only if no duplicates found later.)

    # Step 2: Gather all scene objects.
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)

    doc.StartUndo()

    # Step 3: Re-link existing instances for each master.
    for master in masters:
        relink_instances(doc, all_objs, master, tolerance)

    # Step 4: Replace duplicates (scene-wide) for each master.
    total_converted = 0
    for master in masters:
        total_converted += replace_duplicates(doc, all_objs, master, masters, tolerance)

    doc.EndUndo()
    c4d.EventAdd()

    # Show a dialog only if no duplicates were found.
    if total_converted == 0:
        gui.MessageDialog("No duplicates found.")
    
if __name__ == '__main__':
    main()
