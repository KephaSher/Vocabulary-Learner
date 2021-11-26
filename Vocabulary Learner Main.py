import json
from random import randint
import time

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
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen

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
            synonyms (list)
            sentence (list)
            type (list)
            answered correctly (int)
            answered total (int)
    LearnedWords (str):
        word (str): 
            meanings (list)
            synonyms (list)
            sentence (list)
            type (list)
            answered correctly (int)
            answered total (int)
"""


class Main(Screen):
    total_answered = ObjectProperty(None)
    correctness = ObjectProperty(None)

    # constructor, this is only called once. Even when the screen changes, 
    # it doesn't make a new instance
    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)

        # popup to ask to import words from a lesson.
        # Contains a text input for lesson number.
        self.lessonNum = 0
        self.popup = LessonNumPopup(self)

        # add the labels to the CPBs, the text will change when they the user
        # answers questions
        self.total_answered.label = textLabel(font_size=35)
        self.correctness.label = textLabel(font_size=35)

        # if you remove this the text of CPBs won't show at first, 
        # but if you switch screens and switch again, it shows.
        # the first display is based on the constructor? idk
        self.update()

    def save(self, *args):
        self.popup.open()


    # ----------------- checks if playing is valid -------------------------
    def find4(self, counted, nextList):
        if len(counted) == 4:
            return True
        if nextList >= len(js['WordList']):
            return False
        mean = js['WordList'][list(js['WordList'].keys())[nextList]][0]
        for i in mean:
            if i not in counted:
                counted.append(i)
                if self.find4(counted, nextList+1):
                    return True
        return False

    def play_valid(self):
        return self.find4(list(), 0)
    # ----------------------------------------------------------------------

    # this is called whenever the current screen is switched to this screen
    # params: new_questions_answered, new_questions_correct
    # - These are the NEW questions BEFORE going to this screen (from last visit of this screen)
    def update(self, new_questions_answered=0, new_questions_correct=0):
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

        
        # update questions_answered
        # -------------------------

        # max: the user's goal of how many questions they want to answer
        self.total_answered.max = js['User']['goal']

        # value: how many questions they actually answered
        self.total_answered.value = min(self.total_answered.max, new_questions_answered)

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
        self.correctness.max = max(total_count + new_questions_answered, 1) # max has to be at least 1
        self.correctness.value = correct_count + new_questions_correct

        self.correctness._default_label_text = "Correct\n   {}%"
        self.correctness._text_label.refresh()


class AddWords(Screen):
    def __init__(self, **kwargs):
        super(AddWords, self).__init__(**kwargs)
        self.words = dict()  # need to reset
        self.types = list()

    def get_types(self):
        if self.noun.active:
            self.types.append("noun")
        if self.verb.active:
            self.types.append("verb")
        if self.adj.active:
            self.types.append("adj")
        if self.adv.active:
            self.types.append("adv")
        if self.other_c.active:
            self.types.append(self.other.text.strip())

    def cleartxt(self):
        # clears the textinputs and checkboxes
        l = [self.word, self.mean1, self.mean2, self.mean3, self.mean4, self.mean5,
             self.syn1, self.syn2, self.syn3, self.sent, self.other]
        for i in l:
            i.text = ''

        c = [self.noun, self.verb, self.adj, self.adv, self.other_c]
        for i in c:
            i.active = False

        self.types = list()

    def confirm_pressed(self):
        # checks if all info is legal

        # if word exists
        if self.word.text in [i for i in js['WordList']]:
            popup = InputError('The word is already in\nyour word list')
            popup.open()
        # if text input is empty
        elif not (self.mean1.text and self.syn1.text and self.sent.text):
            popup = InputError(
                'Please fill in the blanks\nthat are not optional')
            popup.open()
        # if checkboxes is checked (at least 1)
        elif not(self.noun.active or self.verb.active or self.adj.active or
                 self.adv.active or self.other_c.active):
            popup = InputError('Please select the\ntype of the word')
            popup.open()
        # if word not in sentence
        elif self.word.text not in self.sent.text:
            popup = InputError('The word is not in\nthe sentence')
            popup.open()
        # if other checkbox is checked and the text input is empty
        elif self.other_c.active and self.other.text.strip() == '':
            popup = InputError("The 'other' box is empty")
            popup.open()
        else:
            # saves word
            meanings = [self.mean1.text, self.mean2.text, self.mean3.text, self.mean4.text, self.mean5.text]
            synonyms = [self.syn1.text, self.syn2.text, self.syn3.text]
            mean_list = []
            syn_list = []

            current_word = self.word.text # the current word

            for meaning in meanings:
                if meaning != '':
                    mean_list.append(meaning)

            for synonym in synonyms:
                if synonym != '':
                    syn_list.append(synonym)

            self.get_types()

            js['WordList'][current_word] = [mean_list,
                                              syn_list, [self.sent.text], self.types, 0, 0]

            self.cleartxt()
            popup = Notice('save', self)
            popup.open()

    def cancel_pressed(self):
        popup = Notice('cancel', self)
        popup.open()


class Play(Screen):
    correct_answers = 0
    total_answers = 0
    answer_correct = False
    _label = textLabel(text="{}%", font_size=45)

    def get_word(self):
        # dictionary of label -> checkbox
        self.labelToCheck = {self.ans1t: self.ans1, self.ans2t: self.ans2,
                             self.ans3t: self.ans3, self.ans4t: self.ans4}
        # list of labels
        answer_labels = [self.ans1t, self.ans2t, self.ans3t, self.ans4t]

        # ------------------------------- Reset ----------------------------------

        # sets label colors to black and enable the checkboxes
        for label in self.labelToCheck:
            label.color = (0, 0, 0, 1)
            label.text = ''  # do not delete this line
            self.labelToCheck[label].disabled = False


        # ---------------------------- Pick New Word -----------------------------
        word_list = list(js['WordList'].keys())

        # selects the correct word
        self.wordName = word_list[randint(0, len(word_list) - 1)]

        # index 5 is the total number of times answered
        self.correct_percentage.max = max(1, js['WordList'][self.wordName][5])
        # index 4 is the number of correct times answered
        self.correct_percentage.value = js['WordList'][self.wordName][4]

        # sets the main word label on the top
        self.word.text = self.wordName


        # puts mean, syn, sent, and type to lists in `others` except the current word (self.wordName)
        others = [[] for i in range(4)]
        for word in js['WordList']:  # loop through all the words
            if word != self.wordName:  # if word ≠ current word
                for i in range(4): # loop through the 4 types (mean, syn, sent, type)
                    others[i] += js['WordList'][word][i]


        # list of meanings for the current word
        meanings = js['WordList'][self.wordName][0]

        # the correct answer label for meaning
        self.correct_label = answer_labels[randint(0, 3)]
        # sets the text for the correct label, randomly select one from the list of meanings
        self.correct_label.text = meanings[randint(0, len(meanings) - 1)]
        # the corresponding checkbox
        self.correct_checkbox = self.labelToCheck[self.correct_label]

        # list of incorrect answers labels
        self.incorrect_labels = [
            i for i in answer_labels if i != self.correct_label]

        others[0] = list(set(others[0])) # remove repeats in `others`
        # others[0] is the list of meanings of other words (not the current one being tested on)

        # if the correct label text is in others, remove it
        for meaning in others[0]:
            if meaning in meanings: # if the meaning is in the list of meanings for the current word
                others[0].remove(meaning)
        
        # this guarentees that meanings will not be repeated
        # but this also means that the meaning count can be < 4, so we need to take care of that

        # set text to incorrect labels
        for i in range(3):
            if len(others[0]) <= 0: # if there are no meanings left, disable the checkbox
                self.incorrect_labels[i].text = 'N/A'
                self.labelToCheck[self.incorrect_labels[i]].disabled = True
            else: # otherwise, pop the current meaning out of `other`
                index = randint(0, len(others[0]) - 1)
                self.incorrect_labels[i].text = others[0].pop(index)

        # update CPB, labels about the current word
        self.update()

    def __init__(self, **kwargs):
        super(Play, self).__init__(**kwargs)
        # set everything up
        self.get_word()

    def update(self):
        # labels
        self.correct_num.text = "Answered correctly " + \
            str(js['WordList'][self.wordName][4]) + " time(s)"

        self.incorrect_num.text = "Answered incorrectly " + \
            str(js['WordList'][self.wordName][5] - js['WordList'][self.wordName][4]) \
                 + " time(s)"

        # CPBs
        self.correct_percentage.max = max(1, js['WordList'][self.wordName][5])
        self.correct_percentage.value = js['WordList'][self.wordName][4]

    def check(self, instance):
        # set checkboxes to disabled and color them
        instance.active = False
        instance.disabled = True

        # if the checkbox is correct
        if instance == self.correct_checkbox:
            self.correct_answers += 1
            self.total_answers += 1

            # add stats to js file
            js['WordList'][self.wordName][4] += 1
            js['WordList'][self.wordName][5] += 1

            # update CPBs and stats labels
            self.update()

            # set correct label to green, incorrect to red
            for i in self.labelToCheck.keys():
                if self.labelToCheck[i] == instance:
                    i.color = (0, 177/255, 106/255, 1)
                else:
                    i.color = (242/255, 38/255, 19/255, 1)

            # disable all incorrect labels
            for label in self.incorrect_labels:
                self.labelToCheck[label].disabled = True

            self.answer_correct = True
        else: # if checkbox is incorrect
            # update stats
            self.total_answers += 1
            js['WordList'][self.wordName][5] += 1
            self.update()
            for label in self.labelToCheck.keys():
                if self.labelToCheck[label] == instance:
                    label.color = (242/255, 38/255, 19/255, 1)
                    
            self.answer_correct = False

    def nextWord(self):
        # user can only go to the next question if they got it right
        if self.answer_correct:
            self.answer_correct = False
            self.get_word()


class ListWords(Screen):
    pass


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
            self.btn.bind(on_press=self.close)
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
            self.no.bind(on_press=self.close)

        self.content.add_widget(Label(text=text, pos_hint={"x": 0.15, "top": 0.95},
                                      size_hint=(0.7, 0.1)))
        self.title = 'Notice'
        self.size_hint = (0.5, 0.35)
        self.pos_hint = {"x": 0.25, "top": 0.75}

    def close(self, *args):
        self.dismiss()

    def press(self, *args):
        # clears text if cancel pressed
        self.widget.cleartxt()
        self.dismiss()


class LessonNumPopup(Popup):
    # popup for users to enter the lesson number to import words
    def __init__(self, my_widget, **kwargs):
        super(LessonNumPopup, self).__init__(**kwargs)
        self.my_widget = my_widget
        self.content = FloatLayout()
        self.content.add_widget(Label(text='Enter the lesson# :', pos_hint={"x": 0.15, "top": 0.95},
                                      size_hint=(0.7, 0.1)))
        self.input = TextInput(pos_hint={"x": 0.35, "top": 0.75}, size_hint=(
            0.3, 0.2), multiline=False, font_size=40)
        self.content.add_widget(self.input)
        self.save_btn = Button(pos_hint={"x": 0.3, "top": 0.3}, size_hint=(
            0.4, 0.25), text='Confirm', font_size=25)
        self.save_btn.bind(on_press=self.save)
        self.content.add_widget(self.save_btn)
        self.title = 'Choose Lesson'
        self.size_hint = (0.5, 0.35)
        self.pos_hint = {"x": 0.25, "top": 0.75}

    def save(self, *args):
        try:
            int(self.input.text)
        except ValueError: # do nothing if input isn't a numeric string
            None
        else:
            self.my_widget.lessonNum = int(self.input.text)
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
screen_manager.add_widget(Play(name="play"))
screen_manager.add_widget(AddWords(name="add_words"))
screen_manager.add_widget(ListWords(name="list_words"))


class Vocabulary_LearnerApp(App):
    def build(self):
        return screen_manager

    def on_start(self):
        Window.size = (350, 600) # resize window

        # remove logins past 1 week

        all_logins = js['Login info']['all logins'] # a list of all logins
        # all_logins is a reference

        today = time.localtime()[2]
        for i in range(len(all_logins) - 1, -1, -1):
            if all_logins[i][0][2] < today - 7: # past 7 days (1 week)
                all_logins.pop(-1)

        # switch to Main Screen, call update()
        screen_manager.get_screen('main_screen').update()
        screen_manager.current = 'main_screen'

    def on_stop(self):
        timelist = time.localtime()[:4]

        # get the answer data
        ans_correct = screen_manager.get_screen('play').correct_answers
        ans_all = screen_manager.get_screen('play').total_answers

        js["Login info"]["last login"] = [timelist, ans_correct, ans_all]
        js["Login info"]["all logins"].append([timelist, ans_correct, ans_all])

        # save score
        file = open('Vocabulary_Words.json', 'w')
        json.dump(js, file, indent=4)
        file.close()
        print('saved')


if __name__ == '__main__':
    Window.clearcolor = (179/255, 1, 1, 0)
    Vocabulary_LearnerApp().run()
