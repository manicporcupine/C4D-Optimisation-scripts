import c4d
from c4d import gui

def debug(msg):
    """Print to the C4D Console with a prefix."""
    print(f"[ParentDialog] {msg}")

def get_true_selection(doc):
    """
    Return every object with BIT_ACTIVE set—no hierarchy culling—
    so selecting both a parent and its child counts as two.
    """
    sel = []
    def recurse(op):
        while op:
            if op.GetBit(c4d.BIT_ACTIVE):
                sel.append(op)
            recurse(op.GetDown())
            op = op.GetNext()
    recurse(doc.GetFirstObject())
    return sel

class ParentDialog(gui.GeDialog):
    def __init__(self):
        super().__init__()
        self.parent_obj = None
        self.ancestors = []

    def CreateLayout(self):
        self.SetTitle("Set Parent & Put Into")
        self.AddStaticText(1000, c4d.BFH_CENTER, name="Select a parent, then objects!")

        # Row: [Set Parent] + status text
        self.GroupBegin(2000, c4d.BFH_LEFT, cols=2)
        self.AddButton(1001, c4d.BFH_LEFT, name="Set Parent")
        self.AddStaticText(
            1003,
            c4d.BFH_SCALEFIT | c4d.BFV_CENTER,
            initw=150, inith=0,
            name=""
        )
        self.GroupEnd()

        # Put Into button
        self.AddButton(1002, c4d.BFH_LEFT, name="Put Into")
        return True

    def Command(self, id, msg):
        if id == 1001:
            self.set_parent()
        elif id == 1002:
            self.put_into()
        return True

    def set_parent(self):
        doc = c4d.documents.GetActiveDocument()
        sel = get_true_selection(doc)

        # Must pick exactly one parent
        if not sel:
            gui.MessageDialog("Please select one object to be the parent.")
            return
        if len(sel) > 1:
            gui.MessageDialog("Only one object may be set as the parent.")
            return

        self.parent_obj = sel[0]
        self.SetString(1003, f"Parent set: {self.parent_obj.GetName()}")

        # Gather ancestors
        self.ancestors = []
        p = self.parent_obj.GetUp()
        while p:
            self.ancestors.append(p)
            p = p.GetUp()

        names = ", ".join(o.GetName() for o in self.ancestors) or "None"
        debug(f"Ancestors of '{self.parent_obj.GetName()}': {names}")

    def put_into(self):
        doc = c4d.documents.GetActiveDocument()
        if not self.parent_obj:
            gui.MessageDialog("No parent set! Use 'Set Parent' first.")
            return

        sel = get_true_selection(doc)
        if not sel:
            gui.MessageDialog("Select objects to move under the parent.")
            return

        # Prevent putting into itself
        for obj in sel:
            if obj is self.parent_obj:
                gui.MessageDialog(f"Cannot put '{obj.GetName()}' into itself.")
                return

        # Prevent immediate-child redundancy
        for obj in sel:
            if obj.GetUp() is self.parent_obj:
                gui.MessageDialog(
                    f"'{self.parent_obj.GetName()}' is already a parent of '{obj.GetName()}'."
                )
                return

        # Error if parent_obj is a child of any selected object
        for obj in sel:
            if obj in self.ancestors:
                gui.MessageDialog(
                    f"Cannot put '{obj.GetName()}' into its descendant '{self.parent_obj.GetName()}'."
                )
                return

        # Build list of top-level selected objects to preserve internal structure
        to_reparent = [obj for obj in sel if obj.GetUp() not in sel]
        debug(f"Top-level to reparent: {[o.GetName() for o in to_reparent]}")

        # Normal reparent: move each top-level under parent_obj
        doc.StartUndo()
        for obj in to_reparent:
            wm = obj.GetMg()
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
            obj.InsertUnder(self.parent_obj)
            obj.SetMg(wm)
        doc.EndUndo()
        c4d.EventAdd()

# -----------------------------------------------------------------------------
# Launch the dialog
# -----------------------------------------------------------------------------
global dlg
dlg = ParentDialog()


def main():
    dlg.Open(
        dlgtype=c4d.DLG_TYPE_ASYNC,
        pluginid=1234567,
        defaultw=350,
        defaulth=160
    )

if __name__ == "__main__":
    main()
