import c4d
from c4d import gui

class ParentDialog(gui.GeDialog):
    def __init__(self):
        super().__init__()
        self.parent_obj = None  # Store the selected parent object

    def CreateLayout(self):
        self.SetTitle("Set Parent & Put Into")  # Set window title

        # Static text for guidance
        self.AddStaticText(1000, c4d.BFH_CENTER, name="Select a parent, then objects!")

        # Buttons
        self.AddButton(1001, c4d.BFH_CENTER, name="Set Parent")  # Set Parent button
        self.AddButton(1002, c4d.BFH_CENTER, name="Put Into")  # Put Into button

        return True  # Ensure the layout is created

    def Command(self, id, msg):
        if id == 1001:  # "Set Parent" button clicked
            self.set_parent()
        elif id == 1002:  # "Put Into" button clicked
            self.put_into()
        
        return True

    def set_parent(self):
        """Stores the selected object as the parent."""
        doc = c4d.documents.GetActiveDocument()
        selected = doc.GetActiveObjects(0)  # Get selected objects

        if not selected:
            gui.MessageDialog("Select an object to be the parent first!")
            return
        
        self.parent_obj = selected[0]  # Store the first selected object
        self.SetTitle(f"Parent Set: {self.parent_obj.GetName()}")  # Update window title

    def put_into(self):
        """Moves selected objects under the stored parent while keeping world coordinates."""
        doc = c4d.documents.GetActiveDocument()
        if not self.parent_obj:
            gui.MessageDialog("No parent set! Use 'Set Parent' first.")
            return

        selected = doc.GetActiveObjects(0)  # Get selected objects
        if not selected:
            gui.MessageDialog("Select objects to move under the parent.")
            return
        
        doc.StartUndo()
        for obj in selected:
            if obj != self.parent_obj:  # Prevent parenting to itself
                world_matrix = obj.GetMg()  # Store world matrix
                
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj.InsertUnder(self.parent_obj)  # Move under parent
                
                obj.SetMg(world_matrix)  # Restore world matrix to maintain position

        doc.EndUndo()
        c4d.EventAdd()  # Refresh scene

# Open dialog globally so it doesn’t close immediately
global dlg
dlg = ParentDialog()

def main():
    dlg.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=1234567, defaultw=300, defaulth=100)

if __name__ == "__main__":
    main()
