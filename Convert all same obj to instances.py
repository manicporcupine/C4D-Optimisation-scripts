# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
from c4d import gui

def get_all_objects(obj, obj_list):
    """Recursively collects all objects in the scene."""
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

def clear_selection(doc):
    """Clears the active selection flag from all objects."""
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)
    for obj in all_objs:
        obj.DelBit(c4d.BIT_ACTIVE)

def get_polygons_hash(obj):
    """
    Generates a hash for a polygonal object (considering only its geometry,
    ignoring position, rotation, and scale).
    """
    if not obj or not obj.CheckType(c4d.Opolygon):
        return None

    points = obj.GetAllPoints()
    polys = obj.GetAllPolygons()

    sorted_points = sorted(points, key=lambda v: (round(v.x, 4), round(v.y, 4), round(v.z, 4)))
    sorted_polys = sorted(polys, key=lambda p: (p.a, p.b, p.c, p.d))

    hash_data = tuple((p.x, p.y, p.z) for p in sorted_points) + tuple((p.a, p.b, p.c, p.d) for p in sorted_polys)
    return hash(hash_data)

def get_master_polygon(obj):
    """
    Traces an object's INSTANCEOBJECT_LINK chain until a polygon object is reached.
    Returns that polygon master (or None if not found).
    """
    while obj and not obj.CheckType(c4d.Opolygon):
        if obj.CheckType(c4d.Oinstance):
            obj = obj[c4d.INSTANCEOBJECT_LINK]
        else:
            break
    return obj

def replace_with_instances(doc, objects):
    """
    Phase A: For polygon objects, record the first encountered master for each unique geometry.
    For instance objects, trace their reference to a polygon master and update their link
    to point to the unique master.
    Then, update the names of all visible instances to "mastername_instance".
    
    Phase B: For each duplicate polygon (a polygon that has the same geometry as a master),
    create a new instance referencing the master, copy texture tags, insert it in the same hierarchy,
    and remove the duplicate.
    """
    doc.StartUndo()
    seen_hashes = {}  # Map: geometry hash -> master polygon object
    duplicate_polys = []  # List of duplicate polygon objects.
    inst_objs = []  # List to store all instance objects.

    # Process objects in scene order.
    for obj in objects:
        if obj.CheckType(c4d.Opolygon):
            h = get_polygons_hash(obj)
            if h is None:
                continue
            if h in seen_hashes:
                duplicate_polys.append(obj)
            else:
                seen_hashes[h] = obj
        elif obj.CheckType(c4d.Oinstance):
            inst_objs.append(obj)
            # For instance objects, trace to get the ultimate polygon master.
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            master = get_master_polygon(ref)
            if master is None:
                continue
            h = get_polygons_hash(master)
            if h is None:
                continue
            if h in seen_hashes:
                new_master = seen_hashes[h]
                if obj[c4d.INSTANCEOBJECT_LINK] != new_master:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = new_master
            else:
                seen_hashes[h] = master

    # Update names of all instance objects.
    for inst in inst_objs:
        master = get_master_polygon(inst[c4d.INSTANCEOBJECT_LINK])
        if master:
            new_name = master.GetName() + "_instance"
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, inst)
            inst.SetName(new_name)

    # Phase B: Replace duplicate polygon objects.
    for dup in duplicate_polys:
        h = get_polygons_hash(dup)
        if h is None or h not in seen_hashes:
            continue
        master = seen_hashes[h]
        instance = c4d.BaseObject(c4d.Oinstance)
        instance[c4d.INSTANCEOBJECT_LINK] = master
        instance.SetName(master.GetName() + "_instance")
        parent = dup.GetUp()
        if parent:
            inv_parent_mg = ~parent.GetMg()
            local_m = inv_parent_mg * dup.GetMg()
            instance.SetMl(local_m)
        else:
            instance.SetMg(dup.GetMg())
        doc.InsertObject(instance, parent=parent, pred=dup)
        # Copy texture tags.
        tag = dup.GetFirstTag()
        while tag:
            if tag.CheckType(c4d.Ttexture):
                new_tag = tag.GetClone()
                instance.InsertTag(new_tag)
            tag = tag.GetNext()
        doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
        doc.AddUndo(c4d.UNDOTYPE_DELETE, dup)
        dup.Remove()

    doc.EndUndo()
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    clear_selection(doc)
    objects = []
    get_all_objects(doc.GetFirstObject(), objects)
    if not objects:
        gui.MessageDialog("No objects found.")
        return

    replace_with_instances(doc, objects)

if __name__ == "__main__":
    main()
