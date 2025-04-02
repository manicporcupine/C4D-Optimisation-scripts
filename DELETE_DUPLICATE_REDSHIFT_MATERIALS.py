# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
import c4d.gui
import maxon

RED_SHIFT_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

def get_node_signature(node):
    """
    Builds a signature for a single node by taking its asset ID and appending
    all immediate input port IDs and their effective values.
    """
    assetId_list = node.GetValue("net.maxon.node.attribute.assetid")
    if not assetId_list:
        return ""
    assetId = assetId_list[0]
    node_signature = str(assetId)
    inputs = node.GetInputs()
    if inputs:
        # Iterate over immediate children (input ports)
        for port in inputs.GetChildren():
            # Use port's ID as its identifier because GetName() is not available
            port_id = str(port.GetId())
            try:
                port_value = port.GetValue("effectivevalue")
            except Exception:
                port_value = "N/A"
            node_signature += f"|{port_id}:{port_value}"
    return node_signature

def get_material_signature(material):
    """
    Calculates a unique signature for the material by concatenating the signatures
    of all nodes in its node graph. The signature for each node includes its asset ID,
    plus the IDs and effective values of its input ports.
    """
    nodeMat = material.GetNodeMaterialReference()
    if not nodeMat or not nodeMat.HasSpace(RED_SHIFT_NODESPACE):
        return None
    graph = nodeMat.GetGraph(RED_SHIFT_NODESPACE)
    if graph.IsNullValue():
        return None
    root = graph.GetViewRoot()
    signatures = []
    # Iterate over all inner nodes of the graph
    for node in root.GetInnerNodes(mask=maxon.NODE_KIND.NODE, includeThis=False):
        sig = get_node_signature(node)
        if sig:
            signatures.append(sig)
    signatures.sort()
    signature_str = "|".join(signatures)
    return signature_str

def get_all_objects(doc):
    """
    Recursively returns all objects in the document.
    """
    obj = doc.GetFirstObject()
    while obj:
        yield obj
        for child in get_all_children(obj):
            yield child
        obj = obj.GetNext()

def get_all_children(obj):
    """
    Recursively returns all children of the given object.
    """
    child = obj.GetDown()
    while child:
        yield child
        for subchild in get_all_children(child):
            yield subchild
        child = child.GetNext()

def main():
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        return

    # 1. Collect all materials with Redshift node space
    materials = doc.GetMaterials()
    redshift_materials = []
    for mat in materials:
        nodeMat = mat.GetNodeMaterialReference()
        if nodeMat and nodeMat.HasSpace(RED_SHIFT_NODESPACE):
            redshift_materials.append(mat)
    
    # 2. Calculate the signature for each material and determine duplicates
    sig_to_material = {}
    duplicates = []
    for mat in redshift_materials:
        sig = get_material_signature(mat)
        if sig is None:
            continue
        if sig in sig_to_material:
            duplicates.append(mat)
        else:
            sig_to_material[sig] = mat
    
    if not duplicates:
        print("No duplicates found.")
        return
    
    print(f"Found {len(duplicates)} duplicates.")

    # 3. Get the list of all objects and update texture tags accordingly
    objects = list(get_all_objects(doc))
    total = len(objects)
    
    for idx, obj in enumerate(objects):
        tag = obj.GetFirstTag()
        while tag:
            if tag.CheckType(c4d.Ttexture):
                currentMat = tag[c4d.TEXTURETAG_MATERIAL]
                if currentMat in duplicates:
                    sig = get_material_signature(currentMat)
                    if sig in sig_to_material:
                        uniqueMat = sig_to_material[sig]
                        tag[c4d.TEXTURETAG_MATERIAL] = uniqueMat
                        print(f"Tag on object '{obj.GetName()}' updated.")
            tag = tag.GetNext()
        # Update progress status
        percent = int((idx + 1) * 100.0 / total)
        c4d.StatusSetBar(percent)
        c4d.StatusSetText(f"Processing object {idx+1} of {total}")
    c4d.StatusClear()
    
    c4d.EventAdd()
    
    # 4. Deselect all materials, then select duplicate materials and execute the delete command.
    allMaterials = doc.GetMaterials()
    for mat in allMaterials:
        mat.DelBit(c4d.BIT_ACTIVE)
    
    for dup in duplicates:
        dup.SetBit(c4d.BIT_ACTIVE)
    c4d.CallCommand(300001024)
    c4d.EventAdd()
    
    c4d.gui.MessageDialog(f"{len(duplicates)} duplicate materials have been removed.")

if __name__=='__main__':
    main()
