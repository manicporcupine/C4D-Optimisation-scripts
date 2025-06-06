import c4d
from c4d import gui

def get_all_objects(op, out):
    """Recursively collects all objects in the scene."""
    while op:
        out.append(op)
        get_all_objects(op.GetDown(), out)
        op = op.GetNext()

def get_centered_points(obj):
    """
    Returns world-space points centered on the object's centroid,
    ignoring its pivot.
    """
    pts = obj.GetAllPoints()
    if not pts:
        return []
    mg = obj.GetMg()
    world_pts = [mg * p for p in pts]
    center = c4d.Vector()
    for p in world_pts:
        center += p
    center /= len(world_pts)
    return [p - center for p in world_pts]

def points_match(a_pts, b_pts, tol):
    """
    True if every point in a_pts has a match in b_pts within tol,
    and vice versa.
    """
    for pa in a_pts:
        if not any((pa - pb).GetLength() <= tol for pb in b_pts):
            return False
    for pb in b_pts:
        if not any((pb - pa).GetLength() <= tol for pa in a_pts):
            return False
    return True

def are_shapes_equal_by_vertices(a, b, tol):
    """
    Compare two polygon objects by their centered vertex clouds.
    """
    if not (a.CheckType(c4d.Opolygon) and b.CheckType(c4d.Opolygon)):
        return False
    if a.GetPointCount() != b.GetPointCount():
        return False
    return points_match(get_centered_points(a),
                        get_centered_points(b),
                        tol)

def deduplicate_selection(selection, tol):
    """
    From the selected polygons, keep only one representative per unique shape.
    """
    unique = []
    for obj in selection:
        if not any(are_shapes_equal_by_vertices(obj, u, tol) for u in unique):
            unique.append(obj)
    return unique

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    # 1) Capture original polygon selection
    original = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    polys = [o for o in original if o.CheckType(c4d.Opolygon)]
    if not polys:
        gui.MessageDialog("Please select one or more polygon objects.")
        return

    # 2) Get tolerance from user
    tol_str = gui.InputDialog("Enter matching tolerance (e.g. 0.01):", "0.01")
    if tol_str is None:
        return
    try:
        tol = float(tol_str)
    except ValueError:
        gui.MessageDialog("Invalid tolerance.")
        return

    # 3) Deduplicate your selection
    masters = deduplicate_selection(polys, tol)

    # 4) Scan entire scene
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)

    # 5) For each master, find and select any other polygon matching by vertex cloud
    found = False
    for m in masters:
        for o in all_objs:
            if o in masters:
                continue
            if are_shapes_equal_by_vertices(m, o, tol):
                o.SetBit(c4d.BIT_ACTIVE)
                found = True

    c4d.EventAdd()

    # 6) If none found, notify
    if not found:
        gui.MessageDialog("No duplicates found.")

if __name__ == '__main__':
    main()
