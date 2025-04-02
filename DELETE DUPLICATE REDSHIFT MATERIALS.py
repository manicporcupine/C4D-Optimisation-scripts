import c4d
import maxon

RED_SHIFT_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

def get_material_signature(material):
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
    obj = doc.GetFirstObject()
    while obj:
        yield obj
        for child in get_all_children(obj):
            yield child
        obj = obj.GetNext()

def get_all_children(obj):
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

    # 1. Собираем все материалы с Redshift узловым пространством
    materials = doc.GetMaterials()
    redshift_materials = []
    for mat in materials:
        nodeMat = mat.GetNodeMaterialReference()
        if nodeMat and nodeMat.HasSpace(RED_SHIFT_NODESPACE):
            redshift_materials.append(mat)
    
    # 2. Вычисляем сигнатуру каждого материала и определяем дубликаты
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
        print("Дубликаты не найдены.")
        return
    
    print(f"Найдено {len(duplicates)} дубликатов.")

    # 3. Получаем список всех объектов и вычисляем их количество
    objects = list(get_all_objects(doc))
    total = len(objects)
    
    # Обходим объекты и обновляем теги, отображая прогресс
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
                        print(f"Тег объекта '{obj.GetName()}' обновлён.")
            tag = tag.GetNext()
        # Обновляем статус выполнения
        percent = int((idx + 1) * 100.0 / total)
        c4d.StatusSetBar(percent)
        c4d.StatusSetText(f"Обработка объекта {idx+1} из {total}")
    
    c4d.StatusClear()  # Очищаем статусную строку

    # 4. Вызываем команду "Удалить неиспользуемые материалы" (ID 12168)
    c4d.CallCommand(12168)
    print("Удаление неиспользуемых материалов выполнено.")
    
    c4d.EventAdd()

if __name__=='__main__':
    main()
