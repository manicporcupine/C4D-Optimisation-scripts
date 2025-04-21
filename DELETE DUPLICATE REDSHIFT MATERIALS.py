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
        if isinstance(value, maxon.ColorA):
            return f"ColorA({value.r:.4f},{value.g:.4f},{value.b:.4f},{value.a:.4f})"
        return str(value)

def collect_ports(port_node, out_dict, prefix=""):
    """
    Recursively walks a GraphNode (which may be an input bundle or a port)
    and, for each leaf port, records its ID and normalized effectivevalue.
    """
    children = port_node.GetChildren()
    if not children:
        try:
            val = port_node.GetValue("effectivevalue")
        except Exception:
            val = "N/A"
        out_dict[prefix + str(port_node.GetId())] = normalize_value(val)
    else:
        for child in children:
            collect_ports(child, out_dict, prefix + str(port_node.GetId()) + ">")

def get_normalized_material_data(material):
    """
    Collects node data from the material in a normalized dictionary.
    Each node dictionary contains:
      - "asset_id": the node's asset ID
      - "ports": a dictionary mapping each leaf-port's identifier (using its ID path) to its normalized effective value.
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
        asset_id_list = node.GetValue("net.maxon.node.attribute.assetid")
        if not asset_id_list:
            continue
        node_data = {"asset_id": str(asset_id_list[0]), "ports": {}}
        inputs = node.GetInputs()
        if inputs:
            collect_ports(inputs, node_data["ports"])
        node_data["ports"] = dict(sorted(node_data["ports"].items()))
        nodes.append(node_data)
    return sorted(nodes, key=lambda n: n["asset_id"])

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
    sig_hash = hashlib.sha256(nodes_json.encode('utf-8')).hexdigest()
    return sig_hash, nodes_json

def get_all_objects(doc):
    """
    Recursively yields all objects in the document.
    """
    obj = doc.GetFirstObject()
    while obj:
        yield obj
        for child in get_all_children(obj):
            yield child
        obj = obj.GetNext()

def get_all_children(obj):
    """
    Recursively yields all children of the given object.
    """
    child = obj.GetDown()
    while child:
        yield child
        for sub in get_all_children(child):
            yield sub
        child = child.GetNext()

def main():
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        return

    # 1. Collect all Redshift node-based materials
    materials = doc.GetMaterials()
    redshift_mats = []
    for mat in materials:
        nm = mat.GetNodeMaterialReference()
        if nm and nm.HasSpace(RED_SHIFT_NODESPACE):
            redshift_mats.append(mat)

    # 2. Compute signatures and find duplicates
    sig_map = {}
    duplicates = []
    for mat in redshift_mats:
        sig, _ = get_normalized_material_signature(mat)
        if sig in sig_map:
            duplicates.append(mat)
        else:
            sig_map[sig] = mat

    if not duplicates:
        c4d.gui.MessageDialog("No duplicates found.")
        return

    print(f"Found {len(duplicates)} duplicate materials out of {len(redshift_mats)}.")

    # 3. Remap texture tags on all objects
    objs = list(get_all_objects(doc))
    total = len(objs)
    for idx, obj in enumerate(objs):
        tag = obj.GetFirstTag()
        while tag:
            if tag.CheckType(c4d.Ttexture):
                cur = tag[c4d.TEXTURETAG_MATERIAL]
                if cur in duplicates:
                    sig, _ = get_normalized_material_signature(cur)
                    keep = sig_map.get(sig)
                    if keep:
                        tag[c4d.TEXTURETAG_MATERIAL] = keep
            tag = tag.GetNext()
        pct = int((idx + 1) * 100.0 / total)
        c4d.StatusSetBar(pct)
        c4d.StatusSetText(f"Processing object {idx+1} of {total}")
    c4d.StatusClear()
    c4d.EventAdd()

    # 4. Delete duplicate materials via Material Manager
    for m in doc.GetMaterials():
        m.DelBit(c4d.BIT_ACTIVE)
    for dup in duplicates:
        dup.SetBit(c4d.BIT_ACTIVE)
    c4d.CallCommand(300001024)  # Delete selected materials
    c4d.EventAdd()

    c4d.gui.MessageDialog(f"{len(duplicates)} duplicate materials have been removed.")

if __name__ == "__main__":
    main()
