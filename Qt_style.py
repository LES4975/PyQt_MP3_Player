# Qt_style.py
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

def create_default_shadow(offset, blur, color):
    shadow = QGraphicsDropShadowEffect()
    shadow.setOffset(*offset)
    shadow.setBlurRadius(blur)
    shadow.setColor(color)
    return shadow
