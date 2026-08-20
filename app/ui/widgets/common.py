from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


def card(title: str, value: str = "") -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    caption = QLabel(title)
    caption.setObjectName("Muted")
    number = QLabel(value)
    number.setStyleSheet("font-size: 24px; font-weight: 700;")
    layout.addWidget(caption)
    layout.addWidget(number)
    frame.value_label = number
    return frame
