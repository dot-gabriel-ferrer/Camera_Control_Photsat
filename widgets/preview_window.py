from PyQt5 import QtWidgets, QtCore, QtGui

class PreviewWindow(QtWidgets.QMainWindow):
    """
    Independent window for displaying the camera preview.
    Allows zooming (using the mouse wheel) and panning the image.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independent Preview Window")
        
        # Create a QGraphicsView and its associated scene
        self.graphicsView = QtWidgets.QGraphicsView()
        self.setCentralWidget(self.graphicsView)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        
        # Add the graphical item that will contain the image
        self.pixmapItem = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixmapItem)
        
        # Configure panning mode and transformation anchor
        self.graphicsView.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.graphicsView.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        
        # Variable to control the zoom level
        self._zoom = 0

    def setImage(self, image):
        """
        Updates the displayed image.
        :param image: QImage or QPixmap instance.
        """
        if isinstance(image, QtGui.QImage):
            pixmap = QtGui.QPixmap.fromImage(image)
        elif isinstance(image, QtGui.QPixmap):
            pixmap = image
        else:
            return

        self.pixmapItem.setPixmap(pixmap)
        # Convert QRect to QRectF and update the scene,
        # but do not reset the zoom to keep the current transformation.
        self.scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
        # Note: The resetZoom() call is removed to preserve the zoom level.

    def resetZoom(self):
        """
        Resets the transformation of the QGraphicsView.
        """
        self.graphicsView.resetTransform()
        self._zoom = 0

    def wheelEvent(self, event):
        """
        Handles the mouse wheel event to apply zoom.
        """
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor

        # Position in the scene before zooming
        oldPos = self.graphicsView.mapToScene(event.pos())

        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
            self._zoom += 1
        else:
            zoomFactor = zoomOutFactor
            self._zoom -= 1

        # Limit the zoom level
        if self._zoom < -10:
            self._zoom = -10
            return
        if self._zoom > 20:
            self._zoom = 20
            return

        self.graphicsView.scale(zoomFactor, zoomFactor)

        # Keep the point under the cursor in the same position
        newPos = self.graphicsView.mapToScene(event.pos())
        delta = newPos - oldPos
        self.graphicsView.translate(delta.x(), delta.y())
