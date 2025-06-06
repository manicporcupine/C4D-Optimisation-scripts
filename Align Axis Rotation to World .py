import c4d
from c4d import utils


def VectorEqual(v1, v2, eps=1e-6):
    """Сравнивает два вектора с учётом погрешности."""
    return (abs(v1.x - v2.x) < eps and
            abs(v1.y - v2.y) < eps and
            abs(v1.z - v2.z) < eps)


def CollectDescendants(obj, out):
    """Рекурсивно собирает всех потомков объекта."""
    for c in obj.GetChildren():
        out.append(c)
        CollectDescendants(c, out)


def BakePolygonAxisWithLogs(doc, obj):
    name = obj.GetName() or "<без имени>"
    print(f"\n--- Baking Polygon Axis for '{name}' ---")

    M_before = obj.GetMg()
    hpb_before = utils.MatrixToHPB(M_before)
    print("Global Matrix BEFORE:\n", M_before)
    print("HPB BEFORE:", hpb_before)
    print("Basis BEFORE:", M_before.v1, M_before.v2, M_before.v3, "Off:", M_before.off)

    M_target = c4d.Matrix()
    M_target.off = M_before.off
    hpb_target = utils.MatrixToHPB(M_target)
    print("\nGlobal Matrix TARGET:\n", M_target)
    print("HPB TARGET:", hpb_target)
    print("Basis TARGET:", M_target.v1, M_target.v2, M_target.v3, "Off:", M_target.off)

    change = (~M_target) * M_before
    print("\nChange Matrix (for points):\n", change)

    pts = obj.GetAllPoints()
    new_pts = [change * p for p in pts]
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
    obj.SetAllPoints(new_pts)
    obj.SetMg(M_target)

    M_after = obj.GetMg()
    hpb_after = utils.MatrixToHPB(M_after)
    print("\nGlobal Matrix AFTER:\n", M_after)
    print("HPB AFTER:", hpb_after)
    print("Basis AFTER:", M_after.v1, M_after.v2, M_after.v3, "Off:", M_after.off)

    world_basis = (c4d.Vector(1,0,0), c4d.Vector(0,1,0), c4d.Vector(0,0,1))
    basis_ok = (VectorEqual(M_after.v1, world_basis[0]) and
                VectorEqual(M_after.v2, world_basis[1]) and
                VectorEqual(M_after.v3, world_basis[2]))
    off_ok = VectorEqual(M_after.off, M_target.off)
    print(f"\n→ Basis aligned? {basis_ok}")
    print(f"→ Off preserved?   {off_ok}")


def BakeNullAxisPreserveDescendants(doc, obj):
    name = obj.GetName() or "<без имени>"
    print(f"\n--- Baking Null Axis for '{name}' and preserving descendants ---")

    # запомним мировые матрицы ВСЕХ потомков
    descendants = []
    CollectDescendants(obj, descendants)
    world_mats = {c: c.GetMg() for c in descendants}
    print("Descendants to restore:", [c.GetName() for c in descendants])

    M_before = obj.GetMg()
    print("\nNull Global Matrix BEFORE:\n", M_before)
    print("Basis BEFORE:", M_before.v1, M_before.v2, M_before.v3, "Off:", M_before.off)

    M_target = c4d.Matrix()
    M_target.off = M_before.off
    print("\nNull Global Matrix TARGET:\n", M_target)
    print("Basis TARGET:", M_target.v1, M_target.v2, M_target.v3, "Off:", M_target.off)

    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
    obj.SetMg(M_target)

    # восстановим потомкам их мировые матрицы
    for c, mat in world_mats.items():
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, c)
        c.SetMg(mat)

    M_after = obj.GetMg()
    print("\nNull Global Matrix AFTER:\n", M_after)
    print("Basis AFTER:", M_after.v1, M_after.v2, M_after.v3, "Off:", M_after.off)

    world_basis = (c4d.Vector(1,0,0), c4d.Vector(0,1,0), c4d.Vector(0,0,1))
    basis_ok = (VectorEqual(M_after.v1, world_basis[0]) and
                VectorEqual(M_after.v2, world_basis[1]) and
                VectorEqual(M_after.v3, world_basis[2]))
    off_ok = VectorEqual(M_after.off, M_target.off)
    print(f"\n→ Null basis aligned? {basis_ok}")
    print(f"→ Null off preserved? {off_ok}")


def main():
    doc = c4d.documents.GetActiveDocument()
    sel = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)
    print(f"Найдено объектов в селекции: {len(sel)}")
    if not sel:
        c4d.gui.MessageDialog("Сначала выберите хотя бы один объект.")
        return

    # Собираем список задач: Null и Polygon
    to_process = []
    for obj in sel:
        typ = obj.GetType()
        # Если выбран Null, обрабатываем его и все вложенные Null и Polygon
        if typ == c4d.Onull:
            descendants = []
            CollectDescendants(obj, descendants)
            # сам Null
            to_process.append(('null', obj))
            # вложенные Null и Polygon
            for d in descendants:
                if d.GetType() == c4d.Onull:
                    to_process.append(('null', d))
                if d.GetType() == c4d.Opolygon:
                    to_process.append(('poly', d))
        # Если выбран Polygon, просто добавляем его
        elif typ == c4d.Opolygon:
            to_process.append(('poly', obj))
        # Для других типов генерируем только Polygon-потомков
        else:
            descendants = []
            CollectDescendants(obj, descendants)
            for d in descendants:
                if d.GetType() == c4d.Opolygon:
                    to_process.append(('poly', d))

    # Убираем дубли, сохраняя порядок
    unique = []
    seen = set()
    for kind, o in to_process:
        guid = o.GetGUID()
        if guid not in seen:
            seen.add(guid)
            unique.append((kind, o))

    print(f"Найдено объектов для обработки: {len(unique)}")
    doc.StartUndo()
    for kind, obj in unique:
        if kind == 'null':
            BakeNullAxisPreserveDescendants(doc, obj)
        else:
            BakePolygonAxisWithLogs(doc, obj)
    doc.EndUndo()
    c4d.EventAdd()

if __name__=='__main__':
    main()
