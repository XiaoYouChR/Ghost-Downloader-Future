from qfluentwidgets import TreeView


class AutoSizingTreeView(TreeView):
    def __init__(self, parent=None, minimumVisibleRows: int = 1, maximumVisibleRows: int = 10):
        super().__init__(parent)
