import c4d
from c4d import gui

class ParentDialog(gui.GeDialog):
    def __init__(self):
        super().__init__()
        self.parent_obj = None  # Will hold the “Set Parent” object

    def CreateLayout(self):
        # Fixed window title
        self.SetTitle("Set Parent & Put Into")

        # Instruction text (still centered)
        self.AddStaticText(1000, c4d.BFH_CENTER, name="Select a parent, then objects!")

        # Row: [Set Parent]   [status text], left-aligned
        self.GroupBegin(2000, c4d.BFH_LEFT, cols=2)
        self.AddButton(1001, c4d.BFH_LEFT, name="Set Parent")
        self.AddStaticText(
            1003,
            c4d.BFH_SCALEFIT | c4d.BFV_CENTER,
            initw=150, inith=0,
            name=""
        )
        self.GroupEnd()

        # “Put Into” button, also left-aligned
        self.AddButton(1002, c4d.BFH_LEFT, name="Put Into")

        return True

    def Command(self, id, msg):
        if id == 1001:
            self.set_parent()
        elif id == 1002:
            self.put_into()
        return True

    def set_parent(self):
        """Store the first selected object as parent and update the status text."""
        doc = c4d.documents.GetActiveDocument()
        sel = doc.GetActiveObjects(0)
        if not sel:
            gui.MessageDialog("Select an object to be the parent first!")
            return

        self.parent_obj = sel[0]
        self.SetString(1003, f"Parent set: {self.parent_obj.GetName()}")

    def put_into(self):
        """Move all other selected objects under the stored parent."""
        doc = c4d.documents.GetActiveDocument()
        if not self.parent_obj:
            gui.MessageDialog("No parent set! Use 'Set Parent' first.")
            return

        sel = doc.GetActiveObjects(0)
        if not sel:
            gui.MessageDialog("Select objects to move under the parent.")
            return

        doc.StartUndo()
        for obj in sel:
            if obj is not self.parent_obj:
                wm = obj.GetMg()
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj.InsertUnder(self.parent_obj)
                obj.SetMg(wm)
        doc.EndUndo()
        c4d.EventAdd()

# Create and open the dialog
global dlg
dlg = ParentDialog()

def main():
    dlg.Open(
        dlgtype=c4d.DLG_TYPE_ASYNC,
        pluginid=1234567,
        defaultw=350,
        defaulth=100
    )

if __name__ == "__main__":
    main()
