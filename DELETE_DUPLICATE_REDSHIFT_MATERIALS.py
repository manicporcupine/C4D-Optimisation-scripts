# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d
import c4d.gui
import maxon

RED_SHIFT_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

def get_material_signature(material):
    """
    Calculates a unique signature for the material based on its node graph.
    For each node, it uses the asset ID, and for texture nodes (asset ID equal to 
    "com.redshift3d.redshift4c4d.nodes.core.texturesampler") it also includes the 
    value of the "path" port.
    """
    nodeMat = material.GetNodeMaterialReference()
    if not nodeMat or not nodeMat.HasSpace(RED_SHIFT_NODESPACE):
        return None
    graph = nodeMat.GetGraph(RED_SHIFT_NODESPACE)
    if graph.IsNullValue():
        return None
    root = graph.GetViewRoot()
    signature_elements = []
    for node in root.GetInnerNodes(mask=maxon.NODE_KIND.NODE, includeThis=False):
        assetId_list = node.GetValue("net.maxon.node.attribute.assetid")
        if not assetId_list:
            continue
        assetId = assetId_list[0]
        if assetId == maxon.Id("com.redshift3d.redshift4c4d.nodes.core.texturesampler"):
            filenameInPort = node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0")
            if filenameInPort:
                pathPort = filenameInPort.FindChild("path")
                if pathPort:
                    value = pathPort.GetValue("effectivevalue")
                    signature_elements.append(f"{str(assetId)}:{value}")
                else:
                    signature_elements.append(str(assetId))
            else:
                signature_elements.append(str(assetId))
        else:
            signature_elements.append(str(assetId))
    signature_elements.sort()
    signature_str = "|".join(signature_elements)
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
    
    # 4. Deselect all materials in the document
    allMaterials = doc.GetMaterials()
    for mat in allMaterials:
        mat.DelBit(c4d.BIT_ACTIVE)
    
    # Select duplicate materials
    for dup in duplicates:
        dup.SetBit(c4d.BIT_ACTIVE)
    # Execute the delete command (ID 300001024) in the Material Manager
    c4d.CallCommand(300001024)
    c4d.EventAdd()
    
    c4d.gui.MessageDialog(f"{len(duplicates)} duplicate materials have been removed.")

if __name__=='__main__':
    main()
