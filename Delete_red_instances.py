import c4d

def remove_orphan_instances(obj, doc):
    if not obj:
        return
    
    to_delete = []
    
    # Рекурсивный обход всех объектов
    def traverse_hierarchy(op):
        while op:
            next_obj = op.GetNext()
            if op.GetType() == c4d.Oinstance:
                ref = op[c4d.INSTANCEOBJECT_LINK]
                if ref is None:  # Проверяем, есть ли референс
                    to_delete.append(op)
            traverse_hierarchy(op.GetDown())
            op = next_obj
    
    traverse_hierarchy(obj)
    
    # Удаляем найденные объекты
    for inst in to_delete:
        doc.AddUndo(c4d.UNDOTYPE_DELETE, inst)
        inst.Remove()
    
    c4d.EventAdd()

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    
    doc.StartUndo()
    remove_orphan_instances(doc.GetFirstObject(), doc)
    doc.EndUndo()
    
if __name__ == "__main__":
    main()