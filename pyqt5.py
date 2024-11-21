import sys
import pandas as pd
import os
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.dataframe = dataframe
        self.current_index = 0
        self.start_pos = None  # To store initial mouse position for swipe detection

        # Dataframes to store liked and disliked recipes
        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        # Set up main window
        self.setWindowTitle("Recipe Tinder")
        self.setGeometry(100, 100, 400, 600)  # Adjusted for a taller design

        # Set up a main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Create a card widget
        self.card = QWidget(self)
        self.card.setStyleSheet("background-color: white; border-radius: 10px;")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)

        # Add the image label
        self.image_label = QLabel(self.card)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(350, 400)
        self.image_label.setStyleSheet("border-radius: 10px;")
        self.card_layout.addWidget(self.image_label)

        # Create a text container below the image
        self.text_container = QWidget(self.card)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(10, 10, 10, 10)

        # Add the title label
        self.title_label = QLabel("", self.text_container)
        self.title_label.setWordWrap(True)  # Enable word wrapping
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.title_label)

        # Add a rating label
        self.rating_label = QLabel("", self.text_container)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.rating_label)

        # Add a total time label
        self.total_time_label = QLabel("", self.text_container)
        self.total_time_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.total_time_label)

        # Add the text container to the card layout
        self.card_layout.addWidget(self.text_container)

        # Center the card widget
        self.card.setFixedSize(350, 500)
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # Display the first entry
        self.update_card_text()

    def update_card_text(self):
        """Update the card with current entry from dataframe, including the image."""
        if self.current_index < len(self.dataframe):
            row = self.dataframe.iloc[self.current_index]
            
            # Ensure that all values are converted to strings
            self.title_label.setText(self.truncate_text(str(row.get("title", "No Title"))))
            self.total_time_label.setText(f"Total Time: {str(row.get('total_time', 'Unknown'))}")
            
            # If you have a rating column, make sure it is a string as well
            rating = row.get("rating", "No Rating")
            self.rating_label.setText(f"Rating: {str(rating)}")  # Convert the rating to a string

            # Set image
            image_filename = row.get("image_filename", None)
            if image_filename and os.path.exists(f"scraping/images/{image_filename}"):
                pixmap = QPixmap(f"scraping/images/{image_filename}")
                self.image_label.setPixmap(pixmap.scaled(350, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))  # Scale the image to fit

    def truncate_text(self, text):
        """Truncate text to ensure it doesn't overflow."""
        max_lines = 2  # Limit to 2 lines
        max_characters = 100  # Approximate character limit based on font size
        if len(text) > max_characters:
            return text[:max_characters - 3] + "..."  # Add ellipsis if truncated
        return text

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
        self.save_to_disliked()  # Save to disliked dataframe
        self.animate_swipe(-800)  # Swipe left off-screen

    def swipe_right(self):
        """Handle right swipe."""
        self.save_to_liked()  # Save to liked dataframe
        self.animate_swipe(800)  # Swipe right off-screen

    def animate_swipe(self, x_offset):
        """Animate the card swipe."""
        self.animation = QPropertyAnimation(self.card, b"pos")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.card.pos())
        end_pos = self.card.pos() + QPoint(x_offset, 0)
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(self.handle_animation_end)
        self.animation.start()

    def handle_animation_end(self):
        """Handle the end of the swipe animation."""
        self.current_index = (self.current_index + 1) % len(self.dataframe)  # Move to the next recipe
        self.update_card_text()
        self.reset_card_position()

    def reset_card_position(self):
        """Reset the card to its original position after the swipe."""
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)

    def save_to_liked(self):
        """Save the current recipe to the liked dataframe."""
        current_row = self.dataframe.iloc[self.current_index]
        current_row = current_row.dropna()  # Drop NA values to prevent warnings
        if not current_row.empty:  # Ensure the row has data before appending
            self.liked = pd.concat([self.liked, pd.DataFrame([current_row])], ignore_index=True)

    def save_to_disliked(self):
        """Save the current recipe to the disliked dataframe."""
        current_row = self.dataframe.iloc[self.current_index]
        current_row = current_row.dropna()  # Drop NA values to prevent warnings
        if not current_row.empty:  # Ensure the row has data before appending
            self.disliked = pd.concat([self.disliked, pd.DataFrame([current_row])], ignore_index=True)

    def export_dataframes(self, liked_path='data/liked_recipes.csv', disliked_path='data/disliked_recipes.csv'):
        """Export liked and disliked DataFrames to CSV files at specified locations."""
        
        # Ensure the directories exist
        liked_dir = os.path.dirname(liked_path)
        disliked_dir = os.path.dirname(disliked_path)
        if liked_dir and not os.path.exists(liked_dir):
            os.makedirs(liked_dir)
        if disliked_dir and not os.path.exists(disliked_dir):
            os.makedirs(disliked_dir)

        # Save the DataFrames to CSV
        self.liked.to_csv(liked_path, index=False)
        self.disliked.to_csv(disliked_path, index=False)
        print(f"Liked recipes saved to: {liked_path}")
        print(f"Disliked recipes saved to: {disliked_path}")

    def closeEvent(self, event):
        """Handle actions when the window is closed."""
        liked_path = 'data/liked_recipes.csv'
        disliked_path = 'data/disliked_recipes.csv'
        self.export_dataframes(liked_path, disliked_path)
        event.accept()  # Proceed with closing the window


if __name__ == "__main__":
    # Load your DataFrame from a CSV file
    df = pd.read_csv('data/recipe_data.csv')

    # Ensure that the CSV has the required columns
    if not all(col in df.columns for col in ["title", "rating", "total_time", "image_filename"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', 'total_time', and 'image_filename'")

    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    window.show()
    sys.exit(app.exec_())