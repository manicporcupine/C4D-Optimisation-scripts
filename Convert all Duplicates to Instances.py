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
    hash_data = tuple((p.x, p.y, p.z) for p in sorted_points) + \
                tuple((p.a, p.b, p.c, p.d) for p in sorted_polys)
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

def phase_a_relink_instances(doc, objects, master_map):
    """
    For each instance object in the scene, trace its reference chain.
    If its ultimate polygon master has a geometry hash that exists in master_map,
    update its link to point to the stored master and rename it.
    (Transformation is not changed, so world position remains intact.)
    """
    for obj in objects:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            master = get_master_polygon(ref)
            if master:
                h = get_polygons_hash(master)
                if h is None:
                    continue
                if h in master_map:
                    new_master = master_map[h]
                    if obj[c4d.INSTANCEOBJECT_LINK] != new_master:
                        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                        obj[c4d.INSTANCEOBJECT_LINK] = new_master
                        obj.SetName(new_master.GetName() + "_instance")
                    # No transformation change is made, so world position is preserved.

def transfer_children(doc, old_obj, new_parent):
    """
    Transfers all children of 'old_obj' to 'new_parent', preserving each child's world transformation.
    An undo change is recorded for each child.
    """
    child = old_obj.GetDown()
    while child:
        next_child = child.GetNext()  # Store next pointer before reparenting.
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, child)
        child_world = child.GetMg()
        child.Remove()
        doc.InsertObject(child, parent=new_parent)
        if new_parent:
            new_local = ~new_parent.GetMg() * child_world
            child.SetMl(new_local)
        else:
            child.SetMg(child_world)
        child = next_child

def phase_b_replace_duplicates(doc, objects, master_map):
    """
    For every polygon object (other than the stored master) that is identical to its stored master,
    create a new instance referencing the stored master, transfer all its children to the new instance,
    copy texture tags, insert it into the same hierarchy at the same order as the duplicate,
    rename it, and remove the duplicate.
    
    The local matrix is computed so that the new instance's global (world) matrix equals the duplicate's.
    """
    for obj in list(objects):  # iterate over a copy
        if obj.CheckType(c4d.Opolygon):
            h = get_polygons_hash(obj)
            if h is None:
                continue
            if h in master_map and obj != master_map[h]:
                parent = obj.GetUp()
                instance_world = obj.GetMg()
                if parent:
                    inv_parent_mg = ~parent.GetMg()
                    local_m = inv_parent_mg * instance_world
                else:
                    local_m = instance_world

                instance = c4d.BaseObject(c4d.Oinstance)
                instance[c4d.INSTANCEOBJECT_LINK] = master_map[h]
                instance.SetName(master_map[h].GetName() + "_instance")
                instance.SetMl(local_m)
                # Preserve order: insert instance at the duplicate's predecessor.
                pred = obj.GetPred()
                doc.InsertObject(instance, parent=parent, pred=pred)
                
                # Transfer children from the duplicate to the new instance.
                transfer_children(doc, obj, instance)
                
                # Copy texture tags.
                tag = obj.GetFirstTag()
                while tag:
                    if tag.CheckType(c4d.Ttexture):
                        new_tag = tag.GetClone()
                        instance.InsertTag(new_tag)
                    tag = tag.GetNext()
                
                doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
                doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                obj.Remove()

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

    # Build a master map:
    # For each polygon object, compute its geometry hash.
    # If the hash isn't stored yet, store the object.
    # If it is stored, and the stored object has children while the current object is childless,
    # then update the master to the childless one.
    master_map = {}
    for obj in objects:
        if obj.CheckType(c4d.Opolygon):
            h = get_polygons_hash(obj)
            if h is None:
                continue
            if h not in master_map:
                master_map[h] = obj
            else:
                current_master = master_map[h]
                if current_master.GetDown() is not None and obj.GetDown() is None:
                    master_map[h] = obj

    doc.StartUndo()
    # Phase A: Re-link existing instance objects.
    phase_a_relink_instances(doc, objects, master_map)
    # Phase B: Replace duplicate polygon objects with instances.
    phase_b_replace_duplicates(doc, objects, master_map)
    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
