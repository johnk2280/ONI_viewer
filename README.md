#### Цель - изучить фреймворки PyQT, OpenCV, OpenNI2.

В проигрывателе на начальном этапе реализуются следующие возможности:
- открывать .oni файлы через стандартный диалог открытия файла;
- выводить на экран получаемые из файла карты глубин и цветных изображений;
- ставить на паузу и возобновлять воспроизведение;
-  переключаться на произвольный кадр с помощью ползунка;
- покадровая перемотка на один кадр вперед/назад в режиме паузы.

В данном репозитории доступны 2 реализации проигрывателя:
- в папке player_loop_version реализация через класс QThread (запуск цикла while в рабочем потоке отдельно от основного);
- в папке player_timer_version реализация через класс Qtimer.
