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
    QListWidgetItem,  
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QDialog
)

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

        self.recipe_data = recipe_data

        self.ingredients = ast.literal_eval(recipe_data['ingredients'])
        self.directions = ast.literal_eval(recipe_data['directions'])

        self.layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(self.recipe_data['title'])
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        # Rating
        self.rating_label = QLabel(f"Rating: {self.recipe_data['rating']}")
        self.layout.addWidget(self.rating_label)

        # Ingredients Section
        self.ingredients_label = QLabel("Ingredients:")
        self.layout.addWidget(self.ingredients_label)

        # Join the ingredients into a single text block
        ingredients_text = "\n".join(self.ingredients)
        self.ingredients_text = QLabel(ingredients_text)
        self.ingredients_text.setWordWrap(True)  
        self.layout.addWidget(self.ingredients_text)

        # Directions
        self.directions_label = QLabel("Directions:")
        self.layout.addWidget(self.directions_label)

        # Join the directions into a single text block
        directions_text = "\n".join(self.directions)
        self.directions_text = QLabel(directions_text)
        self.directions_text.setWordWrap(True)
        self.layout.addWidget(self.directions_text)

        # Back Button
        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(back_callback)
        self.back_button.setStyleSheet(button_style) 
        self.layout.addWidget(self.back_button)

        self.setLayout(self.layout)


class LikedRecipesPage(QWidget):
    def __init__(self, liked_recipes_dataframe, back_to_swipe_callback):
        super().__init__()
        
        self.back_to_swipe_callback = back_to_swipe_callback
        self.layout = QVBoxLayout(self)
        
        self.back_button = QPushButton("Back to Swipe", self)
        self.back_button.setFixedHeight(30)
        self.back_button.clicked.connect(self.back_to_swipe)
        self.back_button.setStyleSheet(button_style) 
        self.layout.addWidget(self.back_button)
        
        self.recipes_list = QListWidget(self)
        self.recipes_list.setStyleSheet("QListWidget {border: none; border-radius: 10px; padding: 10px;} QListWidget::item {padding: 10px; margin: 5px; border-radius: 5px;} QListWidget::item:hover {background-color: #D3D3D3;}")
        
        for _, row in liked_recipes_dataframe.iterrows():
            item = QListWidgetItem(row['title'])
            item.setData(Qt.UserRole, row)  
            self.recipes_list.addItem(item)
        
        self.recipes_list.itemClicked.connect(self.on_recipe_click)
        
        self.layout.addWidget(self.recipes_list)

    def on_recipe_click(self, item):
        recipe_data = item.data(Qt.UserRole)  
        self.show_recipe_detail_page(recipe_data)

    def show_recipe_detail_page(self, recipe_data):
        def back_to_swipe():
            self.show()
            self.recipe_detail_page.hide()
        
        self.recipe_detail_page = RecipeDetailPage(recipe_data, back_to_swipe)
        self.recipe_detail_page.setGeometry(self.geometry())
        self.recipe_detail_page.setFixedSize(self.size())  
        
        self.hide()
        self.recipe_detail_page.show()
        
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
        font.setPointSize(14)  
        self.liked_recipes_button.setFont(font)

        self.layout.addWidget(self.liked_recipes_button)

        self.update_card_text()

    def show_liked_recipes_page(self):
        liked_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'] == 1]
        liked_recipes = liked_recipes.drop_duplicates(subset="image_filename", keep="last")
        
        def back_to_swipe():
            self.show()
            self.liked_recipes_page.hide()
        
        self.liked_recipes_page = LikedRecipesPage(liked_recipes, back_to_swipe)
        self.liked_recipes_page.setGeometry(self.geometry())  
        self.liked_recipes_page.setFixedSize(self.size())   
        
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

            if abs(delta.x()) > 30 and abs(delta.y()) < 50:
                if delta.x() > 0:
                    self.swipe_right()
                else:
                    self.swipe_left()
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
        prefs_to_save = prefs_to_save.drop_duplicates(subset='image_filename', keep='last')  # Ensure no duplicates
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        prefs_to_save.to_csv(self.preferences_file, index=False)

    def update_available_recipes(self):
        swiped_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]['image_filename']
        self.dataframe = self.original_dataframe[~self.original_dataframe['image_filename'].isin(swiped_recipes)].reset_index(drop=True)
    
    def update_swipe_queue(self):
        # Filter for unswiped recipes
        swiped = self.both_likes_dislikes.dropna()
        unswiped_recipes = self.original_dataframe[
            ~self.original_dataframe["image_filename"].isin(swiped["image_filename"])
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
        train_data = self.both_likes_dislikes.dropna()
        train_data = train_data[['directions', 'like_or_dislike']]
        train_data = train_data.rename(columns={'directions': 'text', 'like_or_dislike': 'classification'})

        self.training_thread = TrainingThread(train_data)
        self.training_thread.training_done.connect(self.on_training_done)
        self.training_thread.start()

        if not self.training_thread.isRunning():
            print("Training thread did not start correctly.")

    def on_training_done(self):
        print("Model training completed!")
        self.model = self.training_thread.model

    def on_predictions_ready(self, ranked_recipes):
        # Sort by prediction scores (descending)
        ranked_recipes = ranked_recipes.sort_values("score", ascending=False)
        
        # Update the swipe queue with the top-N recipes
        self.dataframe = ranked_recipes.head(15).reset_index(drop=True)
        print('Predictions made...')
        self.update_card_text()
    
class TrainingThread(QThread):
    training_done = pyqtSignal()

    def __init__(self, train_data, parent=None):
        super().__init__(parent)
        self.train_data = train_data

    def run(self):
        try:
            print('Initializing model...')
            model = RecipeDataClassification(self.train_data)
            print('Training model...')
            model.train()  # Potential exception here
            self.model = model
            print('Trained model set...')
            self.training_done.emit()  # Signal completion
        except Exception as e:
            print(f"Error during training: {e}")

class PredictionThread(QThread):
    predictions_ready = pyqtSignal(pd.DataFrame)

    def __init__(self, recipes, model, parent=None):
        super().__init__(parent)
        self.recipes = recipes
        self.model = model

    def run(self):
        try:
            print('Running predictions...')
            predictions = self.model.predict(self.recipes['directions'])  # Adjust based on your model's predict method
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