import sys
import pandas as pd
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.dataframe = dataframe
        self.current_index = 0
        self.start_pos = None  # To store initial mouse position for swipe detection

        # Set up main window
        self.setWindowTitle("Recipe Tinder")
        self.setGeometry(100, 100, 600, 400)

        # Set up a main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Create a card widget to hold multiple labels
        self.card = QWidget(self)
        self.card.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(10, 10, 10, 10)

        # Add the title label (larger font)
        self.title_label = QLabel("", self.card)
        title_font = QFont()
        title_font.setPointSize(18)  # Bigger font for the title
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.title_label)

        # Add a rating label
        self.rating_label = QLabel("", self.card)
        self.rating_label.setWordWrap(True)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.rating_label)

        # Add a prep time label
        self.total_time_label = QLabel("", self.card)
        self.total_time_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.total_time_label)

        # Set fixed card size
        self.card.setFixedSize(300, 400)
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # Display the first entry
        self.update_card_text()

    def update_card_text(self):
        # Update card with current entry from dataframe
        if self.current_index < len(self.dataframe):
            row = self.dataframe.iloc[self.current_index]
            
            # Ensure that all values are converted to strings
            self.title_label.setText(str(row.get("title", "No Title")))
            self.total_time_label.setText(f"Total Time: {str(row.get('total_time', 'Unknown'))}")
            
            # If you have a rating column, make sure it is a string as well
            rating = row.get("rating", "No Rating")
            self.rating_label.setText(str(rating))  # Convert the rating to a string

            self.current_index = (self.current_index + 1) % len(self.dataframe)

    def mousePressEvent(self, event):
        """Store the starting position of the mouse."""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """Detect swipe gesture based on the mouse release position."""
        if self.start_pos:
            end_pos = event.pos()
            delta = end_pos - self.start_pos

            # Threshold to determine swipe direction
            if abs(delta.x()) > 100 and abs(delta.y()) < 50:  # Horizontal swipe
                if delta.x() > 0:
                    self.swipe_right()  # Swipe right
                else:
                    self.swipe_left()  # Swipe left
            self.start_pos = None  # Reset the starting position

    def swipe_left(self):
        """Handle left swipe."""
        self.animate_swipe(-800)  # Swipe left off-screen
        self.update_card_text()

    def swipe_right(self):
        """Handle right swipe."""
        self.animate_swipe(800)  # Swipe right off-screen
        self.update_card_text()

    def animate_swipe(self, x_offset):
        """Animate the card swipe."""
        self.animation = QPropertyAnimation(self.card, b"pos")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.card.pos())
        end_pos = self.card.pos() + QPoint(x_offset, 0)
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(self.reset_card_position)
        self.animation.start()

    def reset_card_position(self):
        """Reset the card to its original position after the swipe."""
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)


if __name__ == "__main__":
    # Load your DataFrame from a CSV file
    df = pd.read_csv('data/recipe_data.csv')  # Replace with the actual path to your CSV file

    # Ensure that the CSV has the required columns
    if not all(col in df.columns for col in ["title", "rating", "total_time"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', and 'total_time'")

    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    window.show()
    sys.exit(app.exec_())
