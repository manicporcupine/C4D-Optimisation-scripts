import c4d
from c4d import gui

def get_all_objects(obj, obj_list):
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

def clear_selection(doc):
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)
    for obj in all_objs:
        obj.DelBit(c4d.BIT_ACTIVE)

def get_centered_points(obj):
    points = obj.GetAllPoints()
    if not points:
        return []

    mg = obj.GetMg()
    world_points = [mg * p for p in points]

    center = c4d.Vector()
    for p in world_points:
        center += p
    center /= len(world_points)

    centered = [p - center for p in world_points]
    return centered

def points_match(p_list1, p_list2, tolerance):
    """Checks if every point in p_list1 has at least one point in p_list2 within tolerance."""
    for p1 in p_list1:
        found_match = False
        for p2 in p_list2:
            if (p1 - p2).GetLength() <= tolerance:
                found_match = True
                break
        if not found_match:
            return False
    return True

def are_shapes_equal_by_vertices(obj_a, obj_b, tolerance):
    if obj_a.GetPointCount() != obj_b.GetPointCount():
        return False

    pts_a = get_centered_points(obj_a)
    pts_b = get_centered_points(obj_b)

    return points_match(pts_a, pts_b, tolerance) and points_match(pts_b, pts_a, tolerance)

def get_master_polygon(obj):
    while obj and not obj.CheckType(c4d.Opolygon):
        if obj.CheckType(c4d.Oinstance):
            obj = obj[c4d.INSTANCEOBJECT_LINK]
        else:
            break
    return obj

def phase_a_relink_instances(doc, objects, master_list, tolerance):
    c4d.StatusSetText("Relinking instances...")
    total = len(objects)
    for i, obj in enumerate(objects):
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            master = get_master_polygon(ref)
            if master:
                for known_master in master_list:
                    if are_shapes_equal_by_vertices(master, known_master, tolerance):
                        if obj[c4d.INSTANCEOBJECT_LINK] != known_master:
                            doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                            obj[c4d.INSTANCEOBJECT_LINK] = known_master
                            obj.SetName(known_master.GetName() + "_instance")
                        break
        c4d.StatusSetBar(int((i + 1) / total * 100))

def transfer_children(doc, old_obj, new_parent):
    child = old_obj.GetDown()
    while child:
        next_child = child.GetNext()
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, child)
        world_mtx = child.GetMg()
        child.Remove()
        doc.InsertObject(child, parent=new_parent)
        child.SetMl(~new_parent.GetMg() * world_mtx if new_parent else world_mtx)
        child = next_child

def phase_b_replace_duplicates(doc, objects, master_list, tolerance):
    c4d.StatusSetText("Replacing duplicates...")
    total = len(objects)
    for i, obj in enumerate(list(objects)):
        if obj.CheckType(c4d.Opolygon):
            for master in master_list:
                if obj != master and are_shapes_equal_by_vertices(obj, master, tolerance):
                    parent = obj.GetUp()
                    world_mtx = obj.GetMg()
                    local_mtx = ~parent.GetMg() * world_mtx if parent else world_mtx

                    instance = c4d.BaseObject(c4d.Oinstance)
                    instance[c4d.INSTANCEOBJECT_LINK] = master
                    instance.SetName(master.GetName() + "_instance")
                    instance.SetMl(local_mtx)

                    doc.InsertObject(instance, parent=parent, pred=obj.GetPred())
                    transfer_children(doc, obj, instance)

                    tag = obj.GetFirstTag()
                    while tag:
                        if tag.CheckType(c4d.Ttexture):
                            instance.InsertTag(tag.GetClone())
                        tag = tag.GetNext()

                    doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
                    doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                    obj.Remove()
                    break
        c4d.StatusSetBar(int((i + 1) / total * 100))

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document.")
        return

    input_str = gui.InputDialog("Enter tolerance (e.g. 0.01):", "0.01")
    if not input_str:
        return
    try:
        tolerance = float(input_str)
    except ValueError:
        gui.MessageDialog("Invalid number.")
        return

    clear_selection(doc)
    objects = []
    get_all_objects(doc.GetFirstObject(), objects)
    if not objects:
        gui.MessageDialog("No objects found.")
        return

    c4d.StatusSetText("Building master list...")
    master_list = []
    total = len(objects)
    for i, obj in enumerate(objects):
        if obj.CheckType(c4d.Opolygon):
            if not any(are_shapes_equal_by_vertices(obj, m, tolerance) for m in master_list):
                master_list.append(obj)
        c4d.StatusSetBar(int((i + 1) / total * 100))

    doc.StartUndo()
    phase_a_relink_instances(doc, objects, master_list, tolerance)
    phase_b_replace_duplicates(doc, objects, master_list, tolerance)
    doc.EndUndo()

    c4d.StatusClear()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
