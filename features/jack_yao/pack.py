from PySide6.QtWidgets import QWidget

from app.models.pack import FeaturePack


class CatalogPage(QWidget):
    ...


class JackYaoPack(FeaturePack):
    packId = "jack_yao"

    def pages(self):
        return [CatalogPage()]
