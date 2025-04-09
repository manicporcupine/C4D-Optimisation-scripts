# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
from c4d import gui

# ----------------------------------------------------------------------
# Define key parameters for comparing lights.
LIGHT_PARAMETERS = {
    "Color": c4d.LIGHT_COLOR,                         # Vector (r, g, b)
    "Color Temperature": c4d.LIGHT_TEMPERATURE_MAIN,    # float
    "Intensity": c4d.LIGHT_BRIGHTNESS,                # float
    "Type": c4d.LIGHT_TYPE,                           # int (Omni, Spot, etc.)
    "Shadow": c4d.LIGHT_SHADOWTYPE,                   # int (None, Soft, Hard, etc.)
    "Use Inner": c4d.LIGHT_DETAILS_INNERCONE,          # bool
    "Inner Angle": c4d.LIGHT_DETAILS_INNERANGLE,       # float
    "Outer Angle": c4d.LIGHT_DETAILS_OUTERANGLE,       # float
    "Falloff": c4d.LIGHT_DETAILS_FALLOFF,             # int (None, Inverse Square, etc.)
    "Inner Radius": c4d.LIGHT_DETAILS_INNERDISTANCE,   # float
    "Radius/Decay": c4d.LIGHT_DETAILS_OUTERDISTANCE,   # float
    "Photometric Intensity": c4d.LIGHT_PHOTOMETRIC_INTENSITY,  # float
    "Photometric Data": c4d.LIGHT_PHOTOMETRIC_DATA,            # bool
    "Path": c4d.LIGHT_PHOTOMETRIC_FILE                      # str
}

# ----------------------------------------------------------------------
# Recursively collect all objects in the document.
def get_all_objects(op, out):
    while op:
        out.append(op)
        get_all_objects(op.GetDown(), out)
        op = op.GetNext()

# ----------------------------------------------------------------------
# Supported object types: polygons, splines, primitives, and lights.
def is_supported_type(op):
    return op and (
        op.CheckType(c4d.Opolygon) or 
        op.CheckType(c4d.Ospline) or 
        op.GetType() in SUPPORTED_GENERATORS
    )

SUPPORTED_GENERATORS = {
    c4d.Ocube, c4d.Osphere, c4d.Oplatonic, c4d.Ocone,
    c4d.Ocylinder, c4d.Odisc, c4d.Otorus, c4d.Ocapsule,
    c4d.Otube, c4d.Opyramid, c4d.Ofigure, c4d.Oplane,
    c4d.Ooiltank, c4d.Olight, c4d.Orslight,   # standard and Redshift lights
    # Spline primitives:
    c4d.Osplinecircle, c4d.Osplineprofile, c4d.Osplinehelix,
    c4d.Osplinenside, c4d.Ospline4side, c4d.Osplinerectangle,
    c4d.Osplinestar, c4d.Osplinecogwheel,
}

# ----------------------------------------------------------------------
# Checks if an object is a Redshift light.
def is_redshift_light(op):
    return op and op.GetType() == c4d.Orslight

# ----------------------------------------------------------------------
# For Redshift lights, compare using our working method.
def rs_lights_equal(op1, op2):
    data1 = op1.GetDataInstance()
    data2 = op2.GetDataInstance()
    if data1 is None or data2 is None:
        return False
    try:
        dict1 = dict(data1.GetContainerInstance())
        dict2 = dict(data2.GetContainerInstance())
    except Exception:
        return data1 == data2
    return dict1 == dict2

# ----------------------------------------------------------------------
# For standard lights, compare using the key parameters.
def standard_lights_identical(light1, light2):
    for name, pid in LIGHT_PARAMETERS.items():
        try:
            v1 = light1[pid]
        except Exception:
            v1 = None
        try:
            v2 = light2[pid]
        except Exception:
            v2 = None
        if v1 != v2:
            # For debugging, you may uncomment the following line:
            # print(f"Difference in {name}: Light1 = {v1}, Light2 = {v2}")
            return False
    return True

# ----------------------------------------------------------------------
# Overall comparison of two objects.
def objects_are_identical(op1, op2):
    if not op1 or not op2:
        return False
    if op1.GetType() != op2.GetType():
        return False
    if op1.CheckType(c4d.Opolygon):
        if op1.GetPolygonCount() != op2.GetPolygonCount():
            return False
        if op1.GetPointCount() != op2.GetPointCount():
            return False
        return set(op1.GetAllPoints()) == set(op2.GetAllPoints())
    if op1.CheckType(c4d.Ospline):
        if op1[c4d.SPLINEOBJECT_TYPE] != op2[c4d.SPLINEOBJECT_TYPE]:
            return False
        if op1.GetSegmentCount() != op2.GetSegmentCount():
            return False
        if op1.GetPointCount() != op2.GetPointCount():
            return False
        return set(op1.GetAllPoints()) == set(op2.GetAllPoints())
    if op1.GetType() in (c4d.Olight, c4d.Orslight):
        if op1.GetType() == c4d.Orslight:
            return rs_lights_equal(op1, op2)
        else:
            return standard_lights_identical(op1, op2)
    return op1.GetDataInstance() == op2.GetDataInstance()

# ----------------------------------------------------------------------
# Among selected objects, return only unique (canonical) masters.
def get_canonical_masters(selected):
    canonical = []
    for obj in selected:
        # Skip instance objects.
        if obj.CheckType(c4d.Oinstance):
            continue
        duplicateFound = False
        for canon in canonical:
            if objects_are_identical(obj, canon):
                duplicateFound = True
                break
        if not duplicateFound:
            canonical.append(obj)
    return canonical

# ----------------------------------------------------------------------
# Follow instance links to retrieve the underlying master object.
def get_master_object(obj):
    while obj and is_supported_type(obj):
        if obj.CheckType(c4d.Oinstance):
            obj = obj[c4d.INSTANCEOBJECT_LINK]
        else:
            break
    return obj

# ----------------------------------------------------------------------
# Transfer children from an object to a new parent.
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

# ----------------------------------------------------------------------
# Update instance objects that reference a duplicate (or master).
def relink_instances(doc, all_objs, master, dup_obj=None):
    for obj in all_objs:
        if obj.CheckType(c4d.Oinstance):
            ref = obj[c4d.INSTANCEOBJECT_LINK]
            real = get_master_object(ref)
            if dup_obj:
                if real == dup_obj:
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = master
                    obj.SetName(master.GetName() + "_instance")
            else:
                if real and objects_are_identical(master, real):
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                    obj[c4d.INSTANCEOBJECT_LINK] = master
                    obj.SetName(master.GetName() + "_instance")

# ----------------------------------------------------------------------
# Replace duplicates in the scene with an instance of the canonical master.
def replace_duplicates_with_canonical(doc, all_objs, canonical):
    total_replacements = 0
    canonical_set = set(canonical)
    for master in canonical:
        for obj in list(all_objs):
            # Skip if object is one of the canonical masters.
            if obj in canonical_set:
                continue
            if is_supported_type(obj) and objects_are_identical(master, obj):
                parent = obj.GetUp()
                world_mtx = obj.GetMg()
                local_mtx = ~parent.GetMg() * world_mtx if parent else world_mtx

                relink_instances(doc, all_objs, master, dup_obj=obj)

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
                total_replacements += 1
    return total_replacements

# ----------------------------------------------------------------------
# Main function.
def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document found.")
        return

    # Step 1: Get selected supported objects.
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    if not selection:
        gui.MessageDialog("Please select polygon, spline, primitive, or light objects.")
        return

    # Filter out only supported objects.
    masters = [obj for obj in selection if is_supported_type(obj)]
    if not masters:
        gui.MessageDialog("No supported objects found in selection.")
        return

    # Step 2: Among the selected objects, get only canonical masters.
    canonical = get_canonical_masters(masters)
    # Optionally update active selection to canonical masters.
    try:
        doc.SetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE, canonical)
    except Exception:
        pass

    # Step 3: Gather all objects in the scene.
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)

    doc.StartUndo()
    # Step 4: Relink existing instances (points from any duplicate to canonical master).
    for master in canonical:
        relink_instances(doc, all_objs, master)

    # Step 5: Replace duplicates (non-canonical) in the entire scene with instances of canonical masters.
    total_replacements = replace_duplicates_with_canonical(doc, all_objs, canonical)
    doc.EndUndo()
    c4d.EventAdd()

    # Step 6: If no duplicates were found, show a dialog.
    if total_replacements == 0:
        gui.MessageDialog("No duplicates found.")

if __name__ == "__main__":
    main()
