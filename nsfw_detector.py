import tkinter as tk
from tkinter import scrolledtext
import os
import argparse
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models


def preprocess_image(image_path):

    """
        Предобработка изображения перед подачей его на вход модели
        :param image_path: Путь к изображению
        :return: Тензор изображения после предобработки
        """

    img = Image.open(image_path).convert('RGB') # преобразование в RGB
    preprocess = transforms.Compose([ #Создание последовательности преобразований
        transforms.Resize(256), # Изменение размера изображения до 256x256
        transforms.CenterCrop(224), # Центральное обрезание изображения до 224x224
        transforms.ToTensor(), # Преобразование изображения в тензор
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), # Нормализация значений пикселей
    ])
    img_tensor = preprocess(img) # Применение преобразований к изображению
    return img_tensor.unsqueeze(0) # Добавление размерности батча и возврат тензора


def detect_nsfw(image_path, models):
    img_tensor = preprocess_image(image_path) # Предобработка изображения
    nsfw_scores = []
    for model in models:
        model.eval() # Установка режима оценки
        with torch.no_grad(): # Отключение расчета градиентов
            outputs = model(img_tensor) # Применение модели к изображению
        nsfw_scores.append(torch.sigmoid(outputs[0]).tolist()) # Преобразование выходных данных и добавление в список
    return nsfw_scores # Возврат списка вероятностей NSFW-контента


def is_image_safe(nsfw_scores, threshold):
    for score in nsfw_scores:
        if score[0] > threshold: # Проверка превышения пороговой вероятности
            return False
    return True # Возврат True, если все вероятности ниже порога


def main(model_names, threshold):
    root = tk.Tk() # Создание главного окна Tkinter
    root.title("Проверка") # Установка заголовка окна

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=20) # Создание текстового поля с прокруткой
    text_area.pack(expand=True, fill='both') # Размещение текстового поля в окне

    image_folder = "images" # Папка для безопасных изображений
    unacceptable_folder = "unacceptable" # Папка для изображений с контентом NSFW
    nsfw_count = 0 # Счетчик изображений с контентом NSFW

    if not os.path.exists(unacceptable_folder): # Проверка наличия папки
        os.makedirs(unacceptable_folder) # Создание папки, если не существует

    loaded_models = [] # Список загруженных моделей
    for model_name in model_names:
        if model_name == 'resnet50':
            loaded_models.append(models.resnet50(pretrained=True))
        elif model_name == 'densenet121':
            loaded_models.append(models.densenet121(pretrained=True))
        else:
            text_area.insert(tk.END, f"Неподдерживаемое название модели: {model_name}\n")

    for image_file in os.listdir(unacceptable_folder):
        try:
            image_path = os.path.join(unacceptable_folder, image_file)
            nsfw_scores = detect_nsfw(image_path, loaded_models)
            nsfw_probabilities = [score[0] for score in nsfw_scores]
            text_area.insert(tk.END, f"Вероятности для {image_file}: {', '.join(map(str, nsfw_probabilities))}\n")
            safe = is_image_safe(nsfw_scores, threshold)
            if safe:
                os.rename(image_path, os.path.join(image_folder, image_file))
                text_area.insert(tk.END, f"{image_file} был перемещен обратно в папку изображения.\n")
        except Exception as e:
            text_area.insert(tk.END, f"Ошибка перемещения изображения {image_file}: {e}\n")

    for image_file in os.listdir(image_folder):
        try:
            image_path = os.path.join(image_folder, image_file) # Путь к изображению
            nsfw_scores = detect_nsfw(image_path, loaded_models) # Обнаружение NSFW-контента на изображении
            nsfw_probabilities = [score[0] for score in nsfw_scores] # Список вероятностей NSFW-контента
            text_area.insert(tk.END, f"Вероятности деструктивности для {image_file}: {', '.join(map(str, nsfw_probabilities))}\n") # Вывод результатов в текстовое поле
            safe = is_image_safe(nsfw_scores, threshold)
            if safe:
                text_area.insert(tk.END, f"{image_file} безопасен для просмотра.\n")
            else:
                text_area.insert(tk.END, f"{image_file} содержит деструктивный контент и небезопасен для просмотра.\n")
                os.rename(image_path, os.path.join(unacceptable_folder, image_file))
                nsfw_count += 1
        except Exception as e:
            text_area.insert(tk.END, f"Ошибка перемещения изображения {image_file}: {e}\n")

    text_area.insert(tk.END, f"Найдено {nsfw_count} изображений содержащих деструктивный контент и небезопасных для просмотра.\n")

    root.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs='+', default=['resnet50', 'densenet121'],
                        help="Выбор модели: resnet50, densenet121")
    parser.add_argument("--threshold", type=float, default=0.60,
                        help="Пороговая вероятность для содержимого NSFW для класса NSFW")
    args = parser.parse_args()

    main(args.models, args.threshold)
