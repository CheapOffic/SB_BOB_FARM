# BOB Farm — GUI

**BOB Farm V1.5.6** is the graphical version of the BOB Farm project. The application brings its options, status, reports, and statistics together in one desktop interface.

## What's new in V1.5.6

- Expanded statistics and reporting sections.
- Statistics categories for daily, weekly, current-session, application-session, and lifetime summaries.
- Separate tracking for application runtime and an individual farm session.
- Persistent statistics storage intended to keep accumulated data across restarts.
- More detailed Reports output.
- Expanded Telegram report information and language synchronization with the selected UI language.
- Improved settings organization and configuration handling.
- Localization updates for English and Russian, plus updated Ukrainian README documentation.
- General interface, data-handling, and stability improvements.

## Languages

The README is available in:
- English
- Русский
- Українська

## Files

| File | Description |
|---|---|
| `bob_farm_gui.py` | Main GUI application entry point. |
| `bob_farm_config.json` | User configuration file; created/updated by the application when supported. |
| `requirements.txt` | Python package dependencies, if included in the repository. |


## Requirements

- Windows 10 or Windows 11, 64-bit
- Python 3.9+ (with Tkinter available)
- Packages listed in `requirements.txt`, if provided

## Installation

1. Install Python and ensure it is available from your terminal (`python --version`).
2. Open a terminal in this folder.
3. Install dependencies:

   ```cmd
   pip install -r requirements.txt
   ```

   If no `requirements.txt` is present, install the packages listed by the project maintainers.

## Launch

Run the GUI entry point from a terminal in the project directory:

```cmd
python bob_farm_gui.py
```

## Configuration and data

Application settings and statistics may be stored locally in configuration/data files. Keep a backup of these files before replacing the application or troubleshooting saved settings.

## Disclaimer

This project is provided for educational purposes. Automated gameplay may violate a game's rules or terms of service and could result in account penalties. Use the project responsibly and at your own risk.


---

# Русский

**BOB Farm V1.5.6** — графическая версия проекта BOB Farm. В приложении собраны настройки, состояние программы, отчёты и статистика.

## Что нового в V1.5.6

- Расширены разделы статистики и отчётов.
- Добавлены категории статистики: за день, неделю, текущую сессию, сессию работы приложения и всё время.
- Время работы приложения и отдельной сессии отслеживается раздельно.
- Добавлено постоянное хранение статистики, рассчитанное на сохранение накопленных данных между перезапусками.
- Отчёты стали подробнее.
- Telegram-отчёты дополнены данными, а язык сообщений синхронизируется с языком интерфейса.
- Улучшена организация настроек и работа с конфигурацией.
- Обновлена локализация: английский и русский интерфейсы, а также документация на украинском.
- Общие улучшения интерфейса, обработки данных и стабильности.

## Языки

README доступен на английском, русском и украинском языках.


## Файлы

| Файл | Описание |
|---|---|
| `bob_farm_gui.py` | Основной файл запуска GUI. |
| `bob_farm_config.json` | Файл настроек; создаётся/обновляется приложением, если это предусмотрено. |
| `requirements.txt` | Список Python-зависимостей, если он присутствует в репозитории. |


## Требования

- Windows 10 или Windows 11, 64-bit
- Python 3.9+ (с доступным Tkinter)
- Python-пакеты из `requirements.txt`, если файл есть в репозитории

## Установка

1. Установи Python и проверь, что он доступен в терминале (`python --version`).
2. Открой терминал в этой папке.
3. Установи зависимости:

   ```cmd
   pip install -r requirements.txt
   ```

   Если `requirements.txt` отсутствует, установи пакеты, указанные разработчиками проекта.

## Запуск

В терминале, открытом в папке проекта, выполни:


```cmd
python bob_farm_gui.py
```

## Настройки и данные

Настройки и статистика могут храниться локально в конфигурационных файлах. Перед заменой программы или диагностикой сохранённых настроек рекомендуется сделать резервную копию этих файлов.

## Отказ от ответственности

Проект предоставляется в образовательных целях. Автоматизация игрового процесса может нарушать правила игры или условия использования и привести к санкциям аккаунта. Используй проект ответственно и на свой риск.


---

# Українська

**BOB Farm V1.5.6** — графічна версія проєкту BOB Farm. У програмі зібрані налаштування, стан застосунку, звіти та статистика.

## Що нового у V1.5.6

- Розширено розділи статистики та звітів.
- Додано категорії статистики: за день, тиждень, поточну сесію, сесію роботи застосунку та за весь час.
- Час роботи застосунку й окремої сесії відстежується незалежно.
- Додано постійне збереження статистики, призначене для збереження накопичених даних між перезапусками.
- Звіти стали докладнішими.
- Telegram-звіти доповнено даними, а мова повідомлень синхронізується з мовою інтерфейсу.
- Покращено організацію налаштувань і роботу з конфігурацією.
- Оновлено локалізацію: англійську та російську, а також українську документацію.
- Загальні покращення інтерфейсу, обробки даних і стабільності.

## Мови

README доступний англійською, російською та українською.


## Файли

| Файл | Опис |
|---|---|
| `bob_farm_gui.py` | Основний файл запуску GUI. |
| `bob_farm_config.json` | Файл налаштувань; створюється/оновлюється програмою, якщо це передбачено. |
| `requirements.txt` | Список Python-залежностей, якщо він є в репозиторії. |


## Вимоги

- Windows 10 або Windows 11, 64-bit
- Python 3.9+ (із доступним Tkinter)
- Python-пакети з `requirements.txt`, якщо файл є в репозиторії

## Встановлення

1. Встанови Python і переконайся, що він доступний у терміналі (`python --version`).
2. Відкрий термінал у цій папці.
3. Встанови залежності:

   ```cmd
   pip install -r requirements.txt
   ```

   Якщо `requirements.txt` відсутній, встанови пакети, зазначені розробниками проєкту.

## Запуск

У терміналі, відкритому в папці проєкту, виконай:


```cmd
python bob_farm_gui.py
```

## Налаштування та дані

Налаштування й статистика можуть зберігатися локально у конфігураційних файлах. Перед заміною програми або діагностикою збережених налаштувань рекомендується зробити резервну копію цих файлів.

## Застереження

Проєкт надається з освітньою метою. Автоматизація ігрового процесу може порушувати правила гри або умови використання й призвести до санкцій щодо акаунта. Використовуй проєкт відповідально та на власний ризик.
