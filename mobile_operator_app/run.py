import argparse
import subprocess
import sys
import time
import os

# python run.py main - застосунок + бд
# python run.py test - тести + бд
# python run.py install - завантажити залежності


# --- Налаштування команд Docker ---
CMDS = {
    "up": "docker-compose up -d",
    "stop": "docker-compose stop",
    "down": "docker-compose down",
    "wipe": "docker-compose down -v",
    "check": "docker-compose ps"
}


def run_command(command, allow_fail=False):
    """Виконує команду в терміналі."""
    print(f" Виконую: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f" Помилка при виконанні: {command}")
        if not allow_fail:
            sys.exit(1)
    except KeyboardInterrupt:
        pass


def manage_db(action):
    """Виконує дії з базою даних."""
    if action in CMDS:
        run_command(CMDS[action])
    else:
        print(f" Невідома команда БД: {action}")


def install_requirements():
    """Встановлює бібліотеки з requirements.txt"""
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f" Файл {req_file} не знайдено!")
        return

    print(" Встановлення бібліотек Python...")
    run_command(f"{sys.executable} -m pip install -r {req_file}")
    print(" Бібліотеки успішно встановлено!")


def main():
    parser = argparse.ArgumentParser(description="Менеджер запуску Mobile Operator App")
    parser.add_argument(
        'mode',
        choices=['install', 'main', 'test', 'stop', 'wipe', 'check', 'down'],
        help="Режим: install (бібліотеки), main (додаток), test (тести) або керування БД"
    )
    args = parser.parse_args()
    python_cmd = sys.executable

    try:

        if args.mode == 'install':
            install_requirements()


        elif args.mode in ['main', 'test']:
            print(f" Ініціалізація середовища для режиму: {args.mode.upper()}...")

            # 1. Запускаємо бази даних
            manage_db("up")

            # 2. Чекаємо трохи
            print(" Очікування ініціалізації БД (3 сек)...")
            time.sleep(3)

            # 3. Виконуємо задачу
            if args.mode == 'main':
                print(" Запуск Streamlit...")
                run_command(f"{python_cmd} -m streamlit run main.py")

            elif args.mode == 'test':
                print(" Запуск Pytest...")
                run_command(f"{python_cmd} -m pytest tests -v -s")

        # --- Режими обслуговування ---
        elif args.mode == 'stop':
            print(" Зупинка контейнерів...")
            manage_db("stop")

        elif args.mode == 'wipe':
            print(" ПОВНЕ очищення...")
            manage_db("wipe")

        elif args.mode == 'check':
            manage_db("check")

        elif args.mode == 'down':
            print(" Зупинка контейнерів...")
            manage_db("down")

    except KeyboardInterrupt:
        print("\n\n Отримано сигнал зупинки (Ctrl+C).")

    finally:
        if args.mode in ['main', 'test']:
            print(" Автоматична зупинка баз даних...")
            manage_db("stop")
            print(" Роботу завершено.")


if __name__ == "__main__":
    main()