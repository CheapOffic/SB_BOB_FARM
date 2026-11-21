# BOB Farm — V1.5.6

**A desktop GUI project with configurable settings, session tracking, reports, and multilingual interface support.**

Languages: [English](#english) | [Русский](#русский) | [Українська](#українська)

---

<a name="english"></a>
## English

### Overview

BOB Farm is a Windows desktop application with a graphical interface and configurable preferences. This README describes the V1.5.6 release and the project's main areas. Feature descriptions reflect the release notes; individual features may depend on the current build.


### V1.5.6 — What's new

- **Statistics:** expanded statistics views for daily, weekly, current-session, application-session, and lifetime summaries.
- **Session tracking:** application uptime and activity-session duration are tracked separately to make summaries clearer.
- **Persistence:** statistics are designed to carry over between launches rather than being limited to one run.
- **Reports:** the Reports area provides a more structured overview of accumulated and session information.
- **Telegram integration:** report messages include additional summary information and follow the selected application language.
- **Settings:** settings organization and synchronization have been improved; supported changes can be applied without restarting.
- **Localization:** English and Russian text coverage and consistency have been improved.
- **Reliability:** general internal cleanup and error-handling improvements.

### Highlights

- Graphical desktop interface
- Editable preferences with saved configuration
- English and Russian interface options
- Reports and summary views
- Separate application and session tracking
- Persistent statistics
- Telegram report support
- Hardware/system information page
- Preview and diagnostic views, where available in the build

### Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.9+ (if running from source)
- Tkinter-enabled Python installation
- Dependencies listed in `requirements.txt`

### Installation

Install the project's Python dependencies from the repository folder:

```bash
python -m pip install -r requirements.txt
```

### Running from source

```bash
python bob_farm_gui.py
```

The exact entry-point filename may differ between repository builds. Use the file included in your checkout.

### Configuration and data

- User preferences are stored locally in the application's configuration file.
- Configuration files are created or updated by the application as applicable.
- Statistics storage is intended to persist across application launches in V1.5.x.
- Back up configuration and statistics files before replacing or updating a build.

### Languages

- English
- Russian

Ukrainian README translation is included below; the application's Ukrainian interface is not confirmed to be available in this release.

### Disclaimer

This is an independent project. Automated interaction with third-party games or services may violate their rules and can lead to account restrictions. Review the relevant terms and use software responsibly. This repository is not affiliated with Roblox or Slap Battles.


---

<a name="русский"></a>
## Русский

### О проекте

BOB Farm — десктопное приложение для Windows с графическим интерфейсом и настраиваемыми параметрами. Этот README описывает версию V1.5.6 и основные части проекта. Описание возможностей основано на заметках к обновлению; доступность отдельных функций зависит от конкретной сборки.


### V1.5.6 — Что нового

- **Статистика:** расширены сводки за день, неделю, текущую сессию, запуск приложения и всё время.
- **Отслеживание сессий:** время работы приложения и длительность отдельной сессии учитываются независимо.
- **Сохранение данных:** статистика рассчитана на сохранение между запусками, а не только на один сеанс.
- **Отчёты:** раздел Reports стал более структурированным и содержит больше информации о сессиях и накопленных результатах.
- **Telegram:** в сообщения добавлена дополнительная сводная информация; язык сообщений синхронизируется с языком приложения.
- **Настройки:** улучшена организация настроек и их синхронизация; поддерживаемые изменения можно применять без перезапуска.
- **Локализация:** улучшены полнота и согласованность английского и русского текстов.
- **Надёжность:** проведены внутренние улучшения и доработана обработка ошибок.

### Основные возможности

- Графический интерфейс
- Настраиваемые параметры с сохранением
- Английский и русский языки интерфейса
- Отчёты и статистические сводки
- Раздельный учёт времени приложения и сессии
- Сохраняемая статистика
- Отправка отчётов через Telegram
- Раздел с информацией о системе и оборудовании
- Превью и диагностические окна, если они доступны в сборке

### Требования

- Windows 10 или Windows 11 (64-бит)
- Python 3.9+ (при запуске из исходников)
- Python с Tkinter
- Зависимости из `requirements.txt`

### Установка

Установи Python-зависимости из папки репозитория:


```bash
python -m pip install -r requirements.txt
```

### Запуск из исходников

```bash
python bob_farm_gui.py
```

Имя главного файла может отличаться в разных сборках. Используй файл, который находится в твоей версии репозитория.

### Настройки и данные

- Пользовательские настройки сохраняются локально в конфигурационном файле приложения.
- Файлы настроек создаются или обновляются программой, когда это необходимо.
- В V1.5.x статистика рассчитана на сохранение между запусками.
- Перед заменой или обновлением сборки рекомендуется сделать резервную копию конфигурации и файлов статистики.

### Языки

- English
- Русский

Перевод README на украинский добавлен ниже; наличие украинского языка в интерфейсе этой версии не подтверждено.

### Отказ от ответственности

Это независимый проект. Автоматизированное взаимодействие с сторонними играми или сервисами может нарушать их правила и привести к ограничениям аккаунта. Ознакомься с соответствующими условиями и используй программы ответственно. Репозиторий не связан с Roblox или Slap Battles.


---

<a name="українська"></a>
## Українська

### Про проєкт

BOB Farm — десктопна програма для Windows із графічним інтерфейсом та налаштовуваними параметрами. Цей README описує версію V1.5.6 та основні частини проєкту. Опис можливостей базується на нотатках до оновлення; наявність окремих функцій залежить від конкретної збірки.


### V1.5.6 — Що нового

- **Статистика:** розширено зведення за день, тиждень, поточну сесію, запуск програми та весь час.
- **Облік сесій:** час роботи програми та тривалість окремої сесії обліковуються незалежно.
- **Збереження даних:** статистика має зберігатися між запусками, а не лише протягом одного сеансу.
- **Звіти:** розділ Reports став структурованішим і містить більше даних про сесії та накопичені результати.
- **Telegram:** повідомлення містять додаткову зведену інформацію; мова повідомлень синхронізується з мовою програми.
- **Налаштування:** покращено організацію параметрів та їх синхронізацію; підтримувані зміни можна застосовувати без перезапуску.
- **Локалізація:** покращено повноту й узгодженість англійських та російських текстів.
- **Надійність:** виконано внутрішні покращення та доопрацьовано обробку помилок.

### Основні можливості

- Графічний інтерфейс
- Налаштовувані параметри зі збереженням
- Англійська та російська мови інтерфейсу
- Звіти та статистичні зведення
- Окремий облік часу програми та сесії
- Статистика зі збереженням
- Надсилання звітів через Telegram
- Розділ з інформацією про систему та обладнання
- Попередній перегляд і діагностичні вікна, якщо вони доступні у збірці

### Вимоги

- Windows 10 або Windows 11 (64-біт)
- Python 3.9+ (для запуску з вихідного коду)
- Python із Tkinter
- Залежності з `requirements.txt`

### Встановлення

Встанови залежності Python у папці репозиторію:

```bash
python -m pip install -r requirements.txt
```

### Запуск із вихідного коду

```bash
python bob_farm_gui.py
```

Назва головного файлу може відрізнятися в різних збірках. Використовуй файл, що входить до твоєї версії репозиторію.

### Налаштування та дані

- Налаштування користувача зберігаються локально у конфігураційному файлі програми.
- Файли конфігурації створюються або оновлюються програмою за потреби.
- У V1.5.x статистика розрахована на збереження між запусками.
- Перед заміною або оновленням збірки рекомендується зробити резервну копію конфігурації та файлів статистики.

### Мови

- English
- Русский

Український переклад README додано, але наявність української мови в інтерфейсі цієї версії не підтверджена.

### Відмова від відповідальності

Це незалежний проєкт. Автоматизована взаємодія зі сторонніми іграми або сервісами може порушувати їхні правила та призвести до обмежень акаунта. Ознайомся з відповідними умовами та використовуй програмне забезпечення відповідально. Репозиторій не пов'язаний із Roblox або Slap Battles.
