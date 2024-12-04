import sys
import pandas as pd
import os
import platform
import subprocess
if platform.system() == "Windows":
    import winreg
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

# Define light and dark themes
LIGHT_THEME = """
    QWidget {
        background-color: #FFFFFF;
        color: #000000;
    }
    QLabel {
        font-size: 16px;
    }
"""

DARK_THEME = """
    QWidget {
        background-color: #2D2D2D; /* Main background is dark grey */
        color: #FFFFFF;           /* Text color is white */
    }
    QLabel {
        font-size: 16px;
        color: #FFFFFF;           /* Text color to white */
    }
    QWidget#card {
        background-color: #2D2D2D; /* Card background is dark grey */
        border-radius: 10px;
        color: #FFFFFF;           /* Card text is white */
    }
"""

def is_dark_mode():
    if platform.system() == "Darwin":  # macOS
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0  # Returns 0 if dark mode is enabled
    elif platform.system() == "Windows":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0  
        except FileNotFoundError:
            return False
    return False

def apply_theme(app):
    if is_dark_mode():
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.dataframe = dataframe  # Store the passed dataframe and set up initial variables
        self.current_index = 0 # Start at first recipe in the dataframe
        self.start_pos = None  # To store initial mouse position for swipe detection

        # Dataframes to store liked and disliked recipes
        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        # Set up main window properties
        self.setWindowTitle("Recipe Swiper")  # Title that appears at top of application 
        self.setGeometry(100, 100, 400, 600)  # Set window size and position

        # Set up main widget and layout for window
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Create card widget that will display recipe information
        self.card = QWidget(self)
        self.card.setObjectName("card")  # Add this line to name the card widget
        self.card.setStyleSheet("border-radius: 10px;")  # Keep border styling
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)

        # Add image label to the card
        self.image_label = QLabel(self.card)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(350, 400)
        self.image_label.setStyleSheet("border-radius: 10px;")
        self.card_layout.addWidget(self.image_label)

        # Create text container for recipe information below image
        self.text_container = QWidget(self.card)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(10, 10, 10, 10)

        # Add title label for recipe
        self.title_label = QLabel("", self.text_container)
        self.title_label.setWordWrap(True)  # Enable word wrapping
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.title_label)

        # Add rating label for recipe
        self.rating_label = QLabel("", self.text_container)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.rating_label)

        # Add label for total time to make the recipe
        self.total_time_label = QLabel("", self.text_container)
        self.total_time_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.total_time_label)

        # Add the text container with title, rating, and total time to the card layout
        self.card_layout.addWidget(self.text_container)

        # Set fixed size for the card widget and center it
        self.card.setFixedSize(350, 500)
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # Display first recipe card
        self.update_card_text()

    def update_card_text(self):
        """Update the card with current entry from dataframe, including the image from src/scraping/images folder."""
        if self.current_index < len(self.dataframe):
            row = self.dataframe.iloc[self.current_index]
            
            # Update the title, total time, and rating labels with the recipe data
            self.title_label.setText(self.truncate_text(str(row.get("title", "No Title"))))
            self.total_time_label.setText(f"Total Time: {str(row.get('total_time', 'Unknown'))}")
            
            # Display rating as a string
            rating = row.get("rating", "No Rating")
            self.rating_label.setText(f"Rating: {str(rating)}")  # Convert the rating to a string

            # Display image
            image_filename = row.get("image_filename", None)
            if image_filename and os.path.exists(f"src/scraping/images/{image_filename}"):
                pixmap = QPixmap(f"src/scraping/images/{image_filename}")
                self.image_label.setPixmap(pixmap.scaled(350, 400, 
                                                         Qt.KeepAspectRatioByExpanding, 
                                                         Qt.SmoothTransformation))  # Scale the image to fit

    def truncate_text(self, text):
        """Truncate text to make sure it fits on the card"""
        max_lines = 2  # Limit to 2 lines
        max_characters = 100  
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
            self.start_pos = None  # Reset the starting position after swipe

    def swipe_left(self):
        """Handle left swipe to dislike the recipe."""
        self.save_to_disliked()  # Save to disliked recipes dataframe
        self.animate_swipe(-800)  # Animate swipe to the left off-screen

    def swipe_right(self):
        """Handle right swipe to like the recipe."""
        self.save_to_liked()  # Save to liked recipes dataframe
        self.animate_swipe(800)  # Animate swipe to the right off-screen

    def animate_swipe(self, x_offset):
        """Animate the card swipe to the left or right."""
        self.animation = QPropertyAnimation(self.card, b"pos")  
        self.animation.setDuration(200)  # Set animation duration
        self.animation.setStartValue(self.card.pos())
        end_pos = self.card.pos() + QPoint(x_offset, 0)  # Calculate the end position of the swipe
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(self.handle_animation_end)  # Connect to method after animation finishes
        self.animation.start()

    def handle_animation_end(self):
        """Handle the end of the swipe animation and update the card to the next recipe."""
        self.current_index = (self.current_index + 1) % len(self.dataframe)  # Move to the next recipe
        self.update_card_text()  # Update card content
        self.reset_card_position()  # Reset the card's position to center

    def reset_card_position(self):
        """Reset the position of the card to its original centered position."""
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)

    def save_to_liked(self):
        """Save the current recipe to the liked DataFrame."""
        current_row = self.dataframe.iloc[self.current_index].copy()
        current_row = pd.DataFrame([current_row])
        if len(self.liked) == 0:
            self.liked = current_row
        else:
            self.liked.loc[len(self.liked)] = current_row.iloc[0]

    def save_to_disliked(self):
        """Save the current recipe to the disliked DataFrame."""
        current_row = self.dataframe.iloc[self.current_index].copy()
        current_row = pd.DataFrame([current_row])
        if len(self.disliked) == 0:
            self.disliked = current_row
        else:
            self.disliked.loc[len(self.disliked)] = current_row.iloc[0]

    def export_dataframes(self, liked_path='data/liked_recipes.csv', disliked_path='data/disliked_recipes.csv'):
        """Export the liked and disliked DataFrames to CSV files."""
        # Ensure the directories exist
        liked_dir = os.path.dirname(liked_path)
        disliked_dir = os.path.dirname(disliked_path)
        if liked_dir and not os.path.exists(liked_dir):
            os.makedirs(liked_dir)
        if disliked_dir and not os.path.exists(disliked_dir):
            os.makedirs(disliked_dir)

        # Save the dataframes to csv files
        self.liked.to_csv(liked_path, index=False)
        self.disliked.to_csv(disliked_path, index=False)
        print(f"Liked recipes saved to: {liked_path}")
        print(f"Disliked recipes saved to: {disliked_path}")

    def closeEvent(self, event):
        """Handle actions when the window is closed"""
        liked_path = 'data/liked_recipes.csv'  # Setting folder/file for liked recipe csv
        disliked_path = 'data/disliked_recipes.csv'  # Setting folder/file for disliked recipe csv
        self.export_dataframes(liked_path, disliked_path)  # Export data before closing
        event.accept()  # Proceed with closing the window


if __name__ == "__main__":
    # Load dataframe from csv file
    df = pd.read_csv('data/recipe_data.csv')

    # Validate required columns
    if not all(col in df.columns for col in ["title", "rating", "total_time", "image_filename"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', 'total_time', and 'image_filename'")

    app = QApplication(sys.argv)

    # Apply light or dark theme based on system settings
    apply_theme(app)

    window = SwipeWindow(df)
    window.show()
    sys.exit(app.exec_())