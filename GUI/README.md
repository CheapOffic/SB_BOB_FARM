# BOB Farm - GUI version

Languages: [English](#english) | [Русский](#русский) | [Українська](#українська)

---

<a name="english"></a>
## English

This folder contains the version of the BOB glove portal farmer (Slap Battles, Halloween event) that has a graphical window. You do not have to edit any code: every setting is changed in the window and saved automatically.

### What is in this folder

| File | Description |
|------|-------------|
| `bob_farm_gui.py` | The program itself. Run this file. |
| `bob_farm_config.json` | Your settings. It is created automatically next to the script on the first run and updated every time you save. You do not need to create it. |

### What the program does

1. Captures the Roblox window and finds the bright orange portal by colour.
2. While the portal is not visible, the character jumps and slowly turns the camera until the portal appears.
3. When the portal is found, jumping stops and the character walks straight to it.
4. After entering the portal, it waits 0.1 s, presses E, waits 0.6 s and resets the character (Esc, R, Enter), then starts again.

All delays and thresholds can be changed in the window.

### Features

- All settings are editable in the window (about 40 fields with a short description under each one). Invalid values are highlighted in red.
- Settings are stored in `bob_farm_config.json` and loaded on the next start.
- Two languages: English (default) and Russian. The choice is saved too.
- A "Requirements" tab shows the recommended hardware (system, Python, processor, RAM, graphics card, screen) and detects the specs of your own PC.
- A live preview inside the window shows what the script sees.
- The same pinned debug window as in the console version (always on top, no close button, closed with the "-" key).
- Start and Stop buttons, plus the F8 hotkey to stop.

### Requirements

- Windows 10 or 11 (64-bit)
- Python 3.9 or newer with tkinter (it is included in the standard Python installer for Windows)
- Roblox in windowed or borderless mode, first-person view (zoom the camera all the way in)

The "Requirements" tab inside the program lists the recommended hardware.

### Installation

```
pip install mss opencv-python numpy pydirectinput
```

If the repository has a `requirements.txt`, you can use `pip install -r requirements.txt` instead.

### Usage

1. Open the game and make sure the camera is in first person.
2. Run the program:
   ```
   python bob_farm_gui.py
   ```
3. Check the settings if you want to change anything, then press "Save settings".
4. Press "Start". Roblox is brought to the front automatically and the farm starts after 5 seconds. If nothing happens, click into the game window.
5. Do not touch the mouse while the farm is running.

### Hotkeys

| Key | Action |
|-----|--------|
| F8  | Stop the farm (works while Roblox is focused) |
| -   | Close the debug window (works while Roblox is focused) |

### Settings groups

- **Capture & performance:** FPS, processing width, capture of the Roblox window only, preview and debug window.
- **Portal detection:** colour range (HSV), size and shape filters, red-glove protection, ignored zones.
- **Camera & movement:** camera speed and direction, dead zone, walking angle.
- **Searching & jumping:** jumping and turning while searching, jump interval, search timeout.
- **Entering the portal & reset:** E delay, reset delay, respawn wait, key hold time.

To restore the defaults press "Reset to defaults" and then "Save settings", or delete `bob_farm_config.json`.

### Troubleshooting

- **The character only jumps in place:** make sure "Turn while searching" is on (the "Search: ..." line of the log shows the current state). If the settings came from an old version, press "Reset to defaults" and save.
- **The portal is not detected:** open the debug window and look at the colour mask in the bottom-right corner. Widen the hue, saturation and brightness ranges in "Portal detection".
- **The camera turns the wrong way:** set "Camera direction" to -1.
- **The camera overshoots or shakes:** lower "Camera gain".
- **E is sometimes missed:** increase "Key hold (s)" to 0.1.
- **Low FPS:** lower "Target FPS" or "Processing width".
- **"Roblox window not found" in the log:** the program then captures the whole monitor. The Roblox window title must be exactly "Roblox"; do not minimize it.
- **The window does not open:** install tkinter (reinstall Python and tick "tcl/tk and IDLE") and check the packages from the Installation section.
- **Keys do nothing in the game:** run the terminal as Administrator, especially if Roblox runs as Administrator.

### Disclaimer

This project is for educational purposes. Automating gameplay may violate the Roblox Terms of Use and can lead to an account ban. Use it at your own risk. The author is not responsible for any consequences.

---

<a name="русский"></a>
## Русский

В этой папке лежит версия автофарма портала для перчатки BOB (Slap Battles, событие Halloween) с графическим окном. Код редактировать не нужно: все настройки меняются в окне и сохраняются автоматически.

### Что лежит в папке

| Файл | Описание |
|------|----------|
| `bob_farm_gui.py` | Сама программа. Запускай этот файл. |
| `bob_farm_config.json` | Твои настройки. Создаётся автоматически рядом со скриптом при первом запуске и обновляется при каждом сохранении. Создавать его вручную не нужно. |

### Что делает программа

1. Захватывает окно Roblox и находит яркий оранжевый портал по цвету.
2. Пока портала не видно, персонаж прыгает и медленно крутит камеру, пока портал не появится.
3. Когда портал найден, прыжки прекращаются, и персонаж идёт к нему прямо.
4. После входа в портал ждёт 0.1 сек, нажимает E, ждёт 0.6 сек и делает ресет персонажа (Esc, R, Enter), после чего начинает заново.

Все задержки и пороги можно менять в окне.

### Возможности

- Все настройки редактируются в окне (около 40 полей, под каждым короткое описание). Неверные значения подсвечиваются красным.
- Настройки хранятся в `bob_farm_config.json` и подгружаются при следующем запуске.
- Два языка: английский (по умолчанию) и русский. Выбор тоже сохраняется.
- Вкладка «Требования» показывает рекомендуемое железо (система, Python, процессор, ОЗУ, видеокарта, экран) и определяет характеристики твоего ПК.
- Живое превью в окне показывает, что видит скрипт.
- Такое же закреплённое окно debug, как в консольной версии (всегда поверх окон, без крестика, закрывается клавишей «-»).
- Кнопки «Старт» и «Стоп», а также горячая клавиша F8 для остановки.

### Требования

- Windows 10 или 11 (64-бит)
- Python 3.9 или новее с tkinter (он входит в стандартный установщик Python для Windows)
- Roblox в оконном режиме или в окне без рамки, вид от первого лица (максимально приблизь камеру)

Рекомендуемое железо перечислено на вкладке «Требования» внутри программы.

### Установка

```
pip install mss opencv-python numpy pydirectinput
```

Если в репозитории есть `requirements.txt`, можно вместо этого использовать `pip install -r requirements.txt`.

### Использование

1. Зайди в игру и убедись, что камера от первого лица.
2. Запусти программу:
   ```
   python bob_farm_gui.py
   ```
3. Если хочешь что-то изменить, поправь настройки и нажми «Сохранить настройки».
4. Нажми «Старт». Roblox автоматически выводится на передний план, и фарм начинается через 5 секунд. Если ничего не происходит, кликни в окно игры.
5. Не трогай мышь, пока фарм работает.

### Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| F8      | Остановить фарм (работает, когда активен Roblox) |
| -       | Закрыть окно debug (работает, когда активен Roblox) |

### Группы настроек

- **Захват и производительность:** FPS, ширина обработки, захват только окна Roblox, превью и окно debug.
- **Детект портала:** диапазон цвета (HSV), фильтры размера и формы, защита от красной перчатки, игнорируемые зоны.
- **Камера и движение:** скорость и направление камеры, мёртвая зона, угол для ходьбы.
- **Поиск и прыжки:** прыжки и вращение при поиске, интервал прыжков, тайм-аут поиска.
- **Вход в портал и ресет:** задержка E, задержка ресета, ожидание респавна, время удержания клавиши.

Чтобы вернуть значения по умолчанию, нажми «Сбросить по умолчанию» и затем «Сохранить настройки» либо удали файл `bob_farm_config.json`.

### Решение проблем

- **Персонаж только прыгает на месте:** убедись, что включено «Вращаться при поиске» (текущее состояние показано в строке журнала «Поиск: ...»). Если настройки остались от старой версии, нажми «Сбросить по умолчанию» и сохрани.
- **Портал не находится:** открой окно debug и посмотри цветовую маску в правом нижнем углу. Расширь диапазоны оттенка, насыщенности и яркости в разделе «Детект портала».
- **Камера крутится не в ту сторону:** поставь «Направление камеры» в -1.
- **Камера перелетает или трясётся:** уменьши «Сила поворота камеры».
- **E иногда не срабатывает:** увеличь «Удержание клавиши (с)» до 0.1.
- **Низкий FPS:** уменьши «Целевой FPS» или «Ширину обработки».
- **В журнале «Окно Roblox не найдено»:** тогда программа захватывает весь монитор. Заголовок окна Roblox должен быть именно «Roblox», не сворачивай его.
- **Окно не открывается:** установи tkinter (переустанови Python с галочкой «tcl/tk and IDLE») и проверь пакеты из раздела «Установка».
- **Клавиши в игре не нажимаются:** запусти терминал от имени администратора, особенно если Roblox запущен от администратора.

### Отказ от ответственности

Проект создан в образовательных целях. Автоматизация игрового процесса может нарушать Условия использования Roblox и привести к блокировке аккаунта. Используй на свой страх и риск. Автор не несёт ответственности за любые последствия.

---

<a name="українська"></a>
## Українська

У цій папці лежить версія автофарму порталу для рукавички BOB (Slap Battles, подія Halloween) з графічним вікном. Код редагувати не потрібно: усі налаштування змінюються у вікні й зберігаються автоматично.

### Що лежить у папці

| Файл | Опис |
|------|------|
| `bob_farm_gui.py` | Сама програма. Запускай цей файл. |
| `bob_farm_config.json` | Твої налаштування. Створюється автоматично поруч зі скриптом під час першого запуску й оновлюється при кожному збереженні. Створювати його вручну не потрібно. |

### Що робить програма

1. Захоплює вікно Roblox і знаходить яскравий помаранчевий портал за кольором.
2. Поки порталу не видно, персонаж стрибає й повільно крутить камеру, доки портал не з'явиться.
3. Коли портал знайдено, стрибки припиняються, і персонаж іде до нього прямо.
4. Після входу в портал чекає 0.1 сек, натискає E, чекає 0.6 сек і робить ресет персонажа (Esc, R, Enter), після чого починає знову.

Усі затримки й пороги можна змінювати у вікні.

Увага: інтерфейс програми поки що має лише англійську та російську мови (українського перекладу немає), тому назви кнопок, вкладок і полів нижче наведено англійською, так, як вони виглядають у програмі.

### Можливості

- Усі налаштування редагуються у вікні (близько 40 полів, під кожним короткий опис). Неправильні значення підсвічуються червоним.
- Налаштування зберігаються в `bob_farm_config.json` і підвантажуються під час наступного запуску.
- Дві мови інтерфейсу: англійська (за замовчуванням) і російська. Вибір теж зберігається.
- Вкладка «Requirements» показує рекомендоване залізо (система, Python, процесор, ОЗП, відеокарта, екран) і визначає характеристики твого ПК.
- Живе прев'ю у вікні показує, що бачить скрипт.
- Таке саме закріплене вікно debug, як у консольній версії (завжди поверх вікон, без хрестика, закривається клавішею «-»).
- Кнопки «Start» і «Stop», а також гаряча клавіша F8 для зупинки.

### Вимоги

- Windows 10 або 11 (64-біт)
- Python 3.9 або новіший з tkinter (він входить у стандартний інсталятор Python для Windows)
- Roblox у віконному режимі або у вікні без рамки, вигляд від першої особи (максимально наблизь камеру)

Рекомендоване залізо перелічене на вкладці «Requirements» всередині програми.

### Встановлення

```
pip install mss opencv-python numpy pydirectinput
```

Якщо в репозиторії є `requirements.txt`, можна замість цього використати `pip install -r requirements.txt`.

### Використання

1. Зайди в гру й переконайся, що камера від першої особи.
2. Запусти програму:
   ```
   python bob_farm_gui.py
   ```
3. Якщо хочеш щось змінити, поправ налаштування й натисни «Save settings».
4. Натисни «Start». Roblox автоматично виводиться на передній план, і фарм починається через 5 секунд. Якщо нічого не відбувається, клацни у вікно гри.
5. Не чіпай мишу, поки фарм працює.

### Гарячі клавіші

| Клавіша | Дія |
|---------|-----|
| F8      | Зупинити фарм (працює, коли активний Roblox) |
| -       | Закрити вікно debug (працює, коли активний Roblox) |

### Групи налаштувань

- **Захоплення та продуктивність:** FPS, ширина обробки, захоплення лише вікна Roblox, прев'ю та вікно debug.
- **Детект порталу:** діапазон кольору (HSV), фільтри розміру й форми, захист від червоної рукавички, ігноровані зони.
- **Камера та рух:** швидкість і напрямок камери, мертва зона, кут для ходьби.
- **Пошук і стрибки:** стрибки та обертання під час пошуку, інтервал стрибків, тайм-аут пошуку.
- **Вхід у портал і ресет:** затримка E, затримка ресету, очікування респавну, час утримання клавіші.

Щоб повернути значення за замовчуванням, натисни «Reset to defaults» і потім «Save settings» або видали файл `bob_farm_config.json`.

### Вирішення проблем

- **Персонаж лише стрибає на місці:** переконайся, що ввімкнено «Turn while searching» (поточний стан показано в рядку журналу «Search: ...» або «Поиск: ...»). Якщо налаштування залишилися від старої версії, натисни «Reset to defaults» і збережи.
- **Портал не знаходиться:** відкрий вікно debug і подивися кольорову маску в правому нижньому куті. Розшир діапазони відтінку, насиченості й яскравості (Hue, Saturation, Brightness) у розділі «Portal detection».
- **Камера крутиться не в той бік:** постав «Camera direction» на -1.
- **Камера перелітає або трясеться:** зменш «Camera gain».
- **E іноді не спрацьовує:** збільш «Key hold (s)» до 0.1.
- **Низький FPS:** зменш «Target FPS» або «Processing width (px)».
- **У журналі «Вікно Roblox не знайдено»:** тоді програма захоплює весь монітор. Заголовок вікна Roblox має бути саме «Roblox», не згортай його.
- **Вікно не відкривається:** встанови tkinter (перевстанови Python з галочкою «tcl/tk and IDLE») і перевір пакети з розділу «Встановлення».
- **Клавіші в грі не натискаються:** запусти термінал від імені адміністратора, особливо якщо Roblox запущений від адміністратора.

### Застереження

Проєкт створений в освітніх цілях. Автоматизація ігрового процесу може порушувати Умови використання Roblox і призвести до блокування акаунта. Використовуй на свій ризик. Автор не несе відповідальності за будь-які наслідки.
