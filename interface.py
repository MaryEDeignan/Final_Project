import sys
import pandas as pd
import os
import platform
import subprocess
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QDialog
)


# Define light and dark themes
LIGHT_THEME = """
    QWidget {
        background-color: #FFFFFF;
        color: #000000;
    }
    QLabel {
        font-size: 16px;
        color: #000000;
    }
    QListWidget {
        background-color: #FFFFFF;
        color: #000000;
        border: none;
        border-radius: 10px;
        padding: 10px;
    }
    QListWidget::item {
        color: #000000;
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
    }
    QListWidget::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    QListWidget::item:hover {
        background-color: #E5F3FF;
    }
"""

DARK_THEME = """
    QWidget {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
    QLabel {
        font-size: 16px;
        color: #FFFFFF;
    }
    QListWidget {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 10px;
    }
    QListWidget::item {
        color: #FFFFFF;
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
    }
    QListWidget::item:selected {
        background-color: #808080;
        color: #FFFFFF;
    }
    QListWidget::item:hover {
        background-color: #3D3D3D;
    }
"""


def is_dark_mode():
    if platform.system() == "Darwin":  # mac
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0  
    elif platform.system() == "Windows":  # windows
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except FileNotFoundError:
            return False
    return False

def apply_theme(app, main_window=None):
    button_style = """
        QPushButton {
            background-color: #D3D3D3;
            color: #000000;
            border: none;
            border-radius: 10px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #C0C0C0;
        }
    """

    if is_dark_mode():
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

    if main_window:
        for button in main_window.findChildren(QPushButton):
            button.setStyleSheet(button_style)

        if hasattr(main_window, 'liked_recipes_button'):
            font = main_window.liked_recipes_button.font()
            font.setPointSize(14)  
            main_window.liked_recipes_button.setFont(font)

class LikedRecipesPage(QWidget):
    def __init__(self, liked_recipes_dataframe, back_to_swipe_callback):
        super().__init__()
        
        self.back_to_swipe_callback = back_to_swipe_callback
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.back_button = QPushButton("Back to Swipe", self)
        self.back_button.setFixedHeight(30)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3;
                color: black;  /* Force text to stay black */
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.back_button.clicked.connect(self.back_to_swipe)
        
        self.title_label = QLabel("Liked Recipes", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.back_button)
        
        self.recipes_list = QListWidget(self)
        self.recipes_list.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background-color: #D3D3D3;
            }
        """)
        
        # Populate list
        for _, row in liked_recipes_dataframe.iterrows():
            self.recipes_list.addItem(f"{row['title']}")
        
        self.layout.addWidget(self.recipes_list)
        
        # Set margins for the layout
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

    def back_to_swipe(self):
        self.back_to_swipe_callback()

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.preferences_file = 'data/preferences.csv'
        self.original_dataframe = dataframe  
        self.dataframe = dataframe.copy()
        self.current_index = 0
        self.start_pos = None

        # Load preferences or initialize a new preferences file if one doesn't exist
        if os.path.exists(self.preferences_file):
            self.preferences = pd.read_csv(self.preferences_file)
        else:
            self.preferences = pd.DataFrame(columns=["image_filename", "like_or_dislike"])

        self.both_likes_dislikes = self.merge_preferences()

        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        self.update_available_recipes()

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
        self.card.setFixedSize(350, 550)   
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        self.button_layout = QHBoxLayout()

        # Add "Dislike" button with an "X"
        self.dislike_button = QPushButton("", self)
        self.dislike_button.setFixedHeight(30)
        self.dislike_button.setIcon(QIcon("docs/images/cross.png"))
        self.dislike_button.setIconSize(QSize(20, 20))  # icon size
        self.dislike_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3; /* light grey background */
                border: none;
                border-radius: 10; /*  rounded corners */
            }
            QPushButton:hover {
                background-color: #C0C0C0; /* darker grey on hover */
            }
        """)

        self.dislike_button.clicked.connect(self.swipe_left)
        self.button_layout.addWidget(self.dislike_button)

        # Add "Like" button with a heart
        self.like_button = QPushButton("", self)
        self.like_button.setFixedHeight(30)
        self.like_button.setIcon(QIcon("docs/images/heart.png"))
        self.like_button.setIconSize(QSize(20, 20))  # icon size
        self.like_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3; /* light grey background */
                border: none;
                border-radius: 10px; /* rounded corners */
            }
            QPushButton:hover {
                background-color: #C0C0C0; /* darker grey on hover */
            }
        """)
        self.like_button.clicked.connect(self.swipe_right)
        self.button_layout.addWidget(self.like_button)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)

        self.layout.addLayout(self.button_layout)

        # Liked Recipes Button
        self.liked_recipes_button = QPushButton("Liked Recipes", self)
        self.liked_recipes_button.clicked.connect(self.show_liked_recipes_page)
        self.liked_recipes_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)

        font = self.liked_recipes_button.font()
        font.setPointSize(14)  # Adjust this value to change the font size
        self.liked_recipes_button.setFont(font)

        self.layout.addWidget(self.liked_recipes_button)

        self.update_card_text()

    def show_liked_recipes_page(self):
        liked_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'] == 1]
        liked_recipes = liked_recipes.drop_duplicates(subset="image_filename", keep="last")
        
        def back_to_swipe():
            self.show()
            self.liked_recipes_page.hide()
        
        # Store as instance variable and set geometry to match main window
        self.liked_recipes_page = LikedRecipesPage(liked_recipes, back_to_swipe)
        self.liked_recipes_page.setGeometry(self.geometry())  # Match size and position
        self.liked_recipes_page.setFixedSize(self.size())    # Ensure exact same size
        
        self.hide()
        self.liked_recipes_page.show()

    def merge_preferences(self):
        if os.path.exists(self.preferences_file):
            self.preferences = pd.read_csv(self.preferences_file)
            self.preferences = self.preferences.drop_duplicates(subset="image_filename", keep="last")  # Deduplicate
            self.preferences = self.preferences[["image_filename", "like_or_dislike"]].set_index("image_filename")
            merged = self.original_dataframe.set_index("image_filename").join(
                self.preferences, how="left"
            )
            return merged.reset_index()
        return self.original_dataframe.assign(like_or_dislike=pd.NA)
        
    def update_available_recipes(self):
        # Filter out recipes that have already been swiped
        swiped_recipes = self.both_likes_dislikes[
            self.both_likes_dislikes["like_or_dislike"].notna()
        ]["image_filename"]

        # Keep only the recipes that haven't been swiped yet
        self.dataframe = self.original_dataframe[
            ~self.original_dataframe["image_filename"].isin(swiped_recipes)
        ].reset_index(drop=True)

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
        self.update_available_recipes()
        self.animate_swipe(-800)

    def swipe_right(self):
        self.save_to_liked()
        self.update_available_recipes()
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
        if len(self.dataframe) > 0:
            self.current_index = (self.current_index + 1) % len(self.dataframe)
            self.update_card_text()
            self.reset_card_position()
        else:
            self.title_label.setText("No more recipes!")
            self.image_label.clear()
            self.rating_label.setText("")
            self.total_time_label.setText("")
        self.reset_card_position()

    def reset_card_position(self):
        # Calculate the center position for the card
        center_x = (self.width() - self.card.width()) // 2
        center_y = (self.height() - self.card.height()) // 2 - 50  # Adjust vertical position
        self.card.move(center_x, center_y)

    def save_preferences(self):
        columns_to_save = list(self.original_dataframe.columns) + ['like_or_dislike']
        prefs_to_save = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]
        prefs_to_save = prefs_to_save.drop_duplicates(subset='image_filename', keep='last')  # Ensure no duplicates
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        prefs_to_save.to_csv(self.preferences_file, index=False)

    def update_available_recipes(self):
        swiped_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]['image_filename']
        self.dataframe = self.original_dataframe[~self.original_dataframe['image_filename'].isin(swiped_recipes)].reset_index(drop=True)


    def save_to_liked(self):
        current_row = self.dataframe.iloc[self.current_index]
        mask = self.both_likes_dislikes['image_filename'] == current_row['image_filename']
        self.both_likes_dislikes.loc[mask, 'like_or_dislike'] = 1
        self.save_preferences()  
        self.update_available_recipes() 

    def save_to_disliked(self):
        current_row = self.dataframe.iloc[self.current_index]
        mask = self.both_likes_dislikes['image_filename'] == current_row['image_filename']
        self.both_likes_dislikes.loc[mask, 'like_or_dislike'] = 0
        self.save_preferences()  
        self.update_available_recipes()  

if __name__ == "__main__":
    df = pd.read_csv('data/recipe_data.csv')

    if not all(col in df.columns for col in ["title", "rating", "total_time", "image_filename"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', 'total_time', and 'image_filename'")

    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    apply_theme(app, window)  # Pass the main window
    window.show()
    sys.exit(app.exec_())