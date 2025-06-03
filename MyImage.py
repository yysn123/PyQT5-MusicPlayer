import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class MyImage:
    def __init__(self):
        pass

    @staticmethod
    def circleImage(image_path):
        # 加载图片
        image = QtGui.QPixmap(image_path)
        # 确定尺寸
        size = min(image.width(), image.height())
        # 透明画布
        circle_image = QtGui.QPixmap(size, size)
        circle_image.fill(QtCore.Qt.transparent)
        # 设置渲染
        qp = QtGui.QPainter(circle_image)
        qp.setRenderHints(qp.Antialiasing)
        # 绘制
        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        qp.setClipPath(path)

        image_rect = QtCore.QRect(0, 0, size, size)
        image_rect.moveCenter(image.rect().center())
        qp.drawPixmap(circle_image.rect(), image, image_rect)
        qp.end()

        return circle_image
