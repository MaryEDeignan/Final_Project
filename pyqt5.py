import sys
import pandas as pd
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.dataframe = dataframe  # Store the dataframe for use in the app
        self.current_index = 0  # Start with the first row in the dataframe

        # Set up main window with a fixed size
        self.setWindowTitle("Recipe Tinder")
        self.setGeometry(100, 100, 600, 400)  # Fixed window size (600x400)

        # Set up a main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Set the card size manually (fixed size)
        card_width = 300
        card_height = 400
        self.card = QLabel(self)
        self.card.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
        self.card.setAlignment(Qt.AlignCenter)
        self.card.setFixedSize(card_width, card_height)  # Fixed card size

        # Create buttons (with Check and X symbols)
        self.check_button = QPushButton("✓", self)
        self.x_button = QPushButton("✕", self)

        # Set the buttons to be square (e.g., 150x150) and change font size
        button_size = 100  # Size of the buttons
        self.check_button.setFixedSize(button_size, button_size)
        self.x_button.setFixedSize(button_size, button_size)

        # Set the font size for the check and X buttons
        font = self.check_button.font()
        font.setPointSize(40)  # Set a larger font size for the check mark
        self.check_button.setFont(font)
        self.x_button.setFont(font)  # Apply the same font size to the X button

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.x_button)  # X first
        button_layout.addWidget(self.check_button)  # Check second (on the right)

        # Connect buttons to swipe actions
        self.check_button.clicked.connect(self.swipe_right)
        self.x_button.clicked.connect(self.swipe_left)

        # Add widgets to layout
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.layout.addLayout(button_layout)  # Add the horizontal button layout

        # Display the first entry on the card
        self.update_card_text()

    def swipe_left(self):
        self.animate_swipe(-800)  # Swipe left off-screen
        self.update_card_text()  # Update card with next entry

    def swipe_right(self):
        self.animate_swipe(800)   # Swipe right off-screen
        self.update_card_text()  # Update card with next entry

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

    def update_card_text(self):
        # Get the current row from the dataframe and update the card text
        if self.current_index < len(self.dataframe):
            text = self.dataframe.iloc[self.current_index]["title"]  # Assuming 'text' is a column in your dataframe
            self.card.setText(text)
            self.current_index = (self.current_index + 1) % len(self.dataframe)  # Loop back after reaching the end

if __name__ == "__main__":
    # Load your DataFrame from a CSV file
    df = pd.read_csv('data/recipe_data.csv')  # Replace with the actual path to your CSV file

    # Ensure that the CSV has a column 'title' to display
    if 'title' not in df.columns:
        raise ValueError("CSV file must have a column named 'title'")

    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    window.show()
    sys.exit(app.exec_())
