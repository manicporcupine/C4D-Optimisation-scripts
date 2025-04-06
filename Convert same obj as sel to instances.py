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

def objects_are_identical(obj1, obj2):
    """
    Checks if two polygonal objects are identical (ignoring position, rotation, and scale).
    """
    if obj1.GetPolygonCount() != obj2.GetPolygonCount():
        return False
    if obj1.GetPointCount() != obj2.GetPointCount():
        return False

    points1 = [obj1.GetPoint(i) for i in range(obj1.GetPointCount())]
    points2 = [obj2.GetPoint(i) for i in range(obj2.GetPointCount())]
    return set(points1) == set(points2)

def get_master_polygon(obj):
    """
    Traces an object's INSTANCEOBJECT_LINK chain until a polygon object is reached.
    Returns that polygon master or None.
    """
    while obj and not obj.CheckType(c4d.Opolygon):
        if obj.CheckType(c4d.Oinstance):
            obj = obj[c4d.INSTANCEOBJECT_LINK]
        else:
            break
    return obj

def transfer_children(doc, old_obj, new_parent):
    """
    Transfers all children of 'old_obj' to 'new_parent', preserving each child's world transformation.
    An undo change is recorded for each child so that the reparenting is fully undoable.
    """
    child = old_obj.GetDown()
    while child:
        next_child = child.GetNext()  # store next pointer before reparenting.
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, child)  # record parent's change for this child.
        child_world = child.GetMg()
        child.Remove()
        doc.InsertObject(child, parent=new_parent)
        if new_parent:
            new_local = ~new_parent.GetMg() * child_world
            child.SetMl(new_local)
        else:
            child.SetMg(child_world)
        child = next_child

def phase_a_relink_instances(doc, objects, selected):
    """
    For each instance object in the scene, trace its reference chain and, if its ultimate
    polygon master is identical to 'selected', update its link to point to 'selected'
    and rename it.
    """
    for obj in objects:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            master = get_master_polygon(ref)
            if master and objects_are_identical(selected, master):
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj[c4d.INSTANCEOBJECT_LINK] = selected
                obj.SetName(selected.GetName() + "_instance")

def phase_b_replace_duplicates(doc, objects, selected):
    """
    For every polygon object (other than 'selected') that is identical to 'selected',
    create a new instance referencing 'selected', transfer all its children to the new instance,
    copy texture tags, insert it into the same hierarchy, rename it, and then remove the duplicate.
    """
    for obj in list(objects):  # iterate over a copy
        if obj.CheckType(c4d.Opolygon) and obj != selected and objects_are_identical(selected, obj):
            parent = obj.GetUp()
            instance_world = obj.GetMg()
            if parent:
                inv_parent_mg = ~parent.GetMg()
                local_m = inv_parent_mg * instance_world
            else:
                local_m = instance_world

            instance = c4d.BaseObject(c4d.Oinstance)
            instance[c4d.INSTANCEOBJECT_LINK] = selected
            instance.SetName(selected.GetName() + "_instance")
            instance.SetMl(local_m)
            doc.InsertObject(instance, parent=parent, pred=obj)

            # Transfer all children from the duplicate to the new instance.
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

    selected = doc.GetActiveObject()
    if not selected or not selected.CheckType(c4d.Opolygon):
        gui.MessageDialog("Please select a polygonal object.")
        return

    # If the selected object has children, ask for confirmation.
    if selected.GetDown():
        if not gui.QuestionDialog("The selected object contains child objects.\n"
                                   "Are you sure you want to convert other copies to instances of this object?"):
            return

    doc.StartUndo()
    clear_selection(doc)
    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)
    if not all_objects:
        gui.MessageDialog("No objects found.")
        return

    # Phase A: Re-link any existing instance objects.
    phase_a_relink_instances(doc, all_objects, selected)
    # Phase B: Replace duplicate polygon objects (preserving the child hierarchy) with instances.
    phase_b_replace_duplicates(doc, all_objects, selected)
    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
