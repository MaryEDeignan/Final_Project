import sys
import pandas as pd
import os
import platform
import subprocess
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
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
            import winreg
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

        self.dataframe = dataframe
        self.current_index = 0
        self.start_pos = None

        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        self.setWindowTitle("Recipe Swiper")
        self.setGeometry(100, 100, 400, 600)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet("border-radius: 10px;")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(self.card)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(350, 400)
        self.image_label.setStyleSheet("border-radius: 10px;")
        self.card_layout.addWidget(self.image_label)

        self.text_container = QWidget(self.card)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(10, 10, 10, 10)

        self.title_label = QLabel("", self.text_container)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.title_label)

        self.rating_label = QLabel("", self.text_container)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.rating_label)

        self.total_time_label = QLabel("", self.text_container)
        self.total_time_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.total_time_label)

        self.card_layout.addWidget(self.text_container)
        self.card.setFixedSize(350, 500)
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # Create button layout
        self.button_layout = QHBoxLayout()

        # Add "Dislike" button with an "X"
        self.dislike_button = QPushButton("", self)
        self.dislike_button.setFixedSize(150, 30)
        self.dislike_button.setIcon(QIcon("docs/images/cross.png"))  # Path to your downloaded icon
        self.dislike_button.setIconSize(QSize(20, 20))  # Adjust icon size
        self.dislike_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3; /* Light grey background */
                border: none;
                border-radius: 10; /*  rounded corners */
            }
            QPushButton:hover {
                background-color: #C0C0C0; /* Slightly darker grey when hovered */
            }
        """)

        self.dislike_button.clicked.connect(self.swipe_left)
        self.button_layout.addWidget(self.dislike_button)

        # Add "Like" button with a heart
        self.like_button = QPushButton("", self)
        self.like_button.setFixedSize(150, 30)
        self.like_button.setIcon(QIcon("docs/images/heart.png"))  # Path to your downloaded heart icon
        self.like_button.setIconSize(QSize(20, 20))  # Adjust icon size
        self.like_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3; /* Light grey background */
                border: none;
                border-radius: 10px; /* rounded corners */
            }
            QPushButton:hover {
                background-color: #C0C0C0; /* Slightly darker grey when hovered */
            }
        """)
        self.like_button.clicked.connect(self.swipe_right)
        self.button_layout.addWidget(self.like_button)

        # Add the button layout to the main layout
        self.layout.addLayout(self.button_layout)

        self.update_card_text()

    def update_card_text(self):
        if self.current_index < len(self.dataframe):
            row = self.dataframe.iloc[self.current_index]

            self.title_label.setText(self.truncate_text(str(row.get("title", "No Title"))))
            self.total_time_label.setText(f"Total Time: {str(row.get('total_time', 'Unknown'))}")

            rating = row.get("rating", "No Rating")
            self.rating_label.setText(f"Rating: {str(rating)}")

            image_filename = row.get("image_filename", None)
            if image_filename and os.path.exists(f"src/scraping/images/{image_filename}"):
                pixmap = QPixmap(f"src/scraping/images/{image_filename}")
                self.image_label.setPixmap(pixmap.scaled(350, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def truncate_text(self, text):
        max_characters = 100
        if len(text) > max_characters:
            return text[:max_characters - 3] + "..."
        return text

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if self.start_pos:
            end_pos = event.pos()
            delta = end_pos - self.start_pos

            if abs(delta.x()) > 30 and abs(delta.y()) < 50:
                if delta.x() > 0:
                    self.swipe_right()
                else:
                    self.swipe_left()
            self.start_pos = None

    def swipe_left(self):
        self.save_to_disliked()
        self.animate_swipe(-800)

    def swipe_right(self):
        self.save_to_liked()
        self.animate_swipe(800)

    def animate_swipe(self, x_offset):
        self.animation = QPropertyAnimation(self.card, b"pos")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.card.pos())
        end_pos = self.card.pos() + QPoint(x_offset, 0)
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(self.handle_animation_end)
        self.animation.start()

    def handle_animation_end(self):
        self.current_index = (self.current_index + 1) % len(self.dataframe)
        self.update_card_text()
        self.reset_card_position()

    def reset_card_position(self):
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)

    def save_to_liked(self):
        current_row = self.dataframe.iloc[self.current_index].copy()
        current_row = pd.DataFrame([current_row])
        if len(self.liked) == 0:
            self.liked = current_row
        else:
            self.liked.loc[len(self.liked)] = current_row.iloc[0]

    def save_to_disliked(self):
        current_row = self.dataframe.iloc[self.current_index].copy()
        current_row = pd.DataFrame([current_row])
        if len(self.disliked) == 0:
            self.disliked = current_row
        else:
            self.disliked.loc[len(self.disliked)] = current_row.iloc[0]

if __name__ == "__main__":
    df = pd.read_csv('data/recipe_data.csv')

    if not all(col in df.columns for col in ["title", "rating", "total_time", "image_filename"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', 'total_time', and 'image_filename'")

    app = QApplication(sys.argv)
    apply_theme(app)
    window = SwipeWindow(df)
    window.show()
    sys.exit(app.exec_())