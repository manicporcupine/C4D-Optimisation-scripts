# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d

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
    """Generates a hash for a polygonal object (considering only its geometry, without position, rotation, and scale)."""
    if not obj or not obj.CheckType(c4d.Opolygon):
        return None

    # Get points in local coordinates (without world matrix)
    points = obj.GetAllPoints()
    polys = obj.GetAllPolygons()

    # Normalize the order of points to avoid influence from vertex order
    sorted_points = sorted(points, key=lambda v: (round(v.x, 4), round(v.y, 4), round(v.z, 4)))
    sorted_polys = sorted(polys, key=lambda p: (p.a, p.b, p.c, p.d))

    # Create a unique hash from the sorted geometry data
    hash_data = tuple((p.x, p.y, p.z) for p in sorted_points) + tuple((p.a, p.b, p.c, p.d) for p in sorted_polys)
    return hash(hash_data)

def replace_with_instances(doc, objects):
    """
    Replaces duplicate polygon objects with instances of the first encountered object.
    Ensures that each new instance preserves its world coordinates and remains in the same hierarchy.
    Material (texture) tags from the duplicate object are copied to the new instance.
    """
    doc.StartUndo()
    seen_hashes = {}  # Dictionary to store unique objects by their geometry hash

    for obj in objects:
        obj_hash = get_polygons_hash(obj)
        if obj_hash is None:
            continue

        if obj_hash in seen_hashes:
            # Create an instance of the first found object with the same hash
            instance = c4d.BaseObject(c4d.Oinstance)
            instance[c4d.INSTANCEOBJECT_LINK] = seen_hashes[obj_hash]
            instance.SetName(seen_hashes[obj_hash].GetName() + "_instance")
            parent = obj.GetUp()

            # Preserve world coordinates even if inside a parent (e.g. a null)
            if parent:
                inv_parent_mg = ~parent.GetMg()  # Inverse of parent's global matrix
                local_m = inv_parent_mg * obj.GetMg()  # Compute local matrix relative to parent
                instance.SetMl(local_m)
            else:
                instance.SetMg(obj.GetMg())

            # Insert the instance into the same hierarchy at the same position
            doc.InsertObject(instance, parent=parent, pred=obj)

            # Copy material (texture) tags from the duplicate object to the new instance
            tag = obj.GetFirstTag()
            while tag:
                if tag.CheckType(c4d.Ttexture):
                    new_tag = tag.GetClone()
                    instance.InsertTag(new_tag)
                tag = tag.GetNext()

            doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
            doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
            obj.Remove()  # Remove the original duplicate object
        else:
            seen_hashes[obj_hash] = obj  # Remember the original object

    doc.EndUndo()
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    # Clear any active selection from the scene.
    clear_selection(doc)

    # Recursively gather all objects in the scene, including those nested inside nulls.
    objects = []
    get_all_objects(doc.GetFirstObject(), objects)
    polygon_objects = [obj for obj in objects if obj.CheckType(c4d.Opolygon)]

    if not polygon_objects:
        c4d.gui.MessageDialog("No polygonal objects found.")
        return

    replace_with_instances(doc, polygon_objects)

if __name__ == "__main__":
    main()
