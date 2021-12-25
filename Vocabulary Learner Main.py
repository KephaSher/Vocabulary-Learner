import json
import time
from random import randint
from datetime import datetime, timedelta
from collections import defaultdict

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window

from kivy.graphics import *
from kivy.graphics import RoundedRectangle

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from kivy.uix.widget import Widget
from kivy.core.text import Label as textLabel
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.dropdown import DropDown

# Not natively in Kivy
from circular_progress_bar import CircularProgressBar
from wrapped_label import WrappedLabel
from wrapped_button import WrappedButton

LEARNED_THRESHOLD = 0.8
FAMILIAR_THRESHOLD = 0.45

# load kv file
Builder.load_file("vocab.kv")

"""
Json File Structure
-------------------

Root (dict):
    User (dict):
        name (str): str
        goal (str): int
        questions answered (str): int
        current list
    Login Info (dict):
        last login (str):
            time (list):
                year (int)
                month (int)
                day (int)
                hour (int)
            correct answer count (int)
            all answers count (int)
        all logins (str):
            time (list):
                year (int)
                month (int)
                day (int)
                hour (int)
            correct answer count (int)
            all answers count (int)
    WordList (str):
        word (str): 
            meanings (list)
            answered correctly (int)
            answered total (int)
            list (str)
    LearnedWords (str):
        word (str): 
            meanings (list)
            synonyms (list)
            sentence (list)
            type (list)
            answered correctly (int)
            answered total (int)
"""
file = open('Vocabulary_Words.json', 'r')
js = json.load(file)

# Because looping through the words everytime is very inefficient, create a dictionary 
# that maps lists to words

word_lists = defaultdict(lambda: [])

# generates word_lists
def generate_word_lists():
    word_lists.clear()
    for word in js['WordList']:
        word_lists[js['WordList'][word][3]].append(word)   
# removes keys with empty lists in `word_lists`
def update_word_lists():        
    i = 0
    while i < len(word_lists):
        if len(list(word_lists.values())[i]) == 0:
            word_lists.pop(list(word_lists.keys())[i])
        else: i += 1
generate_word_lists()

# total question answered and number of them that are correct for this login
total_question_answered = 0
total_question_answered_correct = 0

screen_manager = ScreenManager()

class Main(Screen):
    # label that shows the current list that the user is practicing
    current_list = ObjectProperty(None)

    # the next button
    next = ObjectProperty(None)
    
    # value for the CPB
    correct_percentage = ObjectProperty(None)

    # label: number of times answered correctly
    correct_num = ObjectProperty(None)

    # label: number of times answered incorrectly
    incorrect_num = ObjectProperty(None)

    # the user profile button
    profile_btn = ObjectProperty(None)

    # if the user answered correctly
    answer_correct = False

    # list to practice
    list_to_practice = str()

    """
    `Main.__init__(**kwargs)`
    constructor, this is only called once. Even when the screen changes, 
    it doesn't make a new instance
    """
    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)

        # dictionary of label -> checkbox
        self.labelToCheck = {self.ans1t: self.ans1, self.ans2t: self.ans2,
                             self.ans3t: self.ans3, self.ans4t: self.ans4}

        # list of labels
        self.answer_labels = [self.ans1t, self.ans2t, self.ans3t, self.ans4t]

        # add the labels to the CPBs, the text will change when they the user
        # answers questions
        self.total_answered.label = textLabel(font_size=35)
        self.correctness.label = textLabel(font_size=35)
        self.update()

    """
    `Main.deactivate()`
    Called whenever playing is NOT valid

    1. Sets word box (`self.word`) to blank
    2. Deactivate all checkboxes
    3. Clears labels
    4. Clears CPB
    """
    def deactivate(self):
        # reset the word box
        self.word.text = ''

        # sets label colors to black and enable the checkboxes
        for label in self.labelToCheck:
            label.color = (0, 0, 0, 1)
            label.text = ''
            self.labelToCheck[label].disabled = True
        
        # reset the CPB
        self.correct_percentage.max = 1
        self.correct_percentage.value = 0

    """
    `Main.play_valid()`
    Called whenever `self.update()` is called
    
    1. checks if playing is valid
    """
    def play_valid(self) -> bool:
        if word_lists.get(self.list_to_practice) == None:
            return False

        words = word_lists[self.list_to_practice]

        meanings = set()
        for word in words:
            mean_list = js['WordList'][word][0]
            for mean in mean_list:
                meanings.add(mean)
            if len(meanings) >= 4:
                return True

        return False

    """
    `Main.update()`
    Called whenever the current screen is switched to this screen

    1. updates greetings
    2. calls `play()` if possible
    """
    def update(self):
        # set the greetings based on time
        # -------------------------------
        
        # user is a list of first, last name
        username = js['User']["name"]

        hour = time.localtime()[3]
        if hour > 7 and hour < 13:
            self.profile_btn.text = "Good Morning, " + username
        elif hour > 12 and hour < 19:
            self.profile_btn.text = "Good Afternoon, " + username
        else:
            self.profile_btn.text = "Good Evening, " + username

        if self.play_valid():
            # set the label of the current list
            self.current_list.text = "Currently studying: " + self.list_to_practice
            self.get_word()
        else:
            self.deactivate()

        # update questions_answered
        # -------------------------

        # max: the user's goal of how many questions they want to answer
        self.total_answered.max = js['User']['goal']

        # value: how many questions they actually answered
        self.total_answered.value = min(self.total_answered.max, total_question_answered)

        today = time.localtime()[2]

        # add all of the questions answered from previous logins from the today
        for login in js['Login info']['all logins']:
            if login[0][2] == today and self.total_answered.value < self.total_answered.max:
                self.total_answered.value = min(
                    self.total_answered.value + login[2], self.total_answered.max)

        self.total_answered._default_label_text = str(self.total_answered.value) + " / " \
            + str(self.total_answered.max) + "\n   {}%"
        self.total_answered._text_label.refresh()

        # update correctness
        # ------------------

        # the questions answered correctly today
        correct_count = 0

        # number of questions answered today
        total_count = 0

        # these are used to figure out the precentage of correctness

        # calculate precentage from questions answered from previous logins from the today
        for login in js['Login info']['all logins']:
            if login[0][2] == today:
                correct_count += login[1]
                total_count += login[2]

        # update questions_correct
        self.correctness.max = max(1, total_count)
        self.correctness.value = correct_count
        self.correctness._default_label_text = "Correct\n   {}%"
        self.correctness._text_label.refresh()

    """
    `Main.get_word()`
    Called whenever the user presses the next button

    1. randomly selects a word to be the correct word
    2. sets up the incorrect ones
    3. updates statistics on the correct word
    """
    def get_word(self):
        for label in self.labelToCheck:
            label.color = (0, 0, 0, 1)
            label.text = ''
            self.labelToCheck[label].disabled = False

        # ---------------------------- Pick New Word -----------------------------
        word_list = word_lists[self.list_to_practice]

        # used for recommendation algorithm (not yet implemented)
        learned = []
        familiar = []
        to_learn = []
        for word in word_list:
            correct_percentage = 0 if js['WordList'][word][2] == 0 \
                else js['WordList'][word][1] / js['WordList'][word][2]
            if correct_percentage > LEARNED_THRESHOLD:
                learned.append(word)
            elif correct_percentage > FAMILIAR_THRESHOLD:
                familiar.append(word)
            else:
                to_learn.append(word)


        # selects the correct word `self.wordName`
        # ----------------------------------------

        self.wordName = word_list[randint(0, len(word_list) - 1)]

        # sets the main word label on the top
        self.word.text = self.wordName

        # index 2 is the total number of times answered
        self.correct_percentage.max = max(1, js['WordList'][self.wordName][2])

        # index 1 is the number of correct times answered
        self.correct_percentage.value = js['WordList'][self.wordName][1]
 

        # list of meanings for the current word
        meanings = js['WordList'][self.wordName][0]

        # puts meanings in `others` except the current word (self.wordName)
        others = []
        for word in js['WordList']:  # loop through all the words
            lst = js['WordList'][word][3]
            if word != self.wordName and lst == self.list_to_practice:  # if word ≠ current word
                others += js['WordList'][word][0]

        # remove repeats in `others`
        others = list(set(others))

        # if the correct label text is in others, remove it
        for meaning in others:
            if meaning in meanings: # if the meaning is in the list of meanings for the current word
                others.remove(meaning)


        # the correct answer label for meaning
        self.correct_label = self.answer_labels[randint(0, 3)]

        # sets the text for the correct label, randomly select one from the list of meanings
        self.correct_label.text = meanings[randint(0, len(meanings) - 1)]


        # the corresponding checkbox for the correct label
        self.correct_checkbox = self.labelToCheck[self.correct_label]


        # list of incorrect answers labels
        self.incorrect_labels = []
        for answer_label in self.answer_labels:
            if answer_label != self.correct_label:
                self.incorrect_labels.append(answer_label)
        
        # this guarentees that meanings will not be repeated
        # but this also means that the meaning count can be < 4, so we need to take care of that

        # set text to incorrect labels
        for i in range(3):
            # if there are no meanings left, disable the checkbox
            if len(others) <= 0:
                self.incorrect_labels[i].text = 'N/A'
                self.labelToCheck[self.incorrect_labels[i]].disabled = True

            # otherwise, pop the current meaning out of `other`
            else:
                index = randint(0, len(others) - 1)
                self.incorrect_labels[i].text = others.pop(index)


        # update CPB, labels about the current word
    
        # labels
        self.correct_num.text = str(js['WordList'][self.wordName][1]) 
        self.incorrect_num.text = str(js['WordList'][self.wordName][2] - js['WordList'][self.wordName][1])

        # CPBs
        self.correct_percentage.max = max(1, js['WordList'][self.wordName][2])
        self.correct_percentage.value = js['WordList'][self.wordName][1]

    """
    `Main.check()`
    Called whenever the user clicks an answer checkbox

    1. Deactives itself, set to red/green depending if the user got it correct
    2. Updates statistics on the word
    3. Updates global total question answered/correct 
    """
    def check(self, instance):
        global total_question_answered
        global total_question_answered_correct

        # the user answered a question, so add to it
        total_question_answered += 1

        # set checkboxes to disabled and color them
        instance.active = False
        instance.disabled = True

        # if the checkbox is correct
        if instance == self.correct_checkbox:
            total_question_answered_correct += 1

            # add stats to js file
            js['WordList'][self.wordName][1] += 1
            js['WordList'][self.wordName][2] += 1

            # set correct label to green, incorrect to red
            for label in self.labelToCheck.keys():
                if self.labelToCheck[label] == instance:
                    label.color = (0, 177/255, 106/255, 1)
                else:
                    label.color = (242/255, 38/255, 19/255, 1)

            # disable all incorrect labels
            for label in self.incorrect_labels:
                self.labelToCheck[label].disabled = True

            self.answer_correct = True
        # if checkbox is incorrect
        else: 
            # update stats
            js['WordList'][self.wordName][2] += 1

            for label in self.labelToCheck.keys():
                if self.labelToCheck[label] == instance:
                    label.color = (242/255, 38/255, 19/255, 1)
                    
            self.answer_correct = False

    """
    `Main.nextWord()`
    Called whenever the next button is pressed

    1. if answer is correct, call `self.get_word()`
    """
    def nextWord(self):
        # user can only go to the next question if they got it right
        if self.answer_correct:
            self.answer_correct = False
            self.get_word()

    """
    `Main.go_to_profile(btn: Button)`
    Called when user presses the profile button
    """
    def go_to_profile(self):
        modal = UserProfile(pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.8, 0.8))
        modal.open()

    """
    `Main.go_to_settings()`
    Called when user presses the profile button
    """
    def go_to_settings(self):
        modal = Settings(pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.8, 0.8))
        modal.open()

class AddWords(Screen):
    """
    A meaning textbox that the user can create by pressing the add meaning input button
    """
    class MeaningInput(TextInput):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.multiline = True
            self.size_hint_y = None
            self.height = 200
            self.hint_text = " Enter meaning"
            self.background_normal = "meaning_input.jpg"
            self.background_active = "meaning_input.jpg"
            self.padding = (10, 10) # padding_x = padding_y = 10

    # the textbox for the main word
    word = ObjectProperty(None)

    # list of meaning inputs
    meaningInputs = list()

    # meaning layout
    meanings_layout = ObjectProperty(None)

    # the button to pick a word list; the main button of the dropdown
    word_list_btn = ObjectProperty(None)

    # confirm button
    confirm = ObjectProperty(None)

    # cancel button
    cancel = ObjectProperty(None)

    # message for the notice modal
    message = str()

    """
    `AddWords.__init__(**kwargs)`

    Creates the add meaning button
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # word list the current word is in
        self.word_list = str()

        # Button to add a new MeaningInput
        self.add_meaning_btn = Button(size_hint_y = None, height = 95,
            background_normal="add_meaning.jpg")

        self.add_meaning_btn.bind(on_press=self.add_new_meaningInput)

        self.update()
    
    """
    `AddWords.add_new_meaningInput()`
    Called when user presses the add meaning input button
    
    1. Removes `self.add_meaning_btn` so that the added MeaningInput goes first
    2. Adds another meaningInput into the gridlayout and self.meaningInputs list
    3. Adds `self.add_nmeaning_btn` back
    """
    def add_new_meaningInput(self, btn: Button):
        self.meanings_layout.remove_widget(self.add_meaning_btn)
        self.meaningInputs.append(self.MeaningInput())
        self.meanings_layout.add_widget(self.meaningInputs[-1])
        self.meanings_layout.add_widget(self.add_meaning_btn)

    """
    `AddWords.update()`
    Called when screen is switched or confirm button pressed

    1. clears the word label and meaning labels
    2. dropdown list button
    4. dropdown itself (add new list button + everything else)
    """
    def update(self):
        # set word textinput to blank
        self.word.text = ''

        # remove the add meaning button
        self.meanings_layout.remove_widget(self.add_meaning_btn)

        # remove all meaning textinputs
        for meainginput in self.meaningInputs:
            self.meanings_layout.remove_widget(meainginput)
        
        # add a new one
        self.meaningInputs = [self.MeaningInput()]
        self.meanings_layout.add_widget(self.meaningInputs[0])

        # add the add meaning button to the end
        self.meanings_layout.add_widget(self.add_meaning_btn)

        self.word_list_btn.text = 'Choose List'
        self.word_list = ''
        self.createDropDown()

    """
    `AddWords.createDropDown()`
    Called when update is called

    1. Add a main button that the user clicks to open the dropdown
    2. Add word list buttons, binded to on_select of dropdown
    """
    def createDropDown(self):
        self.dropdown = DropDown()

        # [add new list] button created separately from the rest, binded to `self.add_new_list`
        btn = Button(text="Add new list", height=60, size_hint_y=None, color=(0, 0, 0, 1),
            background_normal="single_list.jpg")
        btn.bind(on_press=self.createAddNewListModal)
        self.dropdown.add_widget(btn)

        # other buttons are added based on word lists
        for word_list in word_lists:
            btn = Button(text=word_list, height=60, size_hint_y=None, color=(0, 0, 0, 1),
                background_normal="single_list.jpg")

            # when button is pressed, call select() in dropdown
            btn.bind(on_press = lambda btn: self.dropdown.select(btn.text))

            self.dropdown.add_widget(btn)

        # `self.word_selected` when selected
        self.dropdown.bind(on_select=self.word_selected)

    """
    `Addwords.word_selected(btn: Button, value: str)`
    Called when user chooses sth from the dropdown
    
    1. Change the text of the main button along with the property word_list
    """
    def word_selected(self, btn: Button, value: str):
        # change the current word list, these 2 values should always be changed together
        self.word_list = value
        self.word_list_btn.text = value
        
    """
    `AddWords.createAddNewListModal(btn: Button)`
    Called when the add new list button is pressed 

    1. This function creates and opens the modal view for the user to enter a new list
    2. When the confirm button is pressed in the modal view, self._add_new_list() is called
    """
    def createAddNewListModal(self, btn: Button):
        # modal view that contains a textinput and a confirm button 
        self.add_list_modal = ModalView(pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.8, 0.8))
        self.add_list_modal.background = "word_list_modal.jpg"

        # main layout for the modal view
        layout = FloatLayout()

        # textinput, confirm button (binded to `self._add_new_list`)
        self.modal_txtinpt = TextInput(pos_hint={"x": 0.1, "top": 0.8}, size_hint=(0.8, 0.4), 
            hint_text="type in the name of the new list", background_color=(137/255, 166/255, 215/255))

        self.modal_confirm_btn = Button(pos_hint={"center_x": 0.5, "top": 0.3}, size_hint=(0.6, 0.1),
            background_normal = "add_list.jpg")
        self.modal_confirm_btn.bind(on_press=self.add_new_list)

        # put stuff into the main layout
        layout.add_widget(self.modal_txtinpt)
        layout.add_widget(self.modal_confirm_btn)

        # button that dismiss the modal at the top left corner
        closeBtn = Button(pos_hint={"x":0.82, "top": 0.983}, size_hint=(0.13, 0.065),
            background_color=(0, 0, 0, 0))
        closeBtn.bind(on_press=self.add_list_modal.dismiss)
        layout.add_widget(closeBtn)

        self.add_list_modal.add_widget(layout)

        # open the modal view
        self.add_list_modal.open()
    
    """
    `AddWords.add_new_list(instance)`
    Called when the confirm button in the modal is pressed

    1. Checks if the user input is empty, if so do nothing
    2. Makes sure user can only create one new list for each word
    3. Adds new button to the dropdown
    4. Updates the text of the top button along wth sel.word_list
    """
    def add_new_list(self, instance):
        # the new list name that the user entered
        new_list = self.modal_txtinpt.text
        if len(new_list) != 0:
            # self.dropdown.children is a `GridLayout` that contains all the buttons
            dropdown_btns = self.dropdown.children[0].children

            # this is here so that the user can't just create an infinte amount of new lists
            # only one can be there. A new list is a list with no words
            for btn in dropdown_btns:
                # don't want to remove this button!
                if btn.text == 'Add new list': 
                    continue 
                if len(word_lists[btn.text]) == 0 and btn.text != new_list:
                    self.dropdown.remove_widget(btn)

            # add new list button to the dropdown
            btn = Button(text=new_list, height=60, size_hint_y=None)
            btn.bind(on_press = lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)

            # change the text of the main button of the dropdown to the text in the textbox
            self.word_list = self.modal_txtinpt.text
            self.word_list_btn.text = self.modal_txtinpt.text

            # after adding the new list, collapse the dropdown
            self.dropdown.dismiss()

            # dismiss the modal view
            self.add_list_modal.dismiss()

    """
    `AddWords.confirmed_pressed()`
    Called when confirm button is pressed

    1. If word already exists, X
    2. If first meaning is empty, X
    3. If word list not selected, X
    """
    def confirm_pressed(self):
        self.word.text = self.word.text.strip()
        self.word.text.replace('\n', '')

        meanings = []
        # get the text from all the textboxes
        for meaninginput in self.meaningInputs:
            meaninginput.text = meaninginput.text.strip()
            meaninginput.text = meaninginput.text.replace('\n', '')
            if len(meaninginput.text) != 0:
                meanings.append(meaninginput.text)

        # checks if all info is legal
        # if word exists
        if self.word.text in js['WordList'].keys():
            self.open_modal('The word is already in\nyour word list')
        # if text input is empty
        elif len(meanings) == 0:
            self.open_modal('Please fill in at least one blank')
        elif self.word_list_btn.text == 'Choose List':
            self.open_modal('Please select the word list')
        else:
            current_word = self.word.text # the current word
            # update js file
            js['WordList'][current_word] = [meanings, 0, 0, self.word_list]

            # update `word_lists` info
            word_lists[self.word_list].append(current_word)

            self.open_modal("Word saved")

            self.update()

    """
    `AddWords.confirmed_pressed()`
    Called when cancel button is pressed

    1. Clears everything
    """
    def cancel_pressed(self):
        self.update()
        self.open_modal("Cancelled")
    
    """
    Function that opens the modal view that displays `self.message`
    The modalview flashes for 0.5 secs
    """
    def open_modal(self, message: str):
        self.message = message
        modal = Notice()
        modal.bind(on_open=self.close_modal)
        modal.open()

    """
    Function that closes the modal view
    """
    def close_modal(self, modal):
        # pause for 0.5 seconds to let the user see the message
        time.sleep(0.5)
        modal.dismiss()

class WordsList(Screen):
    # main layout
    main_layout = ObjectProperty(None)

    # Button that lets user add another word, located 'on top' of the scroll view
    add_word_btn = ObjectProperty(None)

    # Scrollview for all the word lists
    scrollview = ScrollView()

    """
    `AddWords.__init__(**kwargs)`
    Constructor
    
    1. Creates add_word_btn, binded to self.add_word
    2. Calls update
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # I don't know why you can't just use "x" and "top"
        # https://stackoverflow.com/questions/6560587
        # 84/how-to-create-a-fixed-button-on-top-of-a-scrollview-in-kivy 

        # Note: you can't write this in kv lang since it needs to be after the scrollview
        self.add_word_btn = Button(pos_hint={"x": 0.61, "top": 0.338}, 
            size_hint=(0.3, 0.137), background_color=(0, 0, 0, 0))
        
        self.add_word_btn.bind(on_press=self.add_word)
        self.update()

    """
    `WordsList.update()`
    Called whenever the screen is switched to this

    1. Deletes empty lists from word_lists (bug?)
    2. Removes self.scrollview completely
    3. Goes through word_lists and puts a button into the gridlayout for each word list
    4. Adds the add word button after the layout so it stays unaffected by it
    """
    def update(self):
        # ???
        update_word_lists()

        # awkward... but need to add the add_word_btn AFTER the scrollview
        self.main_layout.remove_widget(self.add_word_btn)
        self.main_layout.remove_widget(self.scrollview)

        # scrollview that contains the word lists
        self.scrollview = ScrollView(pos_hint={"x": 0.07, "top": 0.959}, 
            size_hint=(0.84, 0.84), do_scroll=True)
        
        # inside it put a gridlayout with 2 columns
        scrollview_layout = GridLayout(size_hint_y=None, size_hint_x=1, 
            row_force_default=True, row_default_height=100, pos=(0, 0), cols=2, spacing=40)
        scrollview_layout.bind(minimum_height=scrollview_layout.setter('height'))

        # size_hint: 0.35 x 0.1

        # Put the buttons inside the gridlayout
        for word_list in word_lists:
            btn = Button(text=word_list, background_normal="word_list.jpg", font_size=20, 
                color=(0, 0, 0, 1))
            btn.bind(on_press=self.go_to_list)
            scrollview_layout.add_widget(btn)

        # add an empty button to the grid layout if the # of buttons is odd
        if len(word_lists) & 1: # if len(word_list) is odd
            scrollview_layout.add_widget(Button(disabled=True, background_color=(0, 0, 0, 0)))

        self.scrollview.add_widget(scrollview_layout)

        # add the scrollview before the add_word_btn
        self.main_layout.add_widget(self.scrollview)

        # add the add_word_btn after the scrollview
        self.main_layout.add_widget(self.add_word_btn)

    """
    `Dictionary.go_to_list()`
    Called when the user presses a word list

    1. Sets the title of the single list screen
    2. goes to single list screen
    """
    def go_to_list(self, btn: Button):
        word_list = btn.text

        # set title to list name
        self.manager.get_screen('single_list').list_name.text = word_list
        self.manager.get_screen('single_list').word_list = word_list

        # no prefix at the beginning
        self.manager.get_screen('single_list').search_textbox.text = ''
        self.manager.get_screen('single_list').update('')
        self.manager.transition.direction = 'right' 
        self.manager.current = 'single_list'

    """
    `Dictionary.add_word(btn: Button)`
    Called when user presses add word button

    1. Goes to add_words screen
    """
    def add_word(self, btn: Button):
        self.manager.get_screen('add_words').update()
        self.manager.current = 'add_words'

class SingleList(Screen):
    search_textbox = ObjectProperty(None)

    # The list name the user selected
    list_name = ObjectProperty(None)
    scrollview = ScrollView()
    word_list = str()

    """
    `SingleList.__init__(**kwargs)`
    1. main_layout: FloatLayout, everything fits in it
    2. search_textbox: User searches through it
    3. btn: Set Active button
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = FloatLayout() # the main floatlayout

        # lambda inst, val: self.update(val) reads textinput object, string and calls self.update 
        self.search_textbox.bind(text = lambda inst, val: self.update(val))

        # add everything in the main layout
        self.main_layout.add_widget(self.scrollview) # add an empty scrollview in the layout
                     # first so that it doesn't raise an exception when we call `main_layout.remove_widget`

        self.add_widget(self.main_layout)

    """
    `SingleList.update(prefix: str = '')`

    Button Bindings:
    view meaning: self.go_to_list
    delete word: self.delete_word

    1. Resets the entire ScrollView
    2. Matches all words with the prefix given
    3. Adds 2 buttons into the GirdLayout in the ScrollView, one for the word
        (which goes to a modal view) and a delete button (which deletes the word)
    """
    def update(self, prefix: str = ''):
        # re-initialize everything
        self.main_layout.remove_widget(self.scrollview)

        self.scrollview = ScrollView(pos_hint={"x": 0.08, "top": 0.8}, size_hint=(0.84, 0.63))

        scrollview_layout = GridLayout(size_hint_y=None, size_hint_x=1, cols=2, 
            row_force_default=True, row_default_height=100)
        scrollview_layout.bind(minimum_height=scrollview_layout.setter('height'))

        # list of words in this word list
        self.words = word_lists[self.word_list]

        for word in self.words:
            # make sure prefix of both string matches 
            if word[: len(prefix)] != prefix: continue

            # no need to add another layout here, just set `cols=2` for the GridLayout

            # word button, triggers modal view
            word_btn = Button(text=word, pos_hint={"x": 0, "bottom": 1}, size_hint=(0.8, 1),
                background_normal="word.jpg", color=(0, 0, 0, 1))
            word_btn.bind(on_press=self.go_to_word)

            # delete button, triggers word deletion
            delete_btn = Button(pos_hint={"x": 0.78, "bottom": 1}, size_hint=(0.2, 1), 
                background_normal="delete.jpg")
            delete_btn.bind(on_press=self.delete_word)

            scrollview_layout.add_widget(word_btn)
            scrollview_layout.add_widget(delete_btn)
        
        self.scrollview.add_widget(scrollview_layout)
        self.main_layout.add_widget(self.scrollview)

    """
    `SingleList.set_active(btn: Button)`
    Called when the set active button is pressed
    1. Sets the list to practice in main screen to the current list
    """
    def set_active(self, btn: Button):
        print("New word list: {}".format(self.word_list))
        self.manager.get_screen('main_screen').list_to_practice = self.word_list

    """
    `SingleList.delete_word()`
    Called when a delete button is called
    
    1. Finds the index of the delete button in the gridlayout, and figures out the index of the 
        word button. 
    2. Removes word info from word_lists and js file
    3. Call self.update(original prefix)
    """
    def delete_word(self, delete_btn: Button):
        # the index of the 'x' button in the children list 
        # this is soooooo messy, might need to clean this up

        pos = self.scrollview.children[0].children.index(delete_btn) # help!
        word_btn = self.scrollview.children[0].children[pos + 1]
        # removes the corresponding word button
        self.scrollview.children[0].remove_widget(word_btn)

        # remove word from word lists
        word_lists[self.word_list].remove(word_btn.text)
        if len(word_lists[self.word_list]) == 0:
            word_lists.pop(self.word_list)

        # remove from js file
        js['WordList'].pop(word_btn.text)

        # call update since word list changed
        self.update(self.search_textbox.text)

    """
    `SingleList.go_to_word()`
    Called when word button is pressed, opens modal view
    """
    def go_to_word(self, btn: Button):
        modal = WordModalView(btn.text, pos_hint={"x": 0.1, "bottom": 0.1}, size_hint=(0.8, 0.8))
        modal.open()

class WordModalView(ModalView):
    main_layout = FloatLayout()

    """
    `self.WordModalView.__init__`

    1. Adds meanings to a scrollview, the rest is in the kv
    """
    def __init__(self, word: str, **kwargs):
        super().__init__(**kwargs)
        self.word = word # save it as instance variable 
        self.word_label.text = word

        scrollview = ScrollView(pos_hint={"x": 0.05, "top": 0.75}, size_hint=(0.9, 0.7), do_scroll=True)

        scrollview_layout = GridLayout(size_hint_y=None, size_hint_x=1, cols=1, 
            spacing=50)
        scrollview_layout.bind(minimum_height=scrollview_layout.setter('height'))

        # the 3 meaning labels
        meanings = js['WordList'][word][0] # list of meanings
        self.btn_list = list()

        for i in range(len(meanings)):
            btn = WrappedButton(text=meanings[i], font_size=30, padding=(20, 20),
                color=(0, 0, 0, 1), background_normal="meaning_label.jpg")
            btn.size_hint_y = None
            btn.padding_x = 50

            btn.bind(on_press=self.edit)
            self.btn_list.append(btn)
            scrollview_layout.add_widget(btn)

        scrollview.add_widget(scrollview_layout)
        self.main_layout.add_widget(scrollview)

    """
    `WordModalView.edit`
    Called when a meaning is pressed
    
    1. Creates another modalview that lets user enter the new meaning
    2. Changes meaning in the hs file
    """
    def edit(self, btn: Button):
        # modal view that contains a textinput and a confirm button 
        self.modal = ModalView(pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.8, 0.8))
        self.modal.background = "word_list_modal.jpg"

        # main layout for the modal view
        layout = FloatLayout()

        # text input for the user to enter
        self.modal_txtinpt = TextInput(pos_hint={"x": 0.1, "top": 0.8}, size_hint=(0.8, 0.4), 
            text=btn.text, background_color=(137/255, 166/255, 215/255))

        # confirm button
        self.modal_confirm_btn = Button(pos_hint={"center_x": 0.5, "top": 0.3}, size_hint=(0.6, 0.1),
            background_normal = "confirm_change_meaning.jpg")

        self.modal_confirm_btn.bind(on_press = lambda x: self.process(btn))

        # put stuff into the main layout
        layout.add_widget(self.modal_txtinpt)
        layout.add_widget(self.modal_confirm_btn)

        # button that dismiss the modal at the top left corner
        closeBtn = Button(pos_hint={"x":0.82, "top": 0.983}, size_hint=(0.13, 0.065),
            background_color=(0, 0, 0, 0))
        closeBtn.bind(on_press=self.modal.dismiss)
        layout.add_widget(closeBtn)

        self.modal.add_widget(layout)
        # When the modal is dismissed, call self.save_new_defs
        self.modal.bind(on_dismiss=self.save_new_defs)

        # open the modal view
        self.modal.open()

    """
    `WordModalView.process(btn: Button)`
    Binded to confirm button

    1. Changes the text of the button to the text in the text input if it is not empty
    """
    def process(self, btn: Button):
        if len(self.modal_txtinpt.text) != 0:
            btn.text = self.modal_txtinpt.text
            self.modal.dismiss()

    """
    `WordModalView.save_new_defs(btn: Button)`
    Binded to on_dismiss of the modal

    1. Saves the text to the js file
    """
    def save_new_defs(self, modal: ModalView):
        for i in range(len(self.btn_list)):
            js['WordList'][self.word][0][i] = self.btn_list[i].text

class Dictionary(Screen):
    search_textbox = ObjectProperty(None)
    search_button = ObjectProperty(None)
    target_word = ObjectProperty(None)
    word_missing = ObjectProperty(None)

    meaning_labels = list()
    # meaning layout
    meanings_layout = ObjectProperty(None)

    """
    `Dictionary.update()`
    Called whenever the current screen is switched to this one, or another word is searched
    1. Sets meaning labels to blank
    2. Sets textbox to blank
    3. Sets word missing label to blank
    """
    def update(self):
        # set the 'word missing' label to invisible
        self.search_textbox.text = ''
        self.word_missing.text = ''
        self.target_word.text = ''

        # clear all meanings
        for label in self.meaning_labels:
            self.meanings_layout.remove_widget(label)
        self.meaning_labels.clear()

    """
    `Dictionary.show()`
    Called whenever the user presses the search button
    1. Resets labels, textbox, etc.
    2. Returns if searched string is empty
    3. If word missing, set `self.word_missing` text to visible
    4. Otherwise, set the meaning labels to visible
    """
    def show(self):
        # word that the user inputted
        text_input = self.search_textbox.text
        self.update()

        # if input is empty, just ignore
        if len(text_input) == 0:
            return

        word = text_input.strip()

        # find the word in the js file, get(word) == None is when the word doesn't exist
        if js['WordList'].get(word) == None:
            self.word_missing.text = "Word missing :("
        else:
            self.target_word.text = word
            meanings = js['WordList'][word][0] # list of meanings
            for i in range(len(meanings)):
                # Actually a button since label doesn't have background_normal
                lbl = WrappedButton(text=meanings[i], font_size=30, padding=(20, 20), 
                    disabled_color=(0, 0, 0, 1), background_disabled_normal="meaning_label.jpg")
                lbl.disabled = True
                lbl.size_hint_y = None
                lbl.padding_x = 50

                self.meaning_labels.append(lbl)
                self.meanings_layout.add_widget(lbl)

# add screens
screen_manager.add_widget(Main(name="main_screen"))
screen_manager.add_widget(AddWords(name="add_words"))
screen_manager.add_widget(WordsList(name="words_list"))
screen_manager.add_widget(SingleList(name='single_list'))
screen_manager.add_widget(Dictionary(name="dictionary"))

class Notice(ModalView):
    screen = screen_manager.get_screen('add_words')

class UserProfile(ModalView):
    main_layout = FloatLayout()
    cpb = ObjectProperty(None)
    learned = ObjectProperty(None)
    familiar = ObjectProperty(None)
    to_learn = ObjectProperty(None)
    done = ObjectProperty(None)
    goal = ObjectProperty(None)
    username = ObjectProperty(None)
    scrollview_layout = ObjectProperty(None)

    """
    `UserProfile.__init__(**kwargs)`

    1. Creates the scrollview that includes stats of every word list
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cpb.value += 1 # buggy code...
        self.cpb.value -= 1

        update_word_lists()
    
        for word_list in word_lists:
            # get the stats from the json file
            total_answered = 0
            answered_correct = 0
            for word in word_lists[word_list]:
                answered_correct += js['WordList'][word][1]
                total_answered += js['WordList'][word][2]

            layout = FloatLayout(size_hint_y=None, height=132.5)

            # the button for background, covers the entire screen
            btn = Button(pos_hint={"x": 0, "top": 1}, size_hint=(1, 1), disabled=True,
                background_disabled_normal="user_profile_list.jpg")
            layout.add_widget(btn)
            
            # name of the word list
            lbl = Label(pos_hint={"x": 0.089, "top": 0.762}, size_hint=(0.58, 0.24), 
                text=word_list, font_size=25, color=(0, 0, 0, 1), halign='left')
            lbl.bind(size=lbl.setter('text_size'))

            layout.add_widget(lbl)

            # avoid division by 0
            if total_answered == 0: correct_p = 0
            else: correct_p = answered_correct / total_answered

            # progress bar made by buttons
            btn_left = Button(pos_hint={"x": 0.089, "top": 0.438}, disabled=True,
                size_hint=(0.55 * correct_p, 0.08), background_disabled_normal="dark_blue.jpg")
            btn_right = Button(pos_hint={"x": 0.089 + 0.55 * correct_p, "top": 0.438}, disabled=True,
                size_hint=(0.55 * (1 - correct_p), 0.08), background_disabled_normal="light_blue.jpg")

            # weird things happen when correct_p = 0 (the button still gets shown)
            if correct_p > 0:
                layout.add_widget(btn_left)
            layout.add_widget(btn_right)

            # Correct percentage
            lbl = Label(pos_hint={"x": 0.73, "top": 0.59}, size_hint=(0.15, 0.21), 
                text=str(round(correct_p * 100)) + "%", color=(0, 0, 0, 1), font_size=25)

            layout.add_widget(lbl)

            self.scrollview_layout.add_widget(layout)


    """
    `UserProfile.update()`
    Called when the modal is initialized. Called by the username label in the kv.

    1. Creates learned (list), familiar (list), and to_learn (list)
    2. Sets up the CPB of done/goal
    """
    # this will be called by the username label, but it will update everything
    def update(self):
        learned = []
        familiar = []
        to_learn = []

        for word in js['WordList']:
            # avoid division by 0
            correct_percentage = 0 if js['WordList'][word][2] == 0 \
                else js['WordList'][word][1] / js['WordList'][word][2]

            if correct_percentage > LEARNED_THRESHOLD:
                learned.append(word)
            elif correct_percentage > FAMILIAR_THRESHOLD:
                familiar.append(word)
            else:
                to_learn.append(word)
        
        self.learned.text = str(len(learned))
        self.familiar.text = str(len(familiar))
        self.to_learn.text = str(len(to_learn))

        # only count correct answers, since if we count incorrect ones 
        # a question can produce 4 tries
        total_answered = total_question_answered_correct

        for login in js['Login info']['all logins']:
            timelist = time.localtime()[:4]
            login_time = login[0]

            # if the login is within one day
            if login_time[2] == timelist[2] and login_time[1] == timelist[1] and login_time[0] == timelist[0]:
                # login[2] is the total number of questions answered
                total_answered += login[1]

        self.done.text = str(total_answered)
        self.goal.text = str(js['User']['goal'])

        self.cpb.max = max(1, js['User']['goal'])
        self.cpb.value = total_answered

        # remember this is called by the username label so return the text
        return js['User']['name']
        
class Settings(ModalView):
    main_screen = screen_manager.get_screen('main_screen')
    main_layout = FloatLayout()
    """
    `Settings.__init__(**kwargs)`
    Creates all the GUI, no kv

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Username button
        username = Button(text=js['User']['name'], font_size=40, color=(0, 0, 0, 1),
            pos_hint={"x": 0.05, "top": 0.9}, size_hint=(0.9, 0.1), background_color=(0, 0, 0, 0))
        username.bind(on_press=self.edit)

        self.main_layout.add_widget(username)


        # light/dark mode
        light_mode = ToggleButton(text='Light', group='mode', background_color=(92/255, 103/255, 204/255, 0.5),
            pos_hint={"x": 0.3, "top": 0.75}, size_hint=(0.2, 0.05))
        light_mode.bind(on_press=self.change_mode)

        dark_mode = ToggleButton(text='Dark', group='mode', background_color=(92/255, 103/255, 204/255, 0.5),
            pos_hint={"x": 0.5, "top": 0.75}, size_hint=(0.2, 0.05), color=(0, 0, 0, 1))
        dark_mode.bind(on_press=self.change_mode)

        if js['User']['mode'] == 'light':
            light_mode.state = "down"
        else:
            dark_mode.state = "down"

        self.main_layout.add_widget(light_mode)
        self.main_layout.add_widget(dark_mode)
        

        # daily goal
        daily_goal = Button(text="Daily goal: {}".format(js['User']['goal']), halign='left', color=(0, 0, 0, 1), font_size=35,
            valign='middle', pos_hint={"x": 0.05, "top": 0.65}, size_hint=(0.9, 0.1), background_color=(0, 0, 0, 0))
        daily_goal.bind(size=daily_goal.setter('text_size'))    
        daily_goal.halign='center'
        daily_goal.bind(on_press=self.edit)

        self.main_layout.add_widget(daily_goal)

    """
    `Settings.edit(btn: Button)`
    Called when the user presses one of the buttons

    1. Creates a modal for the user to enter new infos (same with the WordModalView)
    """
    def edit(self, btn: Button):
        # modal view that contains a textinput and a confirm button 
        self.modal = ModalView(pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.8, 0.8))
        self.modal.background = "word_list_modal.jpg"

        # main layout for the modal view
        layout = FloatLayout()

        # text input for the user to enter
        self.modal_txtinpt = TextInput(pos_hint={"x": 0.1, "top": 0.8}, size_hint=(0.8, 0.4), 
            text=btn.text, background_color=(137/255, 166/255, 215/255))

        # confirm button
        self.modal_confirm_btn = Button(pos_hint={"center_x": 0.5, "top": 0.3}, size_hint=(0.6, 0.1),
            background_normal = "confirm_change_meaning.jpg")

        self.modal_confirm_btn.bind(on_press = lambda x: self.process(btn))

        # put stuff into the main layout
        layout.add_widget(self.modal_txtinpt)
        layout.add_widget(self.modal_confirm_btn)

        # button that dismiss the modal at the top left corner
        closeBtn = Button(pos_hint={"x":0.82, "top": 0.983}, size_hint=(0.13, 0.065),
            background_color=(0, 0, 0, 0))
        closeBtn.bind(on_press=self.modal.dismiss)
        layout.add_widget(closeBtn)

        self.modal.add_widget(layout)

        # open the modal view
        self.modal.open()

    """
    `Settings.process(btn: Button)`
    Called when user presses the confirm button

    1. Changes information based on which button is pressed
    """
    def process(self, btn: Button):
        # change daily goal
        if btn.text[:12] == 'Daily goal: ':
            str_to_check = self.modal_txtinpt.text.strip()
            if self.modal_txtinpt.text[:12] == 'Daily goal: ':
                str_to_check = self.modal_txtinpt.text[12:].strip()

            try:
                int(str_to_check)
            except ValueError:
                None 
            finally:
                goal = int(str_to_check)
                if goal > 0:
                    js['User']['goal'] = goal
                    btn.text = btn.text[: 12] + str(goal)
                    self.modal.dismiss()
        # change username
        else:
            name = self.modal_txtinpt.text.strip()
            if len(name) != 0:
                js['User']['name'] = name
                btn.text = name
                self.modal.dismiss()

    """
    `Settings.change_mode`
    Called when the toggle button (light/dark mode) is pressed, currently not doing anything
    """
    def change_mode(self, btn: Button):
        print("Current Mode:", btn.text)
        js['User']['mode'] = btn.text.lower()

class Vocabulary_LearnerApp(App):
    def build(self):
        return screen_manager

    def on_start(self):
        Window.size = (1125 / 4, 2436 / 4)

        generate_word_lists()

        # current word list to practice
        current_list = js['User']['list']
        # users can delete an active list, so now the list either exists or is an empty str
        if len(word_lists[current_list]) == 0:
            js['User']['list'] = ''
        screen_manager.get_screen('main_screen').list_to_practice = js['User']['list']

        # remove logins past 1 week

        all_logins = js['Login info']['all logins'] # a list of all logins
        # all_logins is a reference

        # year, month, day, hour
        timelist = time.localtime()[:4]

        # early logins appears first
        while len(all_logins) > 0:
            if all_logins[0][0][2] < timelist[2] - 7 \
                or all_logins[0][0][1] != timelist[1] or all_logins[0][0][0] != timelist[0]:
                all_logins.pop(0)
            else: 
                break

        # switch to Main Screen, call update()
        screen_manager.get_screen('main_screen').update()
        screen_manager.current = 'main_screen'

    def on_stop(self):
        timelist = time.localtime()[:4]

        loginfo = [timelist, total_question_answered_correct, total_question_answered]
        js["Login info"]["last login"] = loginfo
        js["Login info"]["all logins"].append(loginfo)

        js['User']['list'] = screen_manager.get_screen('main_screen').list_to_practice

        # save score
        file = open('Vocabulary_Words.json', 'w')
        json.dump(js, file, indent=4)
        file.close()
        print('Thanks for using my App, bye!')


if __name__ == '__main__':
    Vocabulary_LearnerApp().run()
