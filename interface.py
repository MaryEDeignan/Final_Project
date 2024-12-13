import sys
import pandas as pd
import os
import ast
import platform
import subprocess
from src.classifier import RecipeDataClassification
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QPainter
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
        background-color: #FFFFFF;  /* white background */
        color: #000000;  /* black text color throughout */
    }
    QLabel {  
        font-size: 16px;  /* size for text labels */
        color: #000000;  /* black text for text labels */
    }
    QListWidget {   /* styling for liked recipe list */
        background-color: #FFFFFF;  /* white background */
        color: #000000;  /* black text color */
        border: none;  /* remove default borders */
        border-radius: 10px;  /* rounding corners on list containers */
        padding: 10px;  /* setting spacing inside list containers */
    }
    QListWidget::item {  /* individual recipe items in liked recipe list */
        color: #000000;  /* black text */
        padding: 10px;  /* spacing inside each recipe item */
        margin: 5px;  /* spacing between recipe items */
        border-radius: 5px;  /* rounding corners */
    }
    QListWidget::item:selected {  /* selected recipe in the list */
        background-color: #808080;   /* grey background */
        color: #FFFFFF;   /* white text */
    }
    QListWidget::item:hover {  /* hover effect on recipe items */
        background-color: #E5F3FF;  /* light grey background when hovered */
    }
    QPushButton {  /* button styling */
        background-color: #D3D3D3;  /* light gray button background */
        border: none;  /* removing default borders */
        border-radius: 5px;  /* rounding corners */
        padding: 5px;  /* spacing inside buttons */
        color: #000000;  /* black text color */
    }
    QPushButton:hover {  /* hover effect on buttons */
        background-color: #C0C0C0;  /* darker gray when hovering */
    }
    QPushButton:focus {   
        outline: none;  /* remove outline when button is focused */
    }
"""

DARK_THEME = """
    QWidget {
        background-color: #2D2D2D;  /* dark grey background */
        color: #FFFFFF; /* white text */
    }
    QLabel {
        font-size: 16px;   /* size for text labels */
        color: #FFFFFF;  /* white text for text labels */
    }
    QListWidget {  /* styling for liked recipe list */
        background-color: #2D2D2D;  /* dark grey background */
        color: #FFFFFF; /* white text color */
        border: none;  /* remove default borders */
        border-radius: 10px;  /* rounding corners on list containers */
        padding: 10px;  /* setting spacing inside list containers */
    }
    QListWidget::item {  /* individual recipe items in liked recipe list */
        color: #FFFFFF;  /* white text */
        padding: 10px;  /* spacing inside each recipe item */
        margin: 5px; /* spacing between recipe items */
        border-radius: 5px;  /* rounding corners */
    }
    QListWidget::item:selected {  /* selected recipe in the list */
        background-color: #808080; /* grey background */
        color: #FFFFFF;  /* white text */
    }
    QListWidget::item:hover {  /* hover effect on recipe items */
        background-color: #3D3D3D;  /* light grey background when hovered */
    }
    QPushButton { /* button styling */
        background-color: #D3D3D3;  /* light gray button background */
        border: none; /* removing default borders */
        border-radius: 5px;  /* rounding corners */
        padding: 5px;  /* spacing inside buttons */
        color: #000000; /* black text color */
    }
    QPushButton:hover {  /* hover effect on buttons */
        background-color: #C0C0C0;  /* darker gray when hovering */
    }
    QPushButton:focus {
        outline: none;  /* remove outline when button is focused */
    }
"""

button_style = """
    QPushButton {  /* base button styling */
        background-color: #D3D3D3;  /* light gray background */
        border: none;  /* remove default button borders */
        border-radius: 5px;  /* rounding corners */
        padding: 5px;  /* spacing inside buttons */
        color: #000000;  /* black text color */
    }
    QPushButton:hover {  /* hover effect on buttons */
        background-color: #C0C0C0;  /* darker gray on hover */
    }
    QPushButton:focus {  
        outline: none;  /* remove outline when button is focused */
    }
"""


def is_dark_mode()-> bool:
    """    
    Checks the system settings for if computer is in light/dark mode on macOS and Windows.
    For other operating systems, defaults to False (light mode).
    
    Returns:
        bool: True if system is in dark mode, False otherwise
    """
    # check macOS dark mode
    if platform.system() == "Darwin": 
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # returncode 0 indicates 'Dark' was found, so computer is in dark mode
        return result.returncode == 0
    
    # check Windows dark mode
    elif platform.system() == "Windows": 
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            # if light theme is 0, dark mode is being used
            return value == 0
        except FileNotFoundError:
            # assume light mode
            return False
    # default to light mode for other operating systems
    return False

def apply_theme(app, main_window=None):
    """
    Applies theme to application based on computers dark/light mode setting.

    Args:
        app: The QApplication instance to apply theming to
        main_window: Optional main window to apply specific button styling to
    """
    # set app-wide stylesheet based on if light/dark mode is found
    if is_dark_mode():
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

    if main_window:
        # make consistent button styling for all buttons in main window
        for button in main_window.findChildren(QPushButton):
            button.setStyleSheet("""
                QPushButton {
                    background-color: #D3D3D3;  /* light gray background */
                    border: none;  /* remove default border */
                    border-radius: 5px;  /* rounded corners */
                    padding: 5px;  /* internal padding */
                    color: #000000;  /* black text color */
                }
                QPushButton:hover {
                    background-color: #C0C0C0;  /* darker gray on hover */
                }
                QPushButton:focus {
                    outline: none;  /* remove focus outline */
                }
            """)
        # setting larger font size for liked recipes button if it exists
        if hasattr(main_window, 'liked_recipes_button'):
            font = main_window.liked_recipes_button.font()
            font.setPointSize(14)  # font size to 14
            main_window.liked_recipes_button.setFont(font)

class RecipeDetailPage(QWidget):
    """
    Page that shows detailed information about a recipe including times, ratings, 
    nutrition, ingredients, and directions.
    """
    def __init__(self, recipe_data, back_callback):
        super().__init__()
        # set window size and position
        self.setGeometry(100, 100, 450, 600)

        # creating main layout, no margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # creating top section for back buttons
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(10, 10, 10, 5)

        # setting up back button
        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(back_callback)
        self.back_button.setStyleSheet(button_style)
        self.back_button.setFixedWidth(150)
        top_layout.addWidget(self.back_button)
        top_layout.addStretch()

        main_layout.addWidget(top_section)

        # making recipe info section scrollable
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # making container for recipe info
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(10, 5, 10, 10)
        self.layout.setSpacing(10)

        # storing recipe data
        self.recipe_data = recipe_data
        self.ingredients = ast.literal_eval(recipe_data['ingredients'])  # parsing ingredients
        self.directions = ast.literal_eval(recipe_data['directions'])  # parsing directions

        # making content sections
        self.create_header_section()
        self.create_stats_section()
        self.create_nutrition_section()
        self.create_ingredients_section()
        self.create_directions_section()

        # adding content container to the scrollable section
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def create_section_header(self, text:str)-> QLabel:
        """
        Creates a header label for recipe sections.

        Args:
            text: The text to display in the header

        Returns:
            QLabel: The header label
        """
        # making label with text provided
        label = QLabel(text)
        # setting styling for section header
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        return label

    def create_header_section(self)-> None:
        """
        Creating and adding the header section of the recipe detail page.
        This includes recipe title, category, and a horizontal line separator.
        """
        # creating and styling recipe title label
        title_label = QLabel(self.recipe_data['title'])
        title_label.setAlignment(Qt.AlignCenter)  # center align
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setWordWrap(True) # wrap title text if too long
        self.layout.addWidget(title_label)

        # creating and styling category label
        category_label = QLabel(f"Category: {self.recipe_data['category']}")
        category_label.setAlignment(Qt.AlignCenter) # center align
        category_label.setStyleSheet("font-size: 12px;")
        self.layout.addWidget(category_label)

        # adding separator line below header
        self.layout.addWidget(self.create_horizontal_line())

    def create_stats_section(self)-> None:
        """
        Creates and adds the "stats" section of the recipe detail page.
        Displays recipe rating, time information, servings and estimated 
        step count in a horizontal layout with three columns.
        """
        # making main stats container widget and layout
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(5)
        
        # rating info - rating and rating count 
        rating_widget = QWidget()
        rating_layout = QVBoxLayout(rating_widget)
        rating_layout.setAlignment(Qt.AlignCenter)
        rating_layout.setSpacing(0)  
        rating_label = QLabel(f"<b>Rating:</b> {self.recipe_data['rating']}/5")  
        rating_count_label = QLabel(f"({self.recipe_data['rating_count']} reviews)") 
        rating_label.setStyleSheet("font-size: 12px;")
        rating_count_label.setStyleSheet("font-size: 12px;")
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(rating_count_label)
        stats_layout.addWidget(rating_widget)
        
        # time info - cook time and total time
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.setSpacing(0)  
        cook_time_label = QLabel(f"<b>Cook Time:</b> {self.recipe_data['cook_time']}")
        total_time_label = QLabel(f"<b>Total Time:</b> {self.recipe_data['total_time']}")
        cook_time_label.setStyleSheet("font-size: 12px;")
        total_time_label.setStyleSheet("font-size: 12px;")
        time_layout.addWidget(cook_time_label)
        time_layout.addWidget(total_time_label)
        stats_layout.addWidget(time_widget)
        
        # yield/servings and estimation of steps
        servings_widget = QWidget()
        servings_layout = QVBoxLayout(servings_widget)
        servings_layout.setAlignment(Qt.AlignCenter)
        servings_layout.setSpacing(0)  # Reduce vertical spacing
        servings_label = QLabel(f"<b>Yield:</b> {self.recipe_data['yield_servings_merge']}") # using custom yield/servings merge feature
        steps_label = QLabel(f"<b>Steps:</b> ~{self.recipe_data['verb_count']}")
        servings_label.setStyleSheet("font-size: 12px;")
        steps_label.setStyleSheet("font-size: 12px;")
        servings_layout.addWidget(servings_label)
        servings_layout.addWidget(steps_label)
        stats_layout.addWidget(servings_widget)
        
        # adding stats widget and the separator to the main layout
        self.layout.addWidget(stats_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_nutrition_section(self)-> None:
        """
        Creates and adds the nutrition section of the recipe detail page.
        Displays calories, fat, carbs, and protein in a horizontal layout
        with value above the label.
        """
        # adding section header
        self.layout.addWidget(self.create_section_header("Nutritional Information"))

        # creating nutrition container widget and layout
        nutrition_widget = QWidget()
        nutrition_layout = QHBoxLayout(nutrition_widget)
        nutrition_layout.setSpacing(5)   # setting space between different nutritions
        nutrition_layout.setContentsMargins(0, 0, 0, 0) # no margins

        # setting nutrition info to display
        nutrition_items = [
            ("Calories", f"{self.recipe_data['calories']}"),
            ("Fat", f"{self.recipe_data['fat']}"),
            ("Carbs", f"{self.recipe_data['carbs']}"),
            ("Protein", f"{self.recipe_data['protein']}")
        ]

        #  making widget for each nutrition item
        for label, value in nutrition_items:
            # container for each nutrition item
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setAlignment(Qt.AlignCenter)

            # creating and styling value and label
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 14px; font-weight: bold;") # value is bold and larger
            label_label = QLabel(label)
            label_label.setStyleSheet("font-size: 12px;")  # label text

            # adding the value and label to item layout
            item_layout.addWidget(value_label)
            item_layout.addWidget(label_label)
            nutrition_layout.addWidget(item_widget)

        # adding nutrition widget and the separator to the main layout
        self.layout.addWidget(nutrition_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_ingredients_section(self)-> None:
        """
        Creates and adds the ingredients section of the recipe detail page.
        Displays total ingredient count in header and lists each ingredient
        with a bullet point on its own line.
        """
        # adding section header with count of ingredients
        self.layout.addWidget(self.create_section_header(f"Ingredients ({self.recipe_data['ingredient_count']})"))

        # creating ingredients container widget and layout
        ingredients_widget = QWidget()
        ingredients_layout = QVBoxLayout(ingredients_widget)
        ingredients_layout.setSpacing(3)  # space between ingredients

        # making bullet point label for each ingredient
        for ingredient in self.ingredients:
            ingredient_label = QLabel(f"• {ingredient}")
            ingredient_label.setStyleSheet("font-size: 12px;") # ingredient font size
            ingredient_label.setWordWrap(True)  # text wrapping for long ingredients
            ingredients_layout.addWidget(ingredient_label)

        # adding ingredients widget and the separator to the main layout
        self.layout.addWidget(ingredients_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_directions_section(self)-> None:
        """
        Creates and adds the directions section with numbered recipe steps.
        """
        # adding section header
        self.layout.addWidget(self.create_section_header("Directions"))

        # creating directions container and layout
        directions_widget = QWidget()
        directions_layout = QVBoxLayout(directions_widget)
        directions_layout.setSpacing(5)  # space between each step

        # making numbered label for each direction step
        for i, direction in enumerate(self.directions, 1):
            direction_label = QLabel(f"{i}. {direction}")
            direction_label.setStyleSheet("font-size: 12px;")
            direction_label.setWordWrap(True)
            directions_layout.addWidget(direction_label)

        # adding directions widget and separator
        self.layout.addWidget(directions_widget)
        self.layout.addWidget(self.create_horizontal_line())

    def create_horizontal_line(self)-> QFrame:
        """
        Creates a horizontal line separator to divide sections
        """
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # Horizontal line
        line.setStyleSheet("background-color: #BDC3C7;") # light grey color
        return line

class LikedRecipesPage(QWidget):
    """
    Page showing liked recipes in a scrollable list.
    
    Args:
        liked_recipes_dataframe: DataFrame containing liked recipes data
        back_to_swipe_callback: Callback function to return to main swipe page
    """
    def __init__(self, liked_recipes_dataframe:pd.DataFrame, back_to_swipe_callback:callable)-> None:
        super().__init__()
        self.setGeometry(100, 100, 400, 600) # setting position and window size 

        # storing callback
        self.back_to_swipe_callback = back_to_swipe_callback
        #creating layout
        self.layout = QVBoxLayout(self)

        # creating back button
        self.back_button = QPushButton("Back to Swiper", self)
        self.back_button.setFixedHeight(30)
        self.back_button.clicked.connect(self.back_to_swipe)
        self.back_button.setStyleSheet(button_style)
        self.layout.addWidget(self.back_button)

        # creating and styling recipe list
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

        # setting list widget display options
        self.recipes_list.setWordWrap(True)
        self.recipes_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recipes_list.setTextElideMode(Qt.ElideNone)

        # making list with liked recipes
        for _, row in liked_recipes_dataframe.iterrows():
            item = QListWidgetItem(row['title'])
            item.setData(Qt.UserRole, row)  # storing full recipe data
            width = self.recipes_list.viewport().width()
            item.setSizeHint(QSize(width - 30, 60))  # consistent height
            self.recipes_list.addItem(item)

        # conncceting click handler (when clicked) and addding list to layout
        self.recipes_list.itemClicked.connect(self.on_recipe_click)
        self.layout.addWidget(self.recipes_list)

    def on_recipe_click(self, item:QListWidgetItem)-> None:
        """
        Opens detail page for clicked recipe.
        """
        recipe_data = item.data(Qt.UserRole)  # getting stored recipe data
        self.show_recipe_detail_page(recipe_data) # showing recipe info

    def show_recipe_detail_page(self, recipe_data:dict)-> None:
        """
        Shows detailed recipe page and hides current page.
        
        Args:
            recipe_data: Full recipe info to display
        """
        def back_to_liked_recipes():
            """Returns to list of liked recipes."""
            self.setGeometry(100, 100, 400, 600)
            self.show()
            self.recipe_detail_page.hide()

        # creating and setting up details page
        self.recipe_detail_page = RecipeDetailPage(recipe_data, back_to_liked_recipes)
        self.recipe_detail_page.setGeometry(100, 100, 450, 600)

        # hiding liked recipes list and showing recipe details page transition
        self.hide()
        self.recipe_detail_page.show()

    def back_to_swipe(self)-> None:
        """
        Starts callback to return to swiper view.
        """
        self.back_to_swipe_callback()

class SwipeWindow(QMainWindow):
    """
    Main window for recipe swiping application with like and dislike function.
    
    Args:
        dataframe: Pandas DataFrame containing recipe information
    """
    def __init__(self, dataframe: pd.DataFrame)-> None:
        super().__init__()

        # setting up window position and size
        self.setGeometry(100, 100, 400, 600)
        self.setWindowTitle("Snackr")

        # initializing data
        self.preferences_file = 'data/preferences.csv' 
        self.original_dataframe = dataframe
        self.dataframe = dataframe.copy()
        self.current_index = 0
        self.start_pos = None

        # loading past preferences
        if os.path.exists(self.preferences_file):
            self.preferences = pd.read_csv(self.preferences_file)
        else:
            self.preferences = pd.DataFrame(columns=["image_filename", "like_or_dislike"])

        self.both_likes_dislikes = self.merge_preferences()

        # setting up tracking of liked/disliked recipes
        self.liked = pd.DataFrame(columns=dataframe.columns)
        self.disliked = pd.DataFrame(columns=dataframe.columns)

        # classification setup: initializing model and swipes_count for testing
        self.swipes_count = 0  
        self.model = RecipeDataClassification(data = [], use_data = False, verbose = True)

        self.update_available_recipes()

        # setting up main layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # setting up recipe card container
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet("border-radius: 10px;")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)

        # Add image container
        self.image_container = QWidget(self.card)
        self.image_container_layout = QVBoxLayout(self.image_container)
        self.image_container_layout.setContentsMargins(0, 0, 0, 0)

        # setting up image label
        self.image_label = QLabel(self.image_container)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(350, 400)
        self.image_label.setStyleSheet("border-radius: 10px;")
        self.image_container_layout.addWidget(self.image_label)
        
        self.card_layout.addWidget(self.image_container)

        # creating text container
        self.text_container = QWidget(self.card)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(10, 10, 10, 10)

        # creating title container
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6) # space between title and info button

        # adding spacers and title label
        left_spacer = QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        title_layout.addItem(left_spacer)
        self.title_label = QLabel("", self.text_container)
        self.title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
        """)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(self.title_label)
        spacer = QSpacerItem(8, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        title_layout.addItem(spacer)

        # setting up info button
        self.info_button = QPushButton("", self.text_container)
        self.info_button.setIcon(QIcon("docs/images/info.png")) # custom image
        self.info_button.setIconSize(QSize(20, 20))  # icon size
        self.info_button.setFixedSize(25, 25)  # size of button
        self.info_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #D3D3D3;
                background-color: transparent;
                border-radius: 15px;  
            }
            QPushButton:hover {
                background-color: #D3D3D3;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
        """)
        self.info_button.clicked.connect(self.show_recipe_details)

        title_layout.addWidget(self.info_button)
        right_spacer = QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        title_layout.addItem(right_spacer)
        self.text_layout.addWidget(title_container)

        # adding rating and time labels
        self.rating_label = QLabel("", self.text_container)
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.rating_label)

        self.total_time_label = QLabel("", self.text_container)
        self.total_time_label.setAlignment(Qt.AlignCenter)
        self.text_layout.addWidget(self.total_time_label)

        self.card_layout.addWidget(self.text_container)
        self.card.setFixedSize(350, 550)
        self.layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # setting up like/dislike buttons layout
        self.button_layout = QHBoxLayout()

        # adding "dislike" button with an "X"
        self.dislike_button = QPushButton("", self)
        self.dislike_button.setFixedHeight(30)
        self.dislike_button.setIcon(QIcon("docs/images/cross.png"))
        self.dislike_button.setIconSize(QSize(20, 20))
        self.dislike_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.dislike_button.clicked.connect(self.swipe_left)
        self.button_layout.addWidget(self.dislike_button)

        # adding "like" button with a heart
        self.like_button = QPushButton("", self)
        self.like_button.setFixedHeight(30)
        self.like_button.setIcon(QIcon("docs/images/heart.png"))
        self.like_button.setIconSize(QSize(20, 20))
        self.like_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.like_button.clicked.connect(self.swipe_right)
        self.button_layout.addWidget(self.like_button)

        # adding a spacer between card and buttons
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)

        self.layout.addLayout(self.button_layout)

        # setting up liked recipes button
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

    def show_liked_recipes_page(self)-> None:
        """
        Shows page displaying all liked recipes. Creates new page
        and hides current window.
        """
        # getting liked recipes, removing duplicates
        liked_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'] == 1]
        liked_recipes = liked_recipes.drop_duplicates(subset="image_filename", keep="last")

        # defining callback to returning to swipe view
        def back_to_swipe():
            self.setGeometry(100, 100, 400, 600) # resetting window size
            self.show()  # show swipe window
            self.liked_recipes_page.hide()  # hiding liked recipes

        # creating and setting up liked recipes page
        self.liked_recipes_page = LikedRecipesPage(liked_recipes, back_to_swipe)
        self.liked_recipes_page.setGeometry(100, 100, 400, 600)

        # hiding main swipe window and displaying liked recipes window 
        self.hide()
        self.liked_recipes_page.show()

    def merge_preferences(self)-> pd.DataFrame:
        """
        Merges recipe data with user preferences (likes/dislikes).
        Returns original data with preferences if file exists, otherwise adds empty preference column.
        """
        if os.path.exists(self.preferences_file):
            # loading and cleaning preferences
            self.preferences = pd.read_csv(self.preferences_file)
            self.preferences = self.preferences.drop_duplicates(subset="image_filename", keep="last")
            self.preferences = self.preferences[["image_filename", "like_or_dislike"]].set_index("image_filename")
            # merging preferences with recipe data, keep all recipes with left merge
            merged = self.original_dataframe.set_index("image_filename").join(
                self.preferences, how="left"
            )
            return merged.reset_index()
        # if there is no preferences file then return data with empty preference column  
        return self.original_dataframe.assign(like_or_dislike=pd.NA)

    def update_available_recipes(self)-> None:
        """
        Updates available recipes by removing ones already swiped on.
        Filters original dataframe to only show unrated recipes.
        """
        # getting recipes that have been swiped on, using image filename because it is unique to every recipe
        swiped_recipes = self.both_likes_dislikes[
            self.both_likes_dislikes["like_or_dislike"].notna()
        ]["image_filename"]

        # filtering to only unrated recipes
        self.dataframe = self.dataframe[
            ~self.dataframe["image_filename"].isin(swiped_recipes)
        ].reset_index(drop=True)

    def update_card_text(self)-> None:
        """
        Updates recipe card display with current recipe information.
        Shows placeholder text if data is missing.
        """
        # Check if recipes are available
        if self.current_index < len(self.dataframe):
            row = self.dataframe.iloc[self.current_index]
            # setting title, time and rating labels
            self.title_label.setText(self.truncate_text(str(row.get("title", "No Title"))))
            self.total_time_label.setText(f"Total Time: {str(row.get('total_time', 'Unknown'))}")
            rating = row.get("rating", "No Rating")
            self.rating_label.setText(f"Rating: {str(rating)}")
            # loading and display recipe image
            image_filename = row.get("image_filename", None)
            if image_filename and os.path.exists(f"src/scraping/images/{image_filename}"):
                pixmap = QPixmap(f"src/scraping/images/{image_filename}")
                self.image_label.setPixmap(pixmap.scaled(350, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def truncate_text(self, text:str)-> str:
        """
        Truncates text to 35 characters max with ellipsis.
        """
        max_characters = 35  
        if len(text) > max_characters:
            return text[:max_characters - 3] + "..."
        return text

    def mousePressEvent(self, event)-> None:
        """
        Tracks start position of mouse click for swipe detection.
        """
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos() # storing click position if left button is used

    def mouseReleaseEvent(self, event)-> None:
        """
        Detects horizontal swipe gestures for liking/disliking recipes.
        Triggers swipe action if horizontal movement more than 30px and vertical less than 50px.
        """
        if self.start_pos:
            end_pos = event.pos()
            delta = end_pos - self.start_pos
            
            if abs(delta.x()) > 30 and abs(delta.y()) < 50:
                if delta.x() > 0: # right swipe for like
                    self.swipe_right()
                else:   # left swipe for dislike
                    self.swipe_left()
                
            self.start_pos = None  # resetting start position

    def check_swipes_count(self)-> None:
        """
        Tracks swipes and triggers model updates.
        Updates queue at 10 swipes, trains model at 5 swipes.
        """
        self.swipes_count += 1
        print(f'Swipes count = {self.swipes_count}')
        if self.swipes_count >= 10:
            self.update_swipe_queue()  # updating recommendations
            self.swipes_count = 0  # resetting counter
        elif self.swipes_count == 4:
            self.train_model()   # training on new data

    def swipe_left(self)-> None:
        """
        Handles dislike action, saves and animates dislike swipes.
        """
        self.save_to_disliked()  # saving as disliked
        self.update_available_recipes()  # updaing recipe queue
        self.animate_swipe(-800)  # antimating left swipe
        self.check_swipes_count() # checking if model update is needed

    def swipe_right(self)-> None:
        """
        Handles like action, saves and animates like swipes.
        """
        self.save_to_liked() # saving as liked
        self.update_available_recipes()  # updating recipe queue
        self.animate_swipe(800) # animating right swipe
        self.check_swipes_count() # checking if model update is needed
  
    def show_recipe_details(self)-> None:
        """
        Opens recipe detail preview if current recipe exists.
        """
        if self.current_index < len(self.dataframe):
            recipe_data = self.dataframe.iloc[self.current_index] # getting current recipe
            self.show_recipe_detail_preview(recipe_data) # showing recipe preview, stats and ingredients

    def show_recipe_detail_preview(self, recipe_data:dict)-> None:
        """
        Shows preview of recipe details (stats and ingredients) without directions section.
        Creates temporary window with recipe overview.
        """
        def back_to_swipe():
            """Returns to main swipe view."""
            self.setGeometry(100, 100, 400, 600)
            self.show()
            self.recipe_detail_preview.hide()

        class RecipeDetailPreview(RecipeDetailPage):
            def create_directions_section(self, *args, **kwargs):
                pass   # skipping directions

        # creating and showing preview window
        self.recipe_detail_preview = RecipeDetailPreview(recipe_data, back_to_swipe)
        self.recipe_detail_preview.setGeometry(100, 100, 450, 600)
        
        # hide main swipe window and show recipe detail preview window
        self.hide()
        self.recipe_detail_preview.show()

    def animate_swipe(self, x_offset:int)-> None:
        """
        Animates the swiping motion of the recipe card.
        Args:
            x_offset (int): The horizontal offset for the swipe animation.
        """
        self.animation = QPropertyAnimation(self.card, b"pos")
        self.animation.setDuration(200)  # duriation of the animation, 200ms
        self.animation.setStartValue(self.card.pos()) # start poisiton of animation
        end_pos = self.card.pos() + QPoint(x_offset, 0) # end position based on offset
        self.animation.setEndValue(end_pos)  # set end position of animation
        self.animation.finished.connect(self.handle_animation_end)  # connect to handler
        self.animation.start()  # starting animation 

    def handle_animation_end(self)-> None:
        """
        Handles the end of the swipe animation.
        """
        if len(self.dataframe) > 0:
            self.current_index = (self.current_index + 1) % len(self.dataframe) # moving to next recipe
            self.update_card_text() # updating card text with new recipe
            self.reset_card_position() # reset card position 
        else:
            # when no more recipes, clear the card text show message
            self.title_label.setText("No more recipes!")
            self.image_label.clear()
            self.rating_label.setText("")
            self.total_time_label.setText("")
        self.reset_card_position()  # reset the card position

    def reset_card_position(self) -> None:
        """
        Resets the card position to the center of the window.
        """
        center_x = (self.width() - self.card.width()) // 2
        center_y = (self.height() - self.card.height()) // 2 - 50
        self.card.move(center_x, center_y)

    def save_preferences(self)-> None:
        """
        Saves the user's likes and dislikes to the preferences.csv file.
        """
        columns_to_save = list(self.original_dataframe.columns) + ['like_or_dislike']
        prefs_to_save = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]
        prefs_to_save = prefs_to_save.drop_duplicates(subset='image_filename', keep='last')
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True) 
        prefs_to_save.to_csv(self.preferences_file, index=False)  # save preferences to csv file

    def update_available_recipes(self)-> None:
        """
        Updates the available recipes by removing ones that have been swiped on.
        """
        swiped_recipes = self.both_likes_dislikes[self.both_likes_dislikes['like_or_dislike'].notna()]['image_filename']
        self.dataframe = self.dataframe[~self.dataframe['image_filename'].isin(swiped_recipes)].reset_index(drop=True)

    def update_swipe_queue(self)-> None:
        '''Updates the swipe queue based on trained RecipeDataClassification model.
            Samples 20 random non-selected recipes, then calls PredictionThread to make predictions using most recent trained model.'''
        swiped = self.both_likes_dislikes.dropna()
        unswiped_recipes = (shuffle(self.original_dataframe[
            ~self.original_dataframe["image_filename"].isin(swiped["image_filename"])
        ])).head(20)

        self.prediction_thread = PredictionThread(unswiped_recipes, self.model)
        self.prediction_thread.predictions_ready.connect(self.on_predictions_ready)
        self.prediction_thread.start()

    def save_to_liked(self)-> None:
        """
        Saves the current recipe as liked.
        """
        current_row = self.dataframe.iloc[self.current_index]
        mask = self.both_likes_dislikes['image_filename'] == current_row['image_filename']
        self.both_likes_dislikes.loc[mask, 'like_or_dislike'] = 1
        self.save_preferences()
        self.update_available_recipes()

    def save_to_disliked(self)-> None:
        """
        Saves the current recipe as disliked.
        """
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

    def on_training_done(self) -> None:
        '''Once training is complete, signify completion and add model to self.model for later.'''
        print("Model training completed!")
        self.model = self.training_thread.model

    def on_predictions_ready(self, ranked_recipes: pd.DataFrame) -> None:
        '''Prepare predictions to present to the user in descending score order, then add the top 15 predictions to the current list of recipes to present to the user.
            Parameters:
                ranked_recipes (pd.DataFrame): The recipes that have been ranked by the prediction model.'''
        ranked_recipes = ranked_recipes.sort_values("score", ascending=False)
        self.current_index = 0

        self.dataframe = ranked_recipes.head(15).reset_index(drop=True)
        print('Predictions made...')
        self.swipes_count = 0 # reset swipes
        self.update_card_text()

class TrainingThread(QThread):
    '''New thread to allow swiping actions to take place while model is being trained.'''
    training_done = pyqtSignal()

    def __init__(self, train_data: pd.DataFrame, parent=None) -> None:
        '''Initialize model with training information.
            Parameters:
                train_data (pd.DataFrame): training data, should be a directions and classification column
                parent: calls QThread'''
        super().__init__(parent)
        self.train_data = train_data
        self.model = None

    def run(self) -> None:
        '''Train model and set it as the current model'''
        try:
            print('Initializing model...')
            model = RecipeDataClassification(self.train_data, verbose = False)
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

    def __init__(self, data_to_predict: pd.DataFrame, model: RecipeDataClassification, parent=None) -> None:
        '''Initialize variables
            Parameters:
                data_to_predict (pd.DataFrame): data for model to predict, should be only one column
                model (RecipeDataClassification): trained model
                parent: calls QThread'''
        super().__init__(parent)
        self.recipes = data_to_predict
        self.model = model

    def run(self) -> None:
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
    app = QApplication(sys.argv)
    window = SwipeWindow(df)
    apply_theme(app, window) 
    window.show()
    sys.exit(app.exec_())