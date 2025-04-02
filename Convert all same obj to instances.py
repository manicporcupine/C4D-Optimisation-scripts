# Author: Chat GPT and Dani Zaitcev
# Tested with Cinema 4D 2025.2 and Redshift 2025.4

import c4d

def get_polygons_hash(obj):
    """Генерирует хэш для полигонального объекта (учитывая только его геометрию, без позиции, поворота и масштаба)."""
    if not obj or not obj.CheckType(c4d.Opolygon):
        return None
    
    # Получаем точки в локальных координатах (без мировой матрицы)
    points = obj.GetAllPoints()
    polys = obj.GetAllPolygons()

    # Нормализуем порядок точек, чтобы избежать влияния порядка вершин
    sorted_points = sorted(points, key=lambda v: (round(v.x, 4), round(v.y, 4), round(v.z, 4)))
    sorted_polys = sorted(polys, key=lambda p: (p.a, p.b, p.c, p.d))

    # Создаем уникальный хэш
    hash_data = tuple((p.x, p.y, p.z) for p in sorted_points) + tuple((p.a, p.b, p.c, p.d) for p in sorted_polys)

    return hash(hash_data)  # Возвращаем хэш

def replace_with_instances(doc, objects):
    """Заменяет дубликаты инстансами первого найденного объекта."""
    doc.StartUndo()
    
    seen_hashes = {}  # Словарь для хранения уникальных объектов
    
    for obj in objects:
        obj_hash = get_polygons_hash(obj)
        if obj_hash is None:
            continue
        
        if obj_hash in seen_hashes:
            # Создаем инстанс первого найденного объекта с таким же хэшем
            instance = c4d.BaseObject(c4d.Oinstance)
            instance[c4d.INSTANCEOBJECT_LINK] = seen_hashes[obj_hash]
            instance.SetMg(obj.GetMg())  # Сохраняем мировую матрицу (позицию, поворот и масштаб)
            doc.InsertObject(instance, parent=obj.GetUp())  # Вставляем инстанс в сцену
            doc.AddUndo(c4d.UNDOTYPE_NEW, instance)
            doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
            obj.Remove()  # Удаляем оригинальный объект
        else:
            seen_hashes[obj_hash] = obj  # Запоминаем оригинальный объект
    
    doc.EndUndo()
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    
    objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN) or doc.GetObjects()
    polygon_objects = [obj for obj in objects if obj.CheckType(c4d.Opolygon)]
    
    if not polygon_objects:
        c4d.gui.MessageDialog("Не найдено полигональных объектов.")
        return
    
    replace_with_instances(doc, polygon_objects)

if __name__ == "__main__":
    main()
