# BOB Glove Portal Farmer V1 #vibecode

Languages: [English](#english) | [Русский](#русский) | [Українська](#українська)

Tutorial: https://www.youtube.com/watch?v=NB7P3Ffu-2E

---

<a name="english"></a>
## English

A Python script that automatically finds the bright orange portal in Slap Battles (Halloween event), walks to it, enters it, presses E and resets the character. It is built for farming the BOB glove.

### How it works

1. Captures the screen at about 30 FPS.
2. Finds the orange portal by colour (HSV mask plus shape filters, so other orange objects are ignored).
3. Turns the camera with the mouse so the portal is in the centre of the screen and walks to it with W.
4. When you are inside (the orange disappears because of the teleport), waits 0.1 s and presses E.
5. Waits 0.6 s and resets the character (Esc, R, Enter), then starts searching again.

If no portal is visible, the script spins the camera to look for it. If nothing is found for 8 seconds, it presses E and resets.

### Requirements

- Windows (the script uses the Windows API)
- Python 3.9 or newer
- Roblox in windowed or borderless mode, on your primary monitor
- First-person view (zoom the camera all the way in with the mouse wheel)

### Installation

```
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
```

### Usage

1. Join the game and stand in front of the portal area. Make sure the camera is in first person.
2. Run the script:
   ```
   python bob_farm.py
   ```
3. You have 5 seconds to click into the Roblox window.
4. Do not touch the mouse while the script is running.

### Controls

| Key | Action |
|-----|--------|
| F8  | Stop the script |
| -   | Close the debug window (it is pinned on top and has no close button) |

### Debug window

Shows what the script sees:

- Green rectangle: confirmed portal. Yellow rectangle: candidate, not confirmed yet.
- Red vertical line: centre of the screen.
- Grey rectangle: ignored zone (HUD icons).
- Small picture in the bottom-right corner: the colour mask (white means "counts as orange").
- `or=` is the share of the screen that is portal-orange.

### Settings

All settings are at the top of `bob_farm.py`.

| Setting | Default | Description |
|---------|---------|-------------|
| `HSV_LOW`, `HSV_HIGH` | (12,170,200), (26,255,255) | Portal colour range in HSV |
| `IGNORE_ZONES` | top-right corner | Screen zones to ignore, as fractions of the screen |
| `MOUSE_SIGN` | 1 | Set to -1 if the camera turns the wrong way |
| `MOUSE_GAIN` | 500 | Camera turn speed (higher is faster) |
| `E_DELAY` | 0.1 | Seconds to wait after entering the portal before pressing E |
| `RESET_DELAY` | 0.6 | Seconds to wait after pressing E before resetting |
| `RESPAWN_WAIT` | 4.0 | Pause after the reset before searching again |
| `KEY_HOLD` | 0.06 | How long each key is held (increase if E is sometimes missed) |
| `SEARCH_TIMEOUT` | 8.0 | Seconds without a portal before E and reset |
| `PROC_WIDTH` | 640 | Processing width (lower it if FPS is low) |
| `DEBUG` | True | Show the debug window |

### Troubleshooting

- **Camera turns the wrong way:** set `MOUSE_SIGN = -1`.
- **Camera overshoots or shakes:** lower `MOUSE_GAIN`. If it turns too slowly, raise it.
- **Portal is not detected:** look at the mask in the debug window and widen `HSV_LOW` and `HSV_HIGH`.
- **Script follows another orange object:** add its position to `IGNORE_ZONES` or tighten `MIN_SOLIDITY` and `AR_MIN` / `AR_MAX`.
- **E is sometimes missed:** increase `KEY_HOLD` to 0.1.
- **Low FPS:** lower `PROC_WIDTH` to 480.
- **Screen capture is black:** Roblox must not be in exclusive fullscreen. Use windowed or borderless mode.
- **Keys do nothing in the game:** run the terminal as Administrator, especially if Roblox runs as Administrator.

### Disclaimer

This project is for educational purposes. Automating gameplay may violate the Roblox Terms of Use and can lead to an account ban. Use it at your own risk. The author is not responsible for any consequences.

---

<a name="русский"></a>
## Русский

Python-скрипт, который автоматически находит ярко-оранжевый портал в Slap Battles (событие Halloween), идёт к нему, заходит, нажимает E и делает ресет персонажа. Сделан для фарма перчатки BOB.

### Как это работает

1. Захватывает экран примерно в 30 FPS.
2. Находит оранжевый портал по цвету (маска HSV плюс фильтры формы, поэтому остальные оранжевые объекты игнорируются).
3. Поворачивает камеру мышью так, чтобы портал был по центру экрана, и идёт к нему на W.
4. Когда вы внутри (оранжевое пропадает из-за телепорта), ждёт 0.1 сек и нажимает E.
5. Ждёт 0.6 сек и делает ресет персонажа (Esc, R, Enter), после чего снова ищет портал.

Если портала на экране нет, скрипт крутит камеру и ищет его. Если за 8 секунд ничего не найдено, нажимает E и делает ресет.

### Требования

- Windows (скрипт использует Windows API)
- Python 3.9 или новее
- Roblox в оконном режиме или в окне без рамки, на основном мониторе
- Вид от первого лица (максимально приблизьте камеру колёсиком мыши)

### Установка

```
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
```

### Использование

1. Зайдите в игру и встаньте у зоны с порталом. Камера должна быть от первого лица.
2. Запустите скрипт:
   ```
   python bob_farm.py
   ```
3. У вас есть 5 секунд, чтобы кликнуть в окно Roblox.
4. Не трогайте мышь, пока скрипт работает.

### Управление

| Клавиша | Действие |
|---------|----------|
| F8      | Остановить скрипт |
| -       | Закрыть окно debug (оно закреплено поверх всех окон и не имеет крестика) |

### Окно debug

Показывает, что видит скрипт:

- Зелёная рамка: подтверждённый портал. Жёлтая рамка: кандидат, ещё не подтверждён.
- Красная вертикальная линия: центр экрана.
- Серая рамка: игнорируемая зона (иконки интерфейса).
- Маленькая картинка в правом нижнем углу: цветовая маска (белое считается оранжевым).
- `or=` это доля экрана, занятая оранжевым цветом портала.

### Настройки

Все настройки находятся в начале файла `bob_farm.py`.

| Настройка | По умолчанию | Описание |
|-----------|--------------|----------|
| `HSV_LOW`, `HSV_HIGH` | (12,170,200), (26,255,255) | Диапазон цвета портала в HSV |
| `IGNORE_ZONES` | правый верхний угол | Зоны экрана, которые игнорируются (в долях экрана) |
| `MOUSE_SIGN` | 1 | Поставьте -1, если камера крутится не в ту сторону |
| `MOUSE_GAIN` | 500 | Скорость поворота камеры (больше значит быстрее) |
| `E_DELAY` | 0.1 | Сколько секунд ждать после входа в портал перед нажатием E |
| `RESET_DELAY` | 0.6 | Сколько секунд ждать после E перед ресетом |
| `RESPAWN_WAIT` | 4.0 | Пауза после ресета перед новым поиском |
| `KEY_HOLD` | 0.06 | Сколько держать клавишу (увеличьте, если E иногда не срабатывает) |
| `SEARCH_TIMEOUT` | 8.0 | Секунд без портала до нажатия E и ресета |
| `PROC_WIDTH` | 640 | Ширина кадра для обработки (уменьшите, если низкий FPS) |
| `DEBUG` | True | Показывать окно debug |

### Решение проблем

- **Камера крутится не в ту сторону:** поставьте `MOUSE_SIGN = -1`.
- **Камера перелетает или трясётся:** уменьшите `MOUSE_GAIN`. Если поворачивает слишком медленно, увеличьте.
- **Портал не находится:** посмотрите маску в окне debug и расширьте `HSV_LOW` и `HSV_HIGH`.
- **Скрипт идёт к другому оранжевому объекту:** добавьте его место в `IGNORE_ZONES` или ужесточите `MIN_SOLIDITY` и `AR_MIN` / `AR_MAX`.
- **E иногда не срабатывает:** увеличьте `KEY_HOLD` до 0.1.
- **Низкий FPS:** уменьшите `PROC_WIDTH` до 480.
- **Захват экрана чёрный:** Roblox не должен быть в эксклюзивном полноэкранном режиме. Используйте оконный режим или окно без рамки.
- **Клавиши в игре не нажимаются:** запустите терминал от имени администратора, особенно если Roblox запущен от администратора.

### Отказ от ответственности

Проект создан в образовательных целях. Автоматизация игрового процесса может нарушать Условия использования Roblox и привести к блокировке аккаунта. Используйте на свой страх и риск. Автор не несёт ответственности за любые последствия.

---

<a name="українська"></a>
## Українська

Python-скрипт, який автоматично знаходить яскраво-помаранчевий портал у Slap Battles (подія Halloween), іде до нього, заходить, натискає E і робить ресет персонажа. Створений для фарму рукавички BOB.

### Як це працює

1. Захоплює екран приблизно на 30 FPS.
2. Знаходить помаранчевий портал за кольором (маска HSV плюс фільтри форми, тому інші помаранчеві об'єкти ігноруються).
3. Повертає камеру мишею так, щоб портал був по центру екрана, і йде до нього на W.
4. Коли ви всередині (помаранчевий зникає через телепорт), чекає 0.1 сек і натискає E.
5. Чекає 0.6 сек і робить ресет персонажа (Esc, R, Enter), після чого знову шукає портал.

Якщо порталу на екрані немає, скрипт крутить камеру і шукає його. Якщо за 8 секунд нічого не знайдено, натискає E і робить ресет.

### Вимоги

- Windows (скрипт використовує Windows API)
- Python 3.9 або новіший
- Roblox у віконному режимі або у вікні без рамки, на основному моніторі
- Вигляд від першої особи (максимально наблизьте камеру коліщатком миші)

### Встановлення

```
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
```

### Використання

1. Зайдіть у гру та станьте біля зони з порталом. Камера має бути від першої особи.
2. Запустіть скрипт:
   ```
   python bob_farm.py
   ```
3. У вас є 5 секунд, щоб клікнути у вікно Roblox.
4. Не чіпайте мишу, поки скрипт працює.

### Керування

| Клавіша | Дія |
|---------|-----|
| F8      | Зупинити скрипт |
| -       | Закрити вікно debug (воно закріплене поверх усіх вікон і не має хрестика) |

### Вікно debug

Показує, що бачить скрипт:

- Зелена рамка: підтверджений портал. Жовта рамка: кандидат, ще не підтверджений.
- Червона вертикальна лінія: центр екрана.
- Сіра рамка: ігнорована зона (іконки інтерфейсу).
- Маленька картинка в правому нижньому куті: кольорова маска (біле вважається помаранчевим).
- `or=` це частка екрана, зайнята помаранчевим кольором порталу.

### Налаштування

Усі налаштування знаходяться на початку файлу `bob_farm.py`.

| Налаштування | За замовчуванням | Опис |
|--------------|------------------|------|
| `HSV_LOW`, `HSV_HIGH` | (12,170,200), (26,255,255) | Діапазон кольору порталу в HSV |
| `IGNORE_ZONES` | правий верхній кут | Зони екрана, які ігноруються (у частках екрана) |
| `MOUSE_SIGN` | 1 | Поставте -1, якщо камера крутиться не в той бік |
| `MOUSE_GAIN` | 500 | Швидкість повороту камери (більше означає швидше) |
| `E_DELAY` | 0.1 | Скільки секунд чекати після входу в портал перед натисканням E |
| `RESET_DELAY` | 0.6 | Скільки секунд чекати після E перед ресетом |
| `RESPAWN_WAIT` | 4.0 | Пауза після ресету перед новим пошуком |
| `KEY_HOLD` | 0.06 | Скільки тримати клавішу (збільште, якщо E іноді не спрацьовує) |
| `SEARCH_TIMEOUT` | 8.0 | Секунд без порталу до натискання E і ресету |
| `PROC_WIDTH` | 640 | Ширина кадру для обробки (зменште, якщо низький FPS) |
| `DEBUG` | True | Показувати вікно debug |

### Вирішення проблем

- **Камера крутиться не в той бік:** поставте `MOUSE_SIGN = -1`.
- **Камера перелітає або трясеться:** зменште `MOUSE_GAIN`. Якщо повертає надто повільно, збільште.
- **Портал не знаходиться:** подивіться маску у вікні debug і розширте `HSV_LOW` та `HSV_HIGH`.
- **Скрипт іде до іншого помаранчевого об'єкта:** додайте його місце в `IGNORE_ZONES` або посильте `MIN_SOLIDITY` та `AR_MIN` / `AR_MAX`.
- **E іноді не спрацьовує:** збільште `KEY_HOLD` до 0.1.
- **Низький FPS:** зменште `PROC_WIDTH` до 480.
- **Захоплення екрана чорне:** Roblox не повинен бути в ексклюзивному повноекранному режимі. Використовуйте віконний режим або вікно без рамки.
- **Клавіші в грі не натискаються:** запустіть термінал від імені адміністратора, особливо якщо Roblox запущений від адміністратора.

### Застереження

Проєкт створений в освітніх цілях. Автоматизація ігрового процесу може порушувати Умови використання Roblox і призвести до блокування акаунта. Використовуйте на свій ризик. Автор не несе відповідальності за будь-які наслідки.
