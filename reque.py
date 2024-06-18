import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import sys
import argparse
import urllib.parse
import torch
import torchvision.transforms as transforms
import torchvision.models as models

# Извлечение изображений
def extract_images(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        img_tags = soup.find_all('img')
        image_urls = []
        for img in img_tags:
            if 'src' in img.attrs:
                image_urls.append(img['src'])
    return image_urls

# Скачивание изображений
def download_image(image_url, folder, log):
    log.insert(tk.END, f"Скачивание изображения: {image_url}\n")
    response = requests.get(image_url)
    extension = response.headers.get('content-type').split('/')[-1]
    supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    if extension.lower() not in supported_formats:
        log.insert(tk.END, f"Изображение {image_url} имеет неподдерживаемый формат\n")
        return None
    filename = ''.join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in os.path.basename(image_url))
    filename = f"{filename}.{extension}"
    filepath = os.path.join(folder, filename)
    img = Image.open(BytesIO(response.content))
    if img.mode == 'P' and 'transparency' in img.info:
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')
    img.save(filepath)
    log.insert(tk.END, f"Сохранено в: {filepath}\n")
    log.update()  # Обновление содержимого виджета
    return filepath

# Функция вызова extract_images и download_image
def process_images(html_file, output_folder, log):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем путь к исполняемому файлу
    images_dir = os.path.join(current_dir, "images")
    os.makedirs(images_dir, exist_ok=True)  # Создаем папку для изображений
    image_urls = extract_images(html_file)
    downloaded_images = []
    for url in image_urls:
        try:
            filepath = download_image(url, images_dir, log)  # Сохраняем изображения в папку images
            if filepath:
                downloaded_images.append(filepath)
        except Exception as e:
            log.insert(tk.END, f"Ошибка при скачивании изображения {url}: {e}\n")
            log.update()  # Обновление содержимого виджета
    messagebox.showinfo("Готово", f"Скачано {len(downloaded_images)} изображений.")

# Функция обработки при нажатии "Открыть файл"
def open_file(log):
    html_file = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    if html_file:
        output_folder = os.path.join(os.path.dirname(html_file), "images")
        log.insert(tk.END, f"Открыт файл: {html_file}\n")
        log.update()  # Обновление содержимого виджета
        process_images(html_file, output_folder, log)

# Функция обработки при нажатии "Начать проверку NSFW"
def run_nsfw_detector(log):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем путь к текущему скрипту
    nsfw_detector_path = os.path.join(current_dir, 'nsfw_detector.py')
    subprocess.run(['python', nsfw_detector_path], cwd=current_dir)  # Указываем текущую директорию
    # После выполнения nsfw_detector, мы будем обрабатывать результаты и выводить их на графический интерфейс
    display_nsfw_results(log)

# Функция для отображения результатов обнаружения NSFW-контента
def display_nsfw_results(log):

    log.insert(tk.END, "Результаты проверки:\n")
    log.update()  # Обновление виджета для отображения результатов



root = tk.Tk()
root.title("Извлечение изображений из HTML файла")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Выберите HTML файл:")
label.grid(row=0, column=0, sticky="w")

log = scrolledtext.ScrolledText(frame, width=70, height=20)  # Размеры окошек
log.grid(row=1, columnspan=2)

button_open = tk.Button(frame, text="Открыть файл", command=lambda: open_file(log))
button_open.grid(row=0, column=1, padx=5)

button_check = tk.Button(frame, text="Начать проверку", command=lambda: run_nsfw_detector(log))
button_check.grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
