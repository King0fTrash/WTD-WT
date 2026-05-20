Originally fork of [BLK-to-JSON](https://github.com/REFORDER/BLK-to-JSON)

<h1 align="center">WTD ⇄ WT Converter</h1>

<p align="center">
  <b>Универсальный конвертер, способный преобразовывать файлы прицелов из формата <code>.blk</code> в <code>.json</code> для WTDraw, а также собирать <code>.json</code> обратно в готовые для War Thunder файлы <code>.blk</code></b>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python"></a>
  <img src="https://img.shields.io/badge/Platform-Windows-blue?logo=windows&logoColor=white" alt="Platform">
</p>

---

## Ключевые особенности

<h3 align="center">Графический интерфейс и Drag-and-Drop</h3>
<p align="center">
  <img src="https://i.ibb.co/xSW0bbwC/2026-05-20-183548.png" width="750" alt="Интерфейс">
</p>
<p align="center">Программа обладает интуитивным интерфейсом. Функция <b>Drag-and-Drop</b> позволяет удобнее обрабатывать файлы, просто перетащив их мышкой прямо в окно приложения</p>

---

<h3 align="center">Предпросмотр прицела</h3>
<p align="center">
  <img src="https://i.ibb.co/xSPv8638/image.png" width="750" alt="Предпросмотр">
</p>
<p align="center">При конвертации <code>.blk ⇄ .json</code> на встроенном холсте автоматически отображается примитивная интерактивная миниатюра-предпросмотр геометрии самого прицела</p>

> [!WARNING]
> Существуют небольшие проблемы с отображением квадратов на холсте предпросмотра

---

<h3 align="center">Настройки и шаблоны BLK</h3>
<p align="center">
  <img src="https://i.ibb.co/6J0BDkQs/2026-05-20-183716.png" width="750" alt="Настройка">
</p>
<p align="center">Утилита имеет встроенный текстовый редактор конфигураций. Вы можете изменять настройки выходящего BLK-файла, которая автоматически применится при сборке из <code>.json</code> в оригинальный <code>.blk</code>.</p>

---

## Быстрая инструкция

| Входной файл | Действие | Результат |
| :--- | :---: | :--- |
| **Прицел игры (`.blk`)** | Перетащить в окно | Создает чистый `.json` для конструктора WTDraw с **сохранением русской кириллицы**. |
| **Файл конструктора (`.json`)** | Перетащить в окно | Создает файл `_packed.blk` с готовой шапкой настроек для папки `UserSights`. |

> [!NOTE]
Для запуска исходного кода вам крайне желательно установить Python версии 3.8 или выше.
