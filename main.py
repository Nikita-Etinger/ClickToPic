import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import time
import os
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import keyboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save.txt")

class AutomationApp:
    def __init__(self, master):
        self.master = master
        self.master.title("GetEmployersReportFromControlCam")
        self.master.attributes("-topmost", True)

        tk.Label(master, text="Текст автоввода на 2 типе:").pack()
        self.month_entry = tk.Entry(master)
        self.month_entry.pack()

        tk.Label(master, text="Введите задержку через запятую (пример: 1,2,3,4):").pack()
        self.delay_entry = tk.Entry(master)
        self.delay_entry.pack()

        tk.Label(master, text="Введите типы этапов (пример: 0,0,1,2):").pack()
        self.stage_entry = tk.Entry(master)
        self.stage_entry.pack()

        tk.Label(master, text="Кол-во повторов (0 - бесконечно):").pack()
        self.loop_count_entry = tk.Entry(master)
        self.loop_count_entry.pack()

        self.status_label = tk.Label(master, text="Статус: ожидание запуска")
        self.status_label.pack()

        self.pin_var = tk.IntVar(value=1)
        self.pin_check = tk.Checkbutton(master, text="Закрепить поверх всех окон", variable=self.pin_var, command=self.toggle_pin)
        self.pin_check.pack()

        self.loop_var = tk.IntVar()
        self.loop_check = tk.Checkbutton(master, text="Работать в цикле", variable=self.loop_var)
        self.loop_check.pack()

        self.start_button = tk.Button(master, text="Старт", command=self.start_sequence)
        self.start_button.pack()

        self.exit_button = tk.Button(master, text="Выход", command=self.exit_app)
        self.exit_button.pack()

        tk.Label(master, text="LAlt+LShift - остановка").pack()

        self.images = []
        self.delays = []
        self.stages = []
        self.current_index = 0
        self.running = False
        self.loop_limit = 0
        self.loop_counter = 0

        self.load_saved_inputs()
        self.running = False
        self.stop_hotkey_thread = False
        self.hotkey_thread = Thread(target=self.check_hotkey, daemon=True)
        self.hotkey_thread.start()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def check_hotkey(self):
        while not self.stop_hotkey_thread:
            if keyboard.is_pressed("left alt") and keyboard.is_pressed("left shift"):
                self.running = False
                self.update_status("Остановлено пользователем")
                break
            time.sleep(0.1)

    def on_close(self):
        self.running = False
        self.stop_hotkey_thread = True
        self.master.destroy()

    def toggle_pin(self):
        self.master.attributes("-topmost", bool(self.pin_var.get()))

    def update_status(self, text):
        self.status_label.config(text=f"Статус: {text}")

    def find_and_click(self, image_name, confidence=0.9):
        image_path = os.path.join(BASE_DIR, "Pictures", image_name)
        screen = np.array(ImageGrab.grab())
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Шаблон {image_name} не найден по пути: {image_path}")
            return False

        w, h = template.shape[::-1]
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= confidence)

        for pt in zip(*loc[::-1]):
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2
            pyautogui.moveTo(center_x, center_y, duration=0.2)
            pyautogui.click()
            print(f"Нажато по координатам: {center_x}, {center_y}")
            return True

        print("Элемент не найден.")
        return False

    def save_inputs(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            f.write(self.month_entry.get() + "\n")
            f.write(self.delay_entry.get() + "\n")
            f.write(self.stage_entry.get() + "\n")
            f.write(self.loop_count_entry.get() + "\n")

    def load_saved_inputs(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                if len(lines) >= 4:
                    self.month_entry.insert(0, lines[0])
                    self.delay_entry.insert(0, lines[1])
                    self.stage_entry.insert(0, lines[2])
                    self.loop_count_entry.insert(0, lines[3])

    def check_hotkey(self):
        while True:
            if keyboard.is_pressed("left alt") and keyboard.is_pressed("left shift"):
                self.running = False
                self.update_status("Остановлено пользователем")
                break
            time.sleep(0.1)

    def start_sequence(self):
        try:
            month = int(self.month_entry.get())
            if not 1 <= month <= 12:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число от 1 до 12")
            return

        try:
            self.delays = list(map(int, self.delay_entry.get().split(",")))
            self.stages = list(map(int, self.stage_entry.get().split(",")))
            if len(self.delays) != len(self.stages):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Убедитесь, что задержки и этапы указаны корректно и совпадают по количеству")
            return

        try:
            self.loop_limit = int(self.loop_count_entry.get())
        except ValueError:
            self.loop_limit = 0

        self.save_inputs()
        self.images = [f"{i+1}.png" for i in range(len(self.delays))]
        self.current_index = 0
        self.loop_counter = 0
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        Thread(target=self.run_sequence).start()

    def continue_sequence(self):
        self.start_button.config(text="Старт", command=self.start_sequence, state=tk.DISABLED)
        Thread(target=self.run_sequence).start()

    def exit_app(self):
        self.running = False
        self.stop_hotkey_thread = True
        self.master.after(100, self.master.destroy)
    def run_sequence(self):
        while self.running:
            while self.current_index < len(self.images):
                image = self.images[self.current_index]
                step = self.current_index + 1
                self.update_status(f"этап {step}/{len(self.images)}: {image}")

                if not self.find_and_click(image):
                    self.update_status("ошибка — остановка")
                    self.running = False
                    return

                stage_type = self.stages[self.current_index]

                if stage_type == 1:
                    self.update_status("выберите данные вручную")
                    self.start_button.config(text="Продолжить", command=self.continue_sequence, state=tk.NORMAL)
                    self.current_index += 1
                    return

                elif stage_type == 2:
                    text_to_type = self.month_entry.get()
                    pyautogui.write(text_to_type, interval=0.1)
                    print(f"Введено: {text_to_type}")
                    time.sleep(1)
                else:
                    time.sleep(self.delays[self.current_index])

                self.current_index += 1

            self.loop_counter += 1
            if self.loop_var.get() and (self.loop_limit == 0 or self.loop_counter < self.loop_limit):
                self.current_index = 0
                continue
            else:
                break

        self.update_status("завершено")
        self.start_button.config(state=tk.NORMAL)
        self.current_index = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()