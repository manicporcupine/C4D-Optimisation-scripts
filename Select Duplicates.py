import c4d
from c4d import gui

# ----------------------------------------------------------------------
# Define key parameters for comparing lights.
LIGHT_PARAMETERS = {
    "Color": c4d.LIGHT_COLOR,
    "Color Temperature": c4d.LIGHT_TEMPERATURE_MAIN,
    "Intensity": c4d.LIGHT_BRIGHTNESS,
    "Type": c4d.LIGHT_TYPE,
    "Shadow": c4d.LIGHT_SHADOWTYPE,
    "Use Inner": c4d.LIGHT_DETAILS_INNERCONE,
    "Inner Angle": c4d.LIGHT_DETAILS_INNERANGLE,
    "Outer Angle": c4d.LIGHT_DETAILS_OUTERANGLE,
    "Falloff": c4d.LIGHT_DETAILS_FALLOFF,
    "Inner Radius": c4d.LIGHT_DETAILS_INNERDISTANCE,
    "Radius/Decay": c4d.LIGHT_DETAILS_OUTERDISTANCE,
    "Photometric Intensity": c4d.LIGHT_PHOTOMETRIC_INTENSITY,
    "Photometric Data": c4d.LIGHT_PHOTOMETRIC_DATA,
    "Path": c4d.LIGHT_PHOTOMETRIC_FILE
}

# ----------------------------------------------------------------------
def get_all_objects(op, out):
    while op:
        out.append(op)
        get_all_objects(op.GetDown(), out)
        op = op.GetNext()

SUPPORTED_GENERATORS = {
    c4d.Ocube, c4d.Osphere, c4d.Oplatonic, c4d.Ocone,
    c4d.Ocylinder, c4d.Odisc, c4d.Otorus, c4d.Ocapsule,
    c4d.Otube, c4d.Opyramid, c4d.Ofigure, c4d.Oplane,
    c4d.Ooiltank, c4d.Olight, c4d.Orslight,
    c4d.Osplinecircle, c4d.Osplineprofile, c4d.Osplinehelix,
    c4d.Osplinenside, c4d.Ospline4side, c4d.Osplinerectangle,
    c4d.Osplinestar, c4d.Osplinecogwheel,
}
def is_supported_type(op):
    return op and (
        op.CheckType(c4d.Opolygon) or
        op.CheckType(c4d.Ospline) or
        op.GetType() in SUPPORTED_GENERATORS
    )

def rs_lights_equal(op1, op2):
    d1 = op1.GetDataInstance(); d2 = op2.GetDataInstance()
    try:
        return dict(d1.GetContainerInstance()) == dict(d2.GetContainerInstance())
    except:
        return d1 == d2

def standard_lights_identical(l1, l2):
    for pid in LIGHT_PARAMETERS.values():
        v1 = l1[pid] if pid in l1.GetDataInstance() else None
        v2 = l2[pid] if pid in l2.GetDataInstance() else None
        if v1 != v2:
            return False
    return True

def objects_are_identical(o1, o2):
    if not o1 or not o2 or o1.GetType() != o2.GetType():
        return False
    t = o1.GetType()
    if o1.CheckType(c4d.Opolygon):
        return (o1.GetPolygonCount() == o2.GetPolygonCount() and
                o1.GetPointCount() == o2.GetPointCount() and
                set(o1.GetAllPoints()) == set(o2.GetAllPoints()))
    if o1.CheckType(c4d.Ospline):
        return (o1[c4d.SPLINEOBJECT_TYPE] == o2[c4d.SPLINEOBJECT_TYPE] and
                o1.GetSegmentCount() == o2.GetSegmentCount() and
                o1.GetPointCount() == o2.GetPointCount() and
                set(o1.GetAllPoints()) == set(o2.GetAllPoints()))
    if t in (c4d.Olight, c4d.Orslight):
        return rs_lights_equal(o1, o2) if t == c4d.Orslight else standard_lights_identical(o1, o2)
    return o1.GetDataInstance() == o2.GetDataInstance()

def get_canonical_masters(selected):
    canonical = []
    for obj in selected:
        if obj.CheckType(c4d.Oinstance):
            continue
        if not any(objects_are_identical(obj, c) for c in canonical):
            canonical.append(obj)
    return canonical

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        gui.MessageDialog("No active document.")
        return

    # 1) capture original selection
    original_sel = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    if not original_sel:
        gui.MessageDialog("Please select some polygon, spline, primitive or light objects.")
        return

    # 2) filter to supported types
    masters = [o for o in original_sel if is_supported_type(o)]
    if not masters:
        gui.MessageDialog("No supported object types in selection.")
        return

    # 3) find canonical masters
    canonical = get_canonical_masters(masters)

    # 4) scan the whole doc
    all_objs = []
    get_all_objects(doc.GetFirstObject(), all_objs)

    # 5) collect duplicates (excluding the masters themselves)
    duplicates = []
    canon_set = set(canonical)
    for m in canonical:
        for o in all_objs:
            if o in canon_set:
                continue
            if is_supported_type(o) and objects_are_identical(m, o):
                duplicates.append(o)

    # 6) add duplicates to the existing selection (preserving original_sel)
    if duplicates:
        for d in duplicates:
            d.SetBit(c4d.BIT_ACTIVE)
        c4d.EventAdd()
    else:
        gui.MessageDialog("No duplicates found.")
        c4d.EventAdd()

if __name__ == "__main__":
    main()
