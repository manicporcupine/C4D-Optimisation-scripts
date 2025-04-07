import c4d
from c4d import gui

def get_all_objects(obj, obj_list):
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

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

    return [p - center for p in world_points]

def points_match(p_list1, p_list2, tolerance):
    for p1 in p_list1:
        if not any((p1 - p2).GetLength() <= tolerance for p2 in p_list2):
            return False
    return True

def are_shapes_equal_by_vertices(obj_a, obj_b, tolerance):
    if obj_a.GetPointCount() != obj_b.GetPointCount():
        return False

    pts_a = get_centered_points(obj_a)
    pts_b = get_centered_points(obj_b)

    return points_match(pts_a, pts_b, tolerance) and points_match(pts_b, pts_a, tolerance)

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

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    if not selection:
        gui.MessageDialog("Please select one or more polygon objects to use as reference.")
        return

    reference_objects = [obj for obj in selection if obj.CheckType(c4d.Opolygon)]
    if not reference_objects:
        gui.MessageDialog("No polygonal objects selected.")
        return

    input_str = gui.InputDialog("Enter tolerance (e.g. 0.01):", "0.01")
    if not input_str:
        return
    try:
        tolerance = float(input_str)
    except ValueError:
        gui.MessageDialog("Invalid number.")
        return

    # Get all scene objects
    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)

    # Build comparison list (exclude selected refs themselves)
    candidates = [obj for obj in all_objects if obj not in reference_objects and obj.CheckType(c4d.Opolygon)]

    total = len(candidates)
    converted = 0

    doc.StartUndo()
    for i, obj in enumerate(candidates):
        c4d.StatusSetText(f"Checking: {obj.GetName()}")
        c4d.StatusSetBar(int((i + 1) / total * 100))

        for ref in reference_objects:
            if obj.GetPointCount() != ref.GetPointCount():
                continue
            if are_shapes_equal_by_vertices(ref, obj, tolerance):
                parent = obj.GetUp()
                world_mtx = obj.GetMg()
                local_mtx = ~parent.GetMg() * world_mtx if parent else world_mtx

                instance = c4d.BaseObject(c4d.Oinstance)
                instance[c4d.INSTANCEOBJECT_LINK] = ref
                instance.SetName(ref.GetName() + "_instance")
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
                converted += 1
                break  # no need to test against other masters
    doc.EndUndo()
    c4d.StatusClear()
    c4d.EventAdd()

    if converted:
        gui.MessageDialog(f"Converted {converted} duplicate object(s) to instances.")
    else:
        gui.MessageDialog("No duplicates found.")

if __name__ == '__main__':
    main()
