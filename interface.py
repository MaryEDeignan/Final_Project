import sys
import pandas as pd
import os
import ast
import platform
import subprocess
from src.classifier import RecipeDataClassification
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QListWidget,
    QScrollArea,
    QListWidgetItem,
    QVBoxLayout,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QDialog
)
from sklearn.utils import shuffle

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
        background-color: #808080;
        color: #FFFFFF;
    }
    QListWidget::item:hover {
        background-color: #E5F3FF;
    }
    QPushButton {
        background-color: #D3D3D3;
        border: none;
        border-radius: 5px;
        padding: 5px;
        color: #000000;  /* Button text color for light mode */
    }
    QPushButton:hover {
        background-color: #C0C0C0;
    }
    QPushButton:focus {
        outline: none;
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
    QPushButton {
        background-color: #D3D3D3;
        border: none;
        border-radius: 5px;
        padding: 5px;
        color: #000000;
    }
    QPushButton:hover {
        background-color: #C0C0C0;
    }
    QPushButton:focus {
        outline: none;
    }
"""
button_style = """
    QPushButton {
        background-color: #D3D3D3;
        border: none;
        border-radius: 5px;
        padding: 5px;
        color: #000000;
    }
    QPushButton:hover {
        background-color: #C0C0C0;
    }
    QPushButton:focus {
        outline: none;
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
    if is_dark_mode():
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

    if main_window:
        for button in main_window.findChildren(QPushButton):
            button.setStyleSheet("""
                QPushButton {
                    background-color: #D3D3D3;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                    color: #000000;  /* Button text color */
                }
                QPushButton:hover {
                    background-color: #C0C0C0;
                }
                QPushButton:focus {
                    outline: none;
                }
            """)

        if hasattr(main_window, 'liked_recipes_button'):
            font = main_window.liked_recipes_button.font()
            font.setPointSize(14)
            main_window.liked_recipes_button.setFont(font)

class RecipeDetailPage(QWidget):
    def __init__(self, recipe_data, back_callback):
        super().__init__()
        self.setGeometry(100, 100, 450, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(10, 10, 10, 5)

        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(back_callback)
        self.back_button.setStyleSheet(button_style)
        self.back_button.setFixedWidth(150)
        top_layout.addWidget(self.back_button)
        top_layout.addStretch()

        main_layout.addWidget(top_section)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(10, 5, 10, 10)
        self.layout.setSpacing(10)

        self.recipe_data = recipe_data
        self.ingredients = ast.literal_eval(recipe_data['ingredients'])
        self.directions = ast.literal_eval(recipe_data['directions'])

        # Content sections
        self.create_header_section()
        self.create_stats_section()
        self.create_nutrition_section()
        self.create_ingredients_section()
        self.create_directions_section()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def create_section_header(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        return label

    def create_header_section(self):
        title_label = QLabel(self.recipe_data['title'])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setWordWrap(True)
        self.layout.addWidget(title_label)

        category_label = QLabel(f"Category: {self.recipe_data['category']}")
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setStyleSheet("font-size: 12px;")
        self.layout.addWidget(category_label)

        self.layout.addWidget(self.create_horizontal_line())

    def create_stats_section(self):
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(5)
        
        # Rating Information
        rating_widget = QWidget()
        rating_layout = QVBoxLayout(rating_widget)
        rating_layout.setAlignment(Qt.AlignCenter)
        rating_layout.setSpacing(0)  # Reduce vertical spacing
        rating_label = QLabel(f"<b>Rating:</b> {self.recipe_data['rating']}/5")
        rating_count_label = QLabel(f"({self.recipe_data['rating_count']} reviews)")
        rating_label.setStyleSheet("font-size: 12px;")
        rating_count_label.setStyleSheet("font-size: 12px;")
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(rating_count_label)
        stats_layout.addWidget(rating_widget)
        
        # Time Information
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.setSpacing(0)  # Reduce vertical spacing
        cook_time_label = QLabel(f"<b>Cook Time:</b> {self.recipe_data['cook_time']}")
        total_time_label = QLabel(f"<b>Total Time:</b> {self.recipe_data['total_time']}")
        cook_time_label.setStyleSheet("font-size: 12px;")
        total_time_label.setStyleSheet("font-size: 12px;")
        time_layout.addWidget(cook_time_label)
        time_layout.addWidget(total_time_label)
        stats_layout.addWidget(time_widget)
        
        # Servings and Steps
        servings_widget = QWidget()
        servings_layout = QVBoxLayout(servings_widget)
        servings_layout.setAlignment(Qt.AlignCenter)
        servings_layout.setSpacing(0)  # Reduce vertical spacing
        servings_label = QLabel(f"<b>Yield:</b> {self.recipe_data['yield_servings_merge']}")
        steps_label = QLabel(f"<b>Steps:</b> ~{self.recipe_data['verb_count']}")
        servings_label.setStyleSheet("font-size: 12px;")
        steps_label.setStyleSheet("font-size: 12px;")
        servings_layout.addWidget(servings_label)
        servings_layout.addWidget(steps_label)
        stats_layout.addWidget(servings_widget)
        
        self.layout.addWidget(stats_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_nutrition_section(self):
        self.layout.addWidget(self.create_section_header("Nutritional Information"))

        nutrition_widget = QWidget()
        nutrition_layout = QHBoxLayout(nutrition_widget)
        nutrition_layout.setSpacing(5)
        nutrition_layout.setContentsMargins(0, 0, 0, 0)

        nutrition_items = [
            ("Calories", f"{self.recipe_data['calories']}"),
            ("Fat", f"{self.recipe_data['fat']}"),
            ("Carbs", f"{self.recipe_data['carbs']}"),
            ("Protein", f"{self.recipe_data['protein']}")
        ]

        for label, value in nutrition_items:
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setAlignment(Qt.AlignCenter)

            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            label_label = QLabel(label)
            label_label.setStyleSheet("font-size: 12px;")

            item_layout.addWidget(value_label)
            item_layout.addWidget(label_label)
            nutrition_layout.addWidget(item_widget)

        self.layout.addWidget(nutrition_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_ingredients_section(self):
        self.layout.addWidget(self.create_section_header(f"Ingredients ({self.recipe_data['ingredient_count']})"))

        ingredients_widget = QWidget()
        ingredients_layout = QVBoxLayout(ingredients_widget)
        ingredients_layout.setSpacing(3)

        for ingredient in self.ingredients:
            ingredient_label = QLabel(f"• {ingredient}")
            ingredient_label.setStyleSheet("font-size: 12px;")
            ingredient_label.setWordWrap(True)
            ingredients_layout.addWidget(ingredient_label)

        self.layout.addWidget(ingredients_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_directions_section(self):
        self.layout.addWidget(self.create_section_header("Directions"))

        directions_widget = QWidget()
        directions_layout = QVBoxLayout(directions_widget)
        directions_layout.setSpacing(5)

        for i, direction in enumerate(self.directions, 1):
            direction_label = QLabel(f"{i}. {direction}")
            direction_label.setStyleSheet("font-size: 12px;")
            direction_label.setWordWrap(True)
            directions_layout.addWidget(direction_label)

        self.layout.addWidget(directions_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_horizontal_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #BDC3C7;")
        return line

class LikedRecipesPage(QWidget):
    def __init__(self, liked_recipes_dataframe, back_to_swipe_callback):
        super().__init__()
        self.setGeometry(100, 100, 400, 600)

        self.back_to_swipe_callback = back_to_swipe_callback
        self.layout = QVBoxLayout(self)

        self.back_button = QPushButton("Back to Swipe", self)
        self.back_button.setFixedHeight(30)
        self.back_button.clicked.connect(self.back_to_swipe)
        self.back_button.setStyleSheet(button_style)
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

        self.recipes_list.setWordWrap(True)
        self.recipes_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recipes_list.setTextElideMode(Qt.ElideNone)

        for _, row in liked_recipes_dataframe.iterrows():
            item = QListWidgetItem(row['title'])
            item.setData(Qt.UserRole, row)
            width = self.recipes_list.viewport().width()
            item.setSizeHint(QSize(width - 30, 60))
            self.recipes_list.addItem(item)

        self.recipes_list.itemClicked.connect(self.on_recipe_click)
        self.layout.addWidget(self.recipes_list)

    def on_recipe_click(self, item):
        recipe_data = item.data(Qt.UserRole)
        self.show_recipe_detail_page(recipe_data)

    def show_recipe_detail_page(self, recipe_data):
        def back_to_liked_recipes():
            self.setGeometry(100, 100, 400, 600)
            self.show()
            self.recipe_detail_page.hide()

        self.recipe_detail_page = RecipeDetailPage(recipe_data, back_to_liked_recipes)
        self.recipe_detail_page.setGeometry(100, 100, 450, 600)
        self.recipe_detail_page.setFixedSize(450, 600)

        self.hide()
        self.recipe_detail_page.show()

    def back_to_swipe(self):
        self.back_to_swipe_callback()

class SwipeWindow(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.setGeometry(100, 100, 400, 600)

        self.preferences_file = 'data/preferences.csv'
        self.original_dataframe = dataframe
        self.dataframe = dataframe.copy()
        self.current_index = 0
        self.start_pos = None

        if os.path.exists(self.preferences_file):
            self.preferences = pd.read_csv(self.preferences_file)
        else:
            self.preferences = pd.DataFrame(columns=["image_filename", "like_or_dislike"])

        self.both_likes_dislikes = self.merge_preferences()

        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        self.swipes_count = 0
        self.model = RecipeDataClassification(data = [], use_data = False)

        self.update_available_recipes()

        self.setWindowTitle("Recipe Swiper")

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
        font.setPointSize(14)
        self.liked_recipes_button.setFont(font)

        self.layout.addWidget(self.liked_recipes_button)

        self.update_card_text()

    def show_liked_recipes_page(self):
        liked_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'] == 1]
        liked_recipes = liked_recipes.drop_duplicates(subset="image_filename", keep="last")

        def back_to_swipe():
            self.setGeometry(100, 100, 400, 600)
            self.show()
            self.liked_recipes_page.hide()

        self.liked_recipes_page = LikedRecipesPage(liked_recipes, back_to_swipe)
        self.liked_recipes_page.setGeometry(100, 100, 400, 600)
        self.liked_recipes_page.setFixedSize(400, 600)

        self.hide()
        self.liked_recipes_page.show()

    def merge_preferences(self):
        if os.path.exists(self.preferences_file):
            self.preferences = pd.read_csv(self.preferences_file)
            self.preferences = self.preferences.drop_duplicates(subset="image_filename", keep="last")
            self.preferences = self.preferences[["image_filename", "like_or_dislike"]].set_index("image_filename")
            merged = self.original_dataframe.set_index("image_filename").join(
                self.preferences, how="left"
            )
            return merged.reset_index()
        return self.original_dataframe.assign(like_or_dislike=pd.NA)

    def update_available_recipes(self):
        swiped_recipes = self.both_likes_dislikes[
            self.both_likes_dislikes["like_or_dislike"].notna()
        ]["image_filename"]

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
            
            # Check for horizontal swipe
            if abs(delta.x()) > 30 and abs(delta.y()) < 50:
                if delta.x() > 0:
                    self.swipe_right()
                else:
                    self.swipe_left()
            # Check for upward swipe
            elif delta.y() < -50 and abs(delta.x()) < 30: 
                self.swipe_up()
                
            self.start_pos = None

    def check_swipes_count(self):
        self.swipes_count += 1
        print(f'Swipes count = {self.swipes_count}')
        if self.swipes_count >= 10:
            self.update_swipe_queue()
            self.swipes_count = 0
        elif self.swipes_count == 5:
            self.train_model()

    def swipe_left(self):
        self.save_to_disliked()
        self.update_available_recipes()
        self.animate_swipe(-800)
        self.check_swipes_count()

    def swipe_right(self):
        self.save_to_liked()
        self.update_available_recipes()
        self.animate_swipe(800)
        self.check_swipes_count()

    def swipe_up(self):
        if self.current_index < len(self.dataframe):
            recipe_data = self.dataframe.iloc[self.current_index]
            self.show_recipe_detail_preview(recipe_data)

    def show_recipe_detail_preview(self, recipe_data):
        def back_to_swipe():
            self.setGeometry(100, 100, 400, 600)
            self.show()
            self.recipe_detail_preview.hide()

        class RecipeDetailPreview(RecipeDetailPage):
            def create_directions_section(self, *args, **kwargs):
                # Override to skip creating directions section
                pass

        self.recipe_detail_preview = RecipeDetailPreview(recipe_data, back_to_swipe)
        self.recipe_detail_preview.setGeometry(100, 100, 450, 600)
        self.recipe_detail_preview.setFixedSize(450, 600)

        # Create and add transition animation
        self.preview_animation = QPropertyAnimation(self.recipe_detail_preview, b"pos")
        self.preview_animation.setDuration(300)
        start_pos = QPoint(100, 700)  
        end_pos = QPoint(100, 100)    
        
        self.recipe_detail_preview.move(start_pos)
        self.preview_animation.setStartValue(start_pos)
        self.preview_animation.setEndValue(end_pos)
        
        self.hide()
        self.recipe_detail_preview.show()
        self.preview_animation.start()

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
        center_x = (self.width() - self.card.width()) // 2
        center_y = (self.height() - self.card.height()) // 2 - 50
        self.card.move(center_x, center_y)

    def save_preferences(self):
        columns_to_save = list(self.original_dataframe.columns) + ['like_or_dislike']
        prefs_to_save = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]
        prefs_to_save = prefs_to_save.drop_duplicates(subset='image_filename', keep='last')
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        prefs_to_save.to_csv(self.preferences_file, index=False)

    def update_available_recipes(self):
        swiped_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]['image_filename']
        self.dataframe = self.original_dataframe[~self.original_dataframe['image_filename'].isin(swiped_recipes)].reset_index(drop=True)

    def update_swipe_queue(self):
        '''Updates the swipe queue based on trained RecipeDataClassification model.
            Samples 20 random non-selected recipes, then calls PredictionThread to make predictions using most recent trained model.'''
        swiped = self.both_likes_dislikes.dropna()
        unswiped_recipes = self.original_dataframe[
            shuffle(~self.original_dataframe["image_filename"].isin(swiped["image_filename"]))
        ].head(20)

        self.prediction_thread = PredictionThread(unswiped_recipes, self.model)
        self.prediction_thread.predictions_ready.connect(self.on_predictions_ready)
        self.prediction_thread.start()

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

    def train_model(self):
        '''Train model based on all current recipes that have been swiped on.
            Calls TrainingThread to complete model training.'''
        train_data = self.both_likes_dislikes.dropna()
        train_data = train_data[['directions', 'like_or_dislike']]
        train_data = train_data.rename(columns={'directions': 'text', 'like_or_dislike': 'classification'})

        self.training_thread = TrainingThread(train_data)
        self.training_thread.training_done.connect(self.on_training_done)
        self.training_thread.start()

        if not self.training_thread.isRunning():
            print("Training thread did not start correctly.")

    def on_training_done(self):
        '''Once training is complete, signify completion and add model to self.model for later.'''
        print("Model training completed!")
        self.model = self.training_thread.model

    def on_predictions_ready(self, ranked_recipes: pd.DataFrame):
        '''Prepare predictions to present to the user in descending score order, then add the top 15 predictions to the current list of recipes to present to the user.
            Parameters:
                ranked_recipes (pd.DataFrame): The recipes that have been ranked by the prediction model.'''
        ranked_recipes = ranked_recipes.sort_values("score", ascending=False)

        self.dataframe = ranked_recipes.head(15).reset_index(drop=True)
        print('Predictions made...')
        self.update_card_text()

class TrainingThread(QThread):
    '''New thread to allow swiping actions to take place while model is being trained.'''
    training_done = pyqtSignal()

    def __init__(self, train_data: pd.DataFrame, parent=None):
        '''Initialize model with training information.
            Parameters:
                train_data (pd.DataFrame): training data, should be a directions and classification column
                parent: calls QThread'''
        super().__init__(parent)
        self.train_data = train_data
        self.model = None

    def run(self):
        '''Train model and set it as the current model'''
        try:
            print('Initializing model...')
            model = RecipeDataClassification(self.train_data)
            print('Training model...')
            model.train()
            self.model = model
            print('Trained model set...')
            self.training_done.emit()
        except Exception as e:
            print(f"Error during training: {e}")

class PredictionThread(QThread):
    '''Prediction thread to allow SwipeWindow to work while predicting.'''
    predictions_ready = pyqtSignal(pd.DataFrame)

    def __init__(self, data_to_predict: pd.DataFrame, model: RecipeDataClassification, parent=None):
        '''Initialize variables
            Parameters:
                data_to_predict (pd.DataFrame): data for model to predict, should be only one column
                model (RecipeDataClassification): trained model
                parent: calls QThread'''
        super().__init__(parent)
        self.recipes = data_to_predict
        self.model = model

    def run(self):
        '''Run the model and signal completion to the main thread'''
        try:
            print('Running predictions...')
            predictions = self.model.predict(self.recipes['directions'])
            self.recipes['score'] = predictions
            self.predictions_ready.emit(self.recipes)
        except Exception as e:
            print(f"Error during predictions: {e}")


if __name__ == "__main__":
    df = pd.read_csv('data/recipe_data.csv')

    if not all(col in df.columns for col in ["title", "rating", "total_time", "image_filename"]):
        raise ValueError("CSV file must have columns: 'title', 'rating', 'total_time', and 'image_filename'")

    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    apply_theme(app, window)
    window.show()
    sys.exit(app.exec_())