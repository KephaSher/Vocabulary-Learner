import json
from random import randint
import time
from collections import defaultdict

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from kivy.core.text import Label as textLabel
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from circular_progress_bar import CircularProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.dropdown import DropDown

# load kv file
Builder.load_file("vocab.kv")

file = open('Vocabulary_Words.json', 'r')
js = json.load(file)

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

# Because looping through the words everytime is very inefficient, create a dictionary 
# that maps lists to words

word_lists = defaultdict(lambda: [])

def generate_word_lists():
    word_lists.clear()
    for word in js['WordList']:
        word_lists[js['WordList'][word][3]].append(word)   
def update_word_lists():        
    i = 0
    while i < len(word_lists):
        if len(list(word_lists.values())[i]) == 0:
            word_lists.pop(list(word_lists.keys())[i])
        else: i += 1
generate_word_lists()

total_question_answered = 0
total_question_answered_correct = 0

class Main(Screen):
    # total number of times the current word is answered
    total_answered = ObjectProperty(None)

    # the number of correct times the current word is answered
    correctness = ObjectProperty(None)


    # the next button
    next = ObjectProperty(None)
    
    # CPB of correct percentage
    correct_percentage = ObjectProperty(None)

    # label: number of times answered correctly
    correct_num = ObjectProperty(None)

    # label: number of times answered incorrectly
    incorrect_num = ObjectProperty(None)

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
        username = js['User']["name"].split()

        hour = time.localtime()[3]
        if hour > 7 and hour < 13:
            self.greetings.text = "Good Morning, " + username[0]
        elif hour > 12 and hour < 19:
            self.greetings.text = "Good Afternoon, " + username[0]
        else:
            self.greetings.text = "Good Evening, " + username[0]

        if self.play_valid():
            self.get_word()
        else:
            self.deactivate()

        # # update questions_answered
        # # -------------------------

        # # max: the user's goal of how many questions they want to answer
        # self.total_answered.max = js['User']['goal']

        # # value: how many questions they actually answered
        # self.total_answered.value = min(self.total_answered.max, new_questions_answered)

        # today = time.localtime()[2]

        # # add all of the questions answered from previous logins from the today
        # for login in js['Login info']['all logins']:
        #     if login[0][2] == today and self.total_answered.value < self.total_answered.max:
        #         self.total_answered.value = min(
        #             self.total_answered.value + login[2], self.total_answered.max)

        # self.total_answered._default_label_text = str(self.total_answered.value) + " / " \
        #     + str(self.total_answered.max) + "\n   {}%"
        # self.total_answered._text_label.refresh()

        # update correctness
        # ------------------

        # # the questions answered correctly today
        # correct_count = 0

        # # number of questions answered today
        # total_count = 0

        # # these are used to figure out the precentage of correctness

        # # calculate precentage from questions answered from previous logins from the today
        # for login in js['Login info']['all logins']:
        #     if login[0][2] == today:
        #         correct_count += login[1]
        #         total_count += login[2]

        # # update questions_correct
        # self.correctness.max = max(total_count + new_questions_answered, 1) # max has to be at least 1
        # self.correctness.value = correct_count + new_questions_correct

        # self.correctness._default_label_text = "Correct\n   {}%"
        # self.correctness._text_label.refresh()

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


        # selects the correct word `self.wordName`
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
        self.correct_num.text = "Answered correctly " + \
            str(js['WordList'][self.wordName][1]) + " time(s)"

        self.incorrect_num.text = "Answered incorrectly " + \
            str(js['WordList'][self.wordName][2] - js['WordList'][self.wordName][1]) \
                    + " time(s)"

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

class AddWords(Screen):
    word = ObjectProperty(None)
    mean1 = ObjectProperty(None)
    mean2 = ObjectProperty(None)
    mean3 = ObjectProperty(None)
    word_list_btn = ObjectProperty(None)
    confirm = ObjectProperty(None)
    cancel = ObjectProperty(None)

    """
    `AddWords.__init__(**kwargs)`
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # word list the current word is in
        self.word_list = str()
        self.update()
    
    """
    `AddWords.update()`
    Called when screen is switched

    1. clears the word label and meaning labels
    2. dropdown list button
    4. dropdown itself (add new list button + everything else)
    """
    def update(self):
        widget_list = [self.word, self.mean1, self.mean2, self.mean3]
        for widget in widget_list: widget.text = ''

        self.word_list_btn.text = 'choose list'
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
        btn = Button(text="Add new list", height=60, size_hint_y=None)
        btn.bind(on_press=self.createAddNewListModal)
        self.dropdown.add_widget(btn)

        # other buttons are added based on word lists
        for word_list in word_lists:
            btn = Button(text=word_list, height=60, size_hint_y=None)

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
        # main layout for the modal view
        layout = FloatLayout()

        # textinput, confirm button (binded to `self._add_new_list`)
        self.modal_txtinpt = TextInput(pos_hint={"x": 0.1, "top": 0.8}, size_hint=(0.8, 0.2))
        self.modal_confirm_btn = Button(pos_hint={"center_x": 0.5, "top": 0.3}, size_hint=(0.6, 0.1), text='add list')
        self.modal_confirm_btn.bind(on_press=self.add_new_list)

        # put stuff into the main layout
        layout.add_widget(self.modal_txtinpt)
        layout.add_widget(self.modal_confirm_btn)

        # button that dismiss the modal at the top left corner
        btn = Button(pos_hint={"x":0.85, "top": 1}, size_hint=(0.15, 0.07), text='x')
        btn.bind(on_press=self.add_list_modal.dismiss)
        layout.add_widget(btn)

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
    4. 
    """
    def confirm_pressed(self):
        # checks if all info is legal

        # if word exists
        if self.word.text in js['WordList'].keys():
            popup = InputError('The word is already in\nyour word list')
            popup.open()
        # if text input is empty
        elif len(self.mean1.text) == 0:
            popup = InputError('Please fill in the blanks\nthat are not optional')
            popup.open()
        elif self.word_list_btn.text == 'choose list':
            popup = InputError('Please select the word list')
            popup.open()
        else:
            current_word = self.word.text # the current word
            meanings = [self.mean1.text, self.mean2.text, self.mean3.text]

            mean_list = [] # list of meanings

            for meaning in meanings:
                if meaning != '':
                    mean_list.append(meaning)

            # update js file
            js['WordList'][current_word] = [mean_list, 0, 0, self.word_list]

            # update `word_lists` info
            word_lists[self.word_list].append(current_word)

            popup = Notice('save', self)
            popup.open()

    def cancel_pressed(self):
        popup = Notice('cancel', self)
        popup.open()

class WordsList(Screen):
    main_layout = ObjectProperty(None)
    add_word_btn = ObjectProperty(None)
    scrollview = ScrollView()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # I don't know why you can't just use "x" and "top"
        # https://stackoverflow.com/questions/6560587
        # 84/how-to-create-a-fixed-button-on-top-of-a-scrollview-in-kivy 

        # Note: you can't write this in kv lang since it needs to be after the scrollview
        self.add_word_btn = Button(text="add word", 
            pos_hint={"center_x": 0.75, "center_y": 0.2}, size_hint=(0.3, 0.1))
        
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
        self.scrollview = ScrollView(pos_hint={"x": 0, "top": 1}, 
            size_hint=(1, 0.9), do_scroll=True)
        
        # inside it put a gridlayout with 2 columns
        scrollview_layout = GridLayout(size_hint_y=None, size_hint_x=1, 
            row_force_default=True, row_default_height=100, pos=(0, 0), cols=2)

        # size_hint: 0.35 x 0.1

        # Put the buttons inside the gridlayout
        for word_list in word_lists:
            btn = Button(text=word_list)
            btn.bind(on_press=self.go_to_list)
            scrollview_layout.add_widget(btn)

        # add an empty button to the grid layout if the # of buttons is odd
        if len(word_lists) & 1: # if len(word_list) is odd
            scrollview_layout.add_widget(Button(disabled=True))

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

        # add the search textbox
        self.search_textbox = TextInput(pos_hint={"x": 0.1, "top": 0.90},
            size_hint=(0.8, 0.07), multiline=False)

        # lambda inst, val: self.update(val) reads textinput object, string and calls self.update 
        self.search_textbox.bind(text = lambda inst, val: self.update(val))


        # add the set as active button
        btn = Button(pos_hint={"center_x": 0.5, "bottom": 1}, size_hint=(0.4, 0.1), text='set active')
        btn.bind(on_press=self.set_active)


        # add everything in the main layout
        self.main_layout.add_widget(btn)
        self.main_layout.add_widget(self.search_textbox)
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
        self.scrollview = ScrollView(pos_hint={"x": 0, "top": 0.8}, size_hint=(1, 0.7))
        scrollview_layout = GridLayout(size_hint_y=None, size_hint_x=1, 
            row_force_default=True, row_default_height=50, pos=(0, 0), cols=2)

        # list of words in this word list
        self.words = word_lists[self.word_list]

        for word in self.words:
            # make sure prefix of both string matches 
            if word[: len(prefix)] != prefix: continue

            # no need to add another layout here, just set `cols=2` for the GridLayout

            # word button, triggers modal view
            word_btn = Button(text=word, pos_hint={"x": 0, "bottom": 1}, size_hint=(0.9, 1))
            word_btn.bind(on_press=self.go_to_word)

            # delete button, triggers word deletion
            delete_btn = Button(text='x', pos_hint={"x": 0.9, "bottom": 1}, size_hint=(0.1, 1))
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
        print("[INFO   ] [Me        ] New word list: {}".format(self.word_list))
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
    def __init__(self, word: str, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout() # main layout 

        # word label on the top
        main_layout.add_widget(Label(text=word, font_size=40,
            pos_hint={"x": 0.1, "top": 0.9}, size_hint=(0.8, 0.1)))

        # the 3 meaning labels
        meanings = js['WordList'][word][0] # list of meanings
        if len(meanings) > 0:
            label = Label(text=meanings[0], pos_hint={"x": 0.1, "top": 0.8}, 
                size_hint=(0.8, 0.2), font_size=30) # HOW DO I MAKE IT ALIGN LEFT AHHHHH
            main_layout.add_widget(label)

        if len(meanings) > 1:
            label = Label(text=meanings[1], pos_hint={"x": 0.1, "top": 0.6}, 
                size_hint=(0.8, 0.2), font_size=30)
            main_layout.add_widget(label)

        if len(meanings) > 2:
            label = Label(text=meanings[2], pos_hint={"x": 0.1, "top": 0.4}, 
                size_hint=(0.8, 0.2), font_size=30)
            main_layout.add_widget(label)

        # the close button
        close_btn = Button(pos_hint={"x": 0.85, "top":1}, size_hint=(0.15, 0.07))
        close_btn.bind(on_press=self.dismiss)
        main_layout.add_widget(close_btn)

        self.add_widget(main_layout)

class Dictionary(Screen):
    search_textbox = ObjectProperty(None)
    search_button = ObjectProperty(None)
    target_word = ObjectProperty(None)
    word_missing = ObjectProperty(None)
    meaning1 = ObjectProperty(None)
    meaning2 = ObjectProperty(None)
    meaning3 = ObjectProperty(None)

    """
    `Dictionary.update()`
    Called whenever the current screen is switched to this one, or another word is searched
    1. Sets meaning labels to blank
    2. Sets textbox to blank
    3. Sets word missing label to blank
    """
    def update(self):
        # set the 'word missing' label to invisible
        self.word_missing.text = ''
        self.target_word.text = ''
        self.meaning1.text = ''
        self.meaning2.text = ''
        self.meaning3.text = ''

    """
    `Dictionary.show()`
    Called whenever the user presses the search button
    1. Resets labels, textbox, etc.
    2. Returns if searched string is empty
    3. If word missing, set `self.word_missing` text to visible
    4. Otherwise, set the meaning labels to visible
    """
    def show(self):
        self.update()

        # word that the user inputted
        text_input = self.search_textbox.text

        # if input is empty, just ignore
        if len(text_input) == 0:
            return

        word = text_input.strip().lower()

        # find the word in the js file, get(word) == None is when the word doesn't exist
        if js['WordList'].get(word) == None:
            self.word_missing.text = "Word missing :("
        else:
            self.target_word.text = word
            meanings = js['WordList'][word][0] # list of meanings
            # set the 3 meanings
            if len(meanings) > 0:
                self.meaning1.text = meanings[0]
            if len(meanings) > 1:
                self.meaning2.text = meanings[1]
            if len(meanings) > 2:
                self.meaning3.text = meanings[2]

class Notice(Popup):
    # popup when the user cancels or save
    def __init__(self, kind, widget, **kwargs):
        super().__init__(**kwargs)
        self.widget = widget
        self.content = FloatLayout()

        # if the user wants to save it
        if kind == 'save':
            text = 'Your words has been saved'
            self.btn = Button(text='close', pos_hint={
                              "x": 0.3, "top": 0.3}, size_hint=(0.4, 0.25), font_size=30)
            self.btn.bind(on_press=self.dismiss)
            self.content.add_widget(self.btn)
        # if the user wants to cancel
        else:
            text = 'Are you sure to cancel?'
            self.yes = Button(text='Yes', pos_hint={
                              "x": 0.1, "top": 0.3}, size_hint=(0.3, 0.2))
            self.no = Button(text='No', pos_hint={
                             "x": 0.6, "top": 0.3}, size_hint=(0.3, 0.2))
            self.content.add_widget(self.yes)
            self.content.add_widget(self.no)
            self.yes.bind(on_press=self.press)
            self.no.bind(on_press=self.dismiss)

        self.content.add_widget(Label(text=text, pos_hint={"x": 0.15, "top": 0.95},
                                      size_hint=(0.7, 0.1)))
        self.title = 'Notice'
        self.size_hint = (0.5, 0.35)
        self.pos_hint = {"x": 0.25, "top": 0.75}

    def press(self, *args):
        # clears text if cancel pressed
        self.widget.update()
        self.dismiss()

class InputError(Popup):
    # popup for if input is incorrect for adding a word
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.content = FloatLayout()
        self.label = Label(text=text, pos_hint={
                           "x": 0.1, "top": 0.9}, size_hint=(0.8, None), font_size=30)
        self.content.add_widget(self.label)
        self.btn = Button(text='Close', pos_hint={
                          "x": 0.35, "top": 0.25}, size_hint=(0.3, 0.2))
        self.btn.bind(on_press=self.close)
        self.content.add_widget(self.btn)
        self.title = 'Error'
        self.pos_hint = {"x": 0.25, "top": 0.75}
        self.size_hint = (0.5, 0.35)

    def close(self, *args):
        self.dismiss()


# add windows
screen_manager = ScreenManager()
screen_manager.add_widget(Main(name="main_screen"))
screen_manager.add_widget(AddWords(name="add_words"))
screen_manager.add_widget(WordsList(name="words_list"))
screen_manager.add_widget(SingleList(name='single_list'))
screen_manager.add_widget(Dictionary(name="dictionary"))


class Vocabulary_LearnerApp(App):
    def build(self):
        return screen_manager

    def on_start(self):
        Window.size = (1125 / 4, 2436 / 4)

        generate_word_lists()

        # remove logins past 1 week

        all_logins = js['Login info']['all logins'] # a list of all logins
        # all_logins is a reference

        today = time.localtime()[2]

        # early logins appears first
        while len(all_logins) > 0 and all_logins[0][0][2] < today - 7: # BUG: 2020/25, 2021/27
            all_logins.pop(0)

        # switch to Main Screen, call update()
        screen_manager.get_screen('main_screen').update()
        screen_manager.current = 'main_screen'

    def on_stop(self):
        timelist = time.localtime()[:4]

        loginfo = [timelist, total_question_answered_correct, total_question_answered]
        js["Login info"]["last login"] = loginfo
        js["Login info"]["all logins"].append(loginfo)

        # save score
        file = open('Vocabulary_Words.json', 'w')
        json.dump(js, file, indent=4)
        file.close()
        print('saved')


if __name__ == '__main__':
    Window.clearcolor = (179/255, 1, 1, 0)
    Vocabulary_LearnerApp().run()
