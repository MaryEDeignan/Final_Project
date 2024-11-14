import sys
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout

class SwipeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up main window
        self.setWindowTitle("Swipe Animation Example")
        self.setGeometry(100, 100, 400, 300)

        # Set up a main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Create card widget to animate
        self.card = QLabel("Swipe Card", self)
        self.card.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
        self.card.setAlignment(Qt.AlignCenter)
        self.card.setFixedSize(200, 150)

        # Create buttons
        self.like_button = QPushButton("Like", self)
        self.dislike_button = QPushButton("Dislike", self)

        # Connect buttons to swipe actions
        self.like_button.clicked.connect(self.swipe_right)
        self.dislike_button.clicked.connect(self.swipe_left)

        # Add widgets to layout
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.like_button)
        self.layout.addWidget(self.dislike_button)

    def swipe_left(self):
        self.animate_swipe(-300)  # Swipe left off-screen

    def swipe_right(self):
        self.animate_swipe(300)   # Swipe right off-screen

    def animate_swipe(self, x_offset):
        # Create a property animation for the card's position
        self.animation = QPropertyAnimation(self.card, b"pos")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.card.pos())
        end_pos = self.card.pos() + QPoint(x_offset, 0)  # Move horizontally by x_offset
        self.animation.setEndValue(end_pos)

        # Set up the animation to reset the card's position afterward
        self.animation.finished.connect(self.reset_card_position)
        self.animation.start()

    def reset_card_position(self):
        # Reset the card back to the center of the window after the animation
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SwipeWindow()
    window.show()
    sys.exit(app.exec_())