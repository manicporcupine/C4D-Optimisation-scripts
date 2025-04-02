import c4d
from c4d import gui

class RenameDialog(gui.GeDialog):
    def CreateLayout(self):
        self.SetTitle("Rename Selected Objects")  # Window title
        
        # Input field
        self.AddStaticText(1000, c4d.BFH_LEFT, name="Enter Word:")
        self.AddEditText(1001, c4d.BFH_SCALEFIT, initw=200)

        # Buttons
        self.AddButton(2001, c4d.BFH_SCALEFIT, name="Add as Prefix")
        self.AddButton(2002, c4d.BFH_SCALEFIT, name="Add as Postfix")
        self.AddButton(2003, c4d.BFH_SCALEFIT, name="Rename Numbered")  # New button

        return True

    def Command(self, id, msg):
        word = self.GetString(1001)  # Get the input text
        doc = c4d.documents.GetActiveDocument()
        selected = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

        if not word:
            gui.MessageDialog("Please enter a word.")
            return True

        if not selected:
            gui.MessageDialog("No objects selected.")
            return True

        # Apply prefix, postfix, or numbered rename
        if id == 2001:  # Prefix button
            for obj in selected:
                obj.SetName(f"{word}_{obj.GetName()}")
        
        elif id == 2002:  # Postfix button
            for obj in selected:
                obj.SetName(f"{obj.GetName()}_{word}")

        elif id == 2003:  # Rename Numbered
            for i, obj in enumerate(selected, start=1):
                obj.SetName(f"{word}_{i}")

        c4d.EventAdd()  # Refresh Cinema 4D
        return True

# Open as a **non-blocking** dialog (so C4D remains usable)
def main():
    global dlg  # Keep reference to prevent garbage collection
    dlg = RenameDialog()
    dlg.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=300, defaulth=100)

if __name__ == "__main__":
    main()
