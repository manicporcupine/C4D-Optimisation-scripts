# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

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

def is_supported_type(obj):
    return obj and obj.CheckType(c4d.Opolygon) or obj.CheckType(c4d.Ospline)

def objects_are_identical(obj1, obj2):
    if not obj1 or not obj2:
        return False

    if obj1.GetType() != obj2.GetType():
        return False

    if obj1.CheckType(c4d.Opolygon):
        if obj1.GetPolygonCount() != obj2.GetPolygonCount():
            return False
        if obj1.GetPointCount() != obj2.GetPointCount():
            return False
        points1 = [obj1.GetPoint(i) for i in range(obj1.GetPointCount())]
        points2 = [obj2.GetPoint(i) for i in range(obj2.GetPointCount())]
        return set(points1) == set(points2)

    elif obj1.CheckType(c4d.Ospline):
        if obj1.GetSegmentCount() != obj2.GetSegmentCount():
            return False
        if obj1.GetPointCount() != obj2.GetPointCount():
            return False
        if obj1[c4d.SPLINEOBJECT_TYPE] != obj2[c4d.SPLINEOBJECT_TYPE]:
            return False
        points1 = [obj1.GetPoint(i) for i in range(obj1.GetPointCount())]
        points2 = [obj2.GetPoint(i) for i in range(obj2.GetPointCount())]
        return set(points1) == set(points2)

    return False

def get_master_object(obj):
    while obj and not is_supported_type(obj):
        if obj.CheckType(c4d.Oinstance):
            obj = obj[c4d.INSTANCEOBJECT_LINK]
        else:
            break
    return obj

def transfer_children(doc, old_obj, new_parent):
    child = old_obj.GetDown()
    while child:
        next_child = child.GetNext()
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, child)
        child_world = child.GetMg()
        child.Remove()
        doc.InsertObject(child, parent=new_parent)
        child.SetMl(~new_parent.GetMg() * child_world if new_parent else child_world)
        child = next_child

def relink_instances(doc, all_objects, master):
    for obj in all_objects:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            real_master = get_master_object(ref)
            if real_master and objects_are_identical(master, real_master):
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj[c4d.INSTANCEOBJECT_LINK] = master
                obj.SetName(master.GetName() + "_instance")

def replace_duplicates(doc, all_objects, master, other_masters):
    for obj in list(all_objects):
        if obj == master or obj in other_masters:
            continue
        if is_supported_type(obj) and objects_are_identical(master, obj):
            parent = obj.GetUp()
            world_mtx = obj.GetMg()
            local_mtx = ~parent.GetMg() * world_mtx if parent else world_mtx

            instance = c4d.BaseObject(c4d.Oinstance)
            instance[c4d.INSTANCEOBJECT_LINK] = master
            instance.SetName(master.GetName() + "_instance")
            instance.SetMl(local_mtx)
            doc.InsertObject(instance, parent=parent, pred=obj)

            transfer_children(doc, obj, instance)

            tag = obj.GetFirstTag()
            while tag:
                if tag.CheckType(c4d.Ttexture):
                    instance.InsertTag(tag.GetClone())
                tag = tag.GetNext()

            doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
            doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
            obj.Remove()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    masters = [obj for obj in selection if is_supported_type(obj)]
    if not masters:
        gui.MessageDialog("Please select one or more polygon or spline objects.")
        return

    if any(m.GetDown() for m in masters):
        if not gui.QuestionDialog("One or more selected objects have children.\n"
                                  "Are you sure you want to convert their duplicates to instances?"):
            return

    doc.StartUndo()
    clear_selection(doc)

    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)

    for master in masters:
        relink_instances(doc, all_objects, master)
        replace_duplicates(doc, all_objects, master, masters)

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
