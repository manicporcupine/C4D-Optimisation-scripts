import c4d

def get_all_objects(obj, obj_list):
    """ Рекурсивно собирает все объекты сцены """
    while obj:
        obj_list.append(obj)
        get_all_objects(obj.GetDown(), obj_list)
        obj = obj.GetNext()

def objects_are_identical(obj1, obj2):
    """ Проверяет, совпадают ли два полигональных объекта (без учета положения, поворота и масштаба) """
    if obj1.GetPolygonCount() != obj2.GetPolygonCount():
        return False
    if obj1.GetPointCount() != obj2.GetPointCount():
        return False

    # Проверяем совпадение геометрии (точек и полигонов)
    points1 = [obj1.GetPoint(i) for i in range(obj1.GetPointCount())]
    points2 = [obj2.GetPoint(i) for i in range(obj2.GetPointCount())]

    return set(points1) == set(points2)

def replace_with_instance(doc, original, duplicates):
    """ Заменяет все дубликаты инстансами оригинала с сохранением локальных трансформаций """
    for obj in duplicates:
        instance = c4d.BaseObject(c4d.Oinstance)
        instance.SetName(obj.GetName() + "_Instance")
        instance[c4d.INSTANCEOBJECT_LINK] = original

        # Учитываем локальную матрицу объекта относительно родителя
        parent = obj.GetUp()
        if parent:
            instance.SetMl(obj.GetMl())  # Сохраняем локальную трансформацию
        else:
            instance.SetMg(obj.GetMg())  # Если нет родителя, используем мировую трансформацию

        doc.InsertObject(instance, parent=parent, pred=obj)
        doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
        doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
        obj.Remove()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    selected = doc.GetActiveObject()
    if not selected or not selected.CheckType(c4d.Opolygon):
        c4d.gui.MessageDialog("Выберите полигональный объект.")
        return

    doc.StartUndo()

    # Получаем все объекты сцены
    all_objects = []
    get_all_objects(doc.GetFirstObject(), all_objects)

    duplicates = [obj for obj in all_objects if obj != selected and obj.CheckType(c4d.Opolygon) and objects_are_identical(selected, obj)]

    if duplicates:
        replace_with_instance(doc, selected, duplicates)
        c4d.gui.MessageDialog(f"Найдено и заменено {len(duplicates)} объектов.")
    else:
        c4d.gui.MessageDialog("Не найдено идентичных объектов.")

    doc.EndUndo()
    c4d.EventAdd()

if __name__ == "__main__":
    main()
