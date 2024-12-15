import multiprocessing
import os
from PIL import Image
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor


class MandelbrotGenerator:
    def __init__(self, width: int, height: int, max_iter: int = 1000):
        self.width = width  # Высота изображения
        self.height = height  # Ширина изображения
        self.max_iter = max_iter  # Кол-во итераций
        self.x_min, self.x_max = -1.0, 1.0  # Ограничения по х
        self.y_min, self.y_max = -1.5, 1.5  # Ограничения по у

    def get_complex_coordinates(self, point: tuple) -> complex:
        x, y = point
        real = self.x_min + (x / self.width) * (self.x_max - self.x_min)  # Вещественная часть
        imag = self.y_min + (y / self.height) * (self.y_max - self.y_min)  # Мнимая часть
        return complex(real, imag)

    def compute_pixel(self, c: int) -> int:
        z = 0  # начальное значение
        for n in range(self.max_iter):  # Перебираем все итерации
            if abs(z) > 2:  # Проверка на расходимость
                return n
            z = z * z + c  # формула Мандельброта
        return self.max_iter

    def generate_mandelbrot_sequential(self) -> Image:

        """Генерация фрактала Мандельброта в последовательном режиме."""

        image = Image.new("RGB", (self.width, self.height))  # Создается новое изображение

        # Двойной цикл для прохода по каждому пикселю изображения
        for x in range(self.width):
            for y in range(self.height):
                c = self.get_complex_coordinates(
                    (x, y))  # Преобразуем координаты пикселя в соответствующее комплексное число

                value = self.compute_pixel(
                    c)  # определяем, сколько итераций требуется, чтобы понять, принадлежит ли точка множеству Мандельброта

                color = self.get_color(value)  # задает цвет точки
                image.putpixel((x, y), color)  # располагает точку на плоскости
        return image

    def generate_mandelbrot_parallel(self, num_processes=None) -> Image:

        """Генерация фрактала Мандельброта на процессах."""

        if num_processes is None:  # Если кол-во процессов не задано
            num_processes = multiprocessing.cpu_count()  # Используем все доступные

        with multiprocessing.Pool(processes=num_processes) as pool:
            # Создание списка всех координат пикселей
            points = [(x, y) for x in range(self.width) for y in range(self.height)]

            # Преобразование координат пикселей в комплексные координаты
            # с использованием параллельной обработки
            complex_coords = pool.map(self.get_complex_coordinates, points)

            # Вычисление значений пикселей для каждой комплексной координаты
            # также с использованием параллельной обработки
            pixel_values = pool.map(self.compute_pixel, complex_coords)

            # Преобразование значений пикселей в цвета
            colors = list(map(self.get_color, pixel_values))

        # Создание нового изображения
        image = Image.new("RGB", (self.width, self.height))

        # Объединение координат пикселей и их цветов
        pixels = list(zip(points, colors))

        # Установка цвета для каждого пикселя
        for (x, y), color in pixels:
            image.putpixel((x, y), color)
        return image

    def generate_mandelbrot_threads(self, num_threads=None) -> Image:
        """Генерация фрактала Мандельброта на потоках (Задание для самостоятельной практики)"""

        if num_threads is None:
            num_threads = 4

        with ThreadPoolExecutor(max_workers=num_threads) as pool:

            points = [(x, y) for x in range(self.width) for y in range(self.height)]

            complex_coords = pool.map(self.get_complex_coordinates, points)

            pixel_values = pool.map(self.compute_pixel, complex_coords)

            colors = list(map(self.get_color, pixel_values))

        image = Image.new("RGB", (self.width, self.height))

        pixels = list(zip(points, colors))

        for (x, y), color in pixels:
            image.putpixel((x, y), color)
        return image

    def get_color(self, value: int) -> tuple:
        """Определяет цвет пикселя на основе значения итерации."""
        if value == self.max_iter:
            return (0, 0, 0)  # черный для точек внутри множества
        # градиент для точек вне множества (можно настроить цветовой градиент)
        scaled_value = int((value / self.max_iter) * 255)
        return (scaled_value, 0, 255 - scaled_value)


if __name__ == "__main__":
    width = 800  # ширина
    height = 600  # высота
    max_iter = 1000  # кол-во итераций

    generator = MandelbrotGenerator(width, height, max_iter)

    # Последовательная генерация
    start_time = perf_counter()  # время начала
    sequential_image = generator.generate_mandelbrot_sequential()
    end_time = perf_counter()  # время завершения
    print(f"Фрактал Мандельброта (последовательный), время выполения: {end_time - start_time}")

    # Параллельная генерация на процессах
    num_processes = [2, 4, 8, 16]  # Варианты процессов (в моем случае макс 16)
    for num_process in num_processes:  # Перебираем кол-во процессов
        start_time = perf_counter()  # время начала
        parallel_image = generator.generate_mandelbrot_parallel(num_process)
        end_time = perf_counter()  # время завершения
        print(f"Фрактал Мандельброта (параллельный, {num_process} процессов), время выполения: {end_time - start_time}")

    # Потоки
    num_thread = os.cpu_count()
    start_time = perf_counter()
    parallel_image = generator.generate_mandelbrot_parallel(num_thread)
    end_time = perf_counter()
    parallel_image.save('Фрактал_Мандельброта.png')
    print(f"Фрактал Мандельброта (параллельный, {num_thread} потоков), время выполения: {end_time - start_time}")