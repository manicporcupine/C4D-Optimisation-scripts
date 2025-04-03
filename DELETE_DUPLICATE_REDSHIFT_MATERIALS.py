# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
import c4d.gui
import maxon
import json
import hashlib

RED_SHIFT_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

def normalize_value(value):
    """
    Converts the value to a string. If it can be interpreted as a float, rounds it to 4 decimals.
    Otherwise, returns str(value). Handles None values as well.
    """
    if value is None:
        return "None"
    try:
        f = float(value)
        return f"{f:.4f}"
    except Exception:
        # If value is a maxon.ColorA, format it accordingly
        if isinstance(value, maxon.ColorA):
            return f"ColorA({value.r:.4f},{value.g:.4f},{value.b:.4f},{value.a:.4f})"
        return str(value)

def get_normalized_material_data(material):
    """
    Collects node data from the material in a normalized dictionary.
    Each node dictionary contains:
      - "asset_id": the node's asset ID
      - "ports": a dictionary mapping each port's identifier (using its ID) to its normalized effective value.
    The list of nodes is sorted by asset_id, and each node's ports dictionary is also sorted.
    """
    nodeMat = material.GetNodeMaterialReference()
    if not nodeMat or not nodeMat.HasSpace(RED_SHIFT_NODESPACE):
        return None
    graph = nodeMat.GetGraph(RED_SHIFT_NODESPACE)
    if graph.IsNullValue():
        return None
    root = graph.GetViewRoot()
    nodes = []
    for node in root.GetInnerNodes(mask=maxon.NODE_KIND.NODE, includeThis=False):
        assetId_list = node.GetValue("net.maxon.node.attribute.assetid")
        if not assetId_list:
            continue
        node_data = {"asset_id": str(assetId_list[0]), "ports": {}}
        inputs = node.GetInputs()
        if inputs:
            for port in inputs.GetChildren():
                try:
                    val = port.GetValue("effectivevalue")
                except Exception:
                    val = "N/A"
                node_data["ports"][str(port.GetId())] = normalize_value(val)
        # Sort the ports dictionary by key to ensure determinism.
        node_data["ports"] = dict(sorted(node_data["ports"].items()))
        nodes.append(node_data)
    # Sort the list of nodes by asset_id.
    nodes = sorted(nodes, key=lambda n: n["asset_id"])
    return nodes

def get_normalized_material_signature(material):
    """
    Generates a robust signature for the material by converting its normalized node data
    to a JSON string (with sorted keys) and then hashing that string using SHA256.
    Returns a tuple of (signature_hash, nodes_json).
    """
    nodes = get_normalized_material_data(material)
    if nodes is None:
        return None, None
    nodes_json = json.dumps(nodes, sort_keys=True)
    signature_hash = hashlib.sha256(nodes_json.encode('utf-8')).hexdigest()
    return signature_hash, nodes_json

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
    
    # 2. Calculate the normalized signature for each material and determine duplicates
    sig_to_material = {}
    duplicates = []
    print("=== Debug: Normalized Material Data ===")
    for mat in redshift_materials:
        sig, nodes_json = get_normalized_material_signature(mat)
        print("Material:", mat.GetName())
        print("Signature:", sig)
        print("Normalized Data:", nodes_json)
        print("-----")
        if sig in sig_to_material:
            duplicates.append(mat)
        else:
            sig_to_material[sig] = mat
    
    if not duplicates:
        c4d.gui.MessageDialog("No duplicates found.")
        return
    
    print(f"Found {len(duplicates)} duplicates out of {len(redshift_materials)} materials.")

    # 3. Update texture tags on objects: for each object, if a tag uses a duplicate material,
    # replace it with the unique material (based on matching signature).
    objects = list(get_all_objects(doc))
    total = len(objects)
    for idx, obj in enumerate(objects):
        tag = obj.GetFirstTag()
        while tag:
            if tag.CheckType(c4d.Ttexture):
                currentMat = tag[c4d.TEXTURETAG_MATERIAL]
                if currentMat in duplicates:
                    sig, _ = get_normalized_material_signature(currentMat)
                    if sig in sig_to_material:
                        uniqueMat = sig_to_material[sig]
                        tag[c4d.TEXTURETAG_MATERIAL] = uniqueMat
                        print(f"Tag on object '{obj.GetName()}' updated.")
            tag = tag.GetNext()
        percent = int((idx + 1) * 100.0 / total)
        c4d.StatusSetBar(percent)
        c4d.StatusSetText(f"Processing object {idx+1} of {total}")
    c4d.StatusClear()
    c4d.EventAdd()
    
    # 4. Deselect all materials in the document
    allMaterials = doc.GetMaterials()
    for mat in allMaterials:
        mat.DelBit(c4d.BIT_ACTIVE)
    # Then select duplicate materials
    for dup in duplicates:
        dup.SetBit(c4d.BIT_ACTIVE)
    # Execute the delete command (ID 300001024) in the Material Manager
    c4d.CallCommand(300001024)
    c4d.EventAdd()
    
    c4d.gui.MessageDialog(f"{len(duplicates)} duplicate materials have been removed.")

if __name__=='__main__':
    main()

