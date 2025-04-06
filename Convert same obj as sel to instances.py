# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4


import c4d

def get_all_objects(obj, obj_list):
    """Recursively collects all objects in the scene."""
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

def objects_are_identical(obj1, obj2):
    """Checks if two polygonal objects are identical (ignoring position, rotation, and scale)."""
    if obj1.GetPolygonCount() != obj2.GetPolygonCount():
        return False
    if obj1.GetPointCount() != obj2.GetPointCount():
        return False

    # Check if the geometry (points and polygons) matches
    points1 = [obj1.GetPoint(i) for i in range(obj1.GetPointCount())]
    points2 = [obj2.GetPoint(i) for i in range(obj2.GetPointCount())]

    return set(points1) == set(points2)

def replace_with_instance(doc, original, duplicates):
    """
    Replaces all duplicates with instances of the original,
    preserving local transformations and copying material tags.
    """
    for obj in duplicates:
        instance = c4d.BaseObject(c4d.Oinstance)
        instance.SetName(obj.GetName() + "_Instance")
        instance[c4d.INSTANCEOBJECT_LINK] = original

        # Preserve local transformation relative to parent
        parent = obj.GetUp()
        if parent:
            instance.SetMl(obj.GetMl())  # Use local transformation
        else:
            instance.SetMg(obj.GetMg())  # Use global transformation if no parent

        # Insert the instance in the same hierarchy at the same position
        doc.InsertObject(instance, parent=parent, pred=obj)

        # Copy material (texture) tags from the duplicate to the instance
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
        return

    selected = doc.GetActiveObject()
    if not selected or not selected.CheckType(c4d.Opolygon):
        c4d.gui.MessageDialog("Please select a polygonal object.")
        return

    doc.StartUndo()

    # Collect all objects in the scene
    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)

    duplicates = [obj for obj in all_objects if obj != selected and obj.CheckType(c4d.Opolygon) and objects_are_identical(selected, obj)]

    if duplicates:
        replace_with_instance(doc, selected, duplicates)
        c4d.gui.MessageDialog(f"Found and replaced {len(duplicates)} objects.")
    else:
        c4d.gui.MessageDialog("No identical objects found.")

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
