from PySide6.QtWidgets import QWidget


class TitledCardGroup(QWidget):
    def setTitle(self, title: str) -> None:
        pass

    def addCard(self, card: QWidget) -> None:
        pass


class DraftCardGroup(TitledCardGroup):
    def clear(self) -> None:
        pass


class OptionCardGroup(TitledCardGroup):
    def insertCard(self, index: int, card: QWidget) -> None:
        pass

    def options(self) -> dict:
        pass
