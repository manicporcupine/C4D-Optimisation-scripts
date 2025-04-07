import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    
    active_vp = doc.GetActiveBaseDraw()  # Получаем активный вьюпорт
    if not active_vp:
        return
    
    active_camera = active_vp.GetSceneCamera(doc)  # Получаем активную камеру
    if not active_camera:
        return
    
    doc.StartUndo()
    doc.SetActiveObject(active_camera, mode=c4d.SELECTION_NEW)  # Выбираем камеру
    doc.EndUndo()
    
    c4d.EventAdd()

if __name__ == "__main__":
    main()
