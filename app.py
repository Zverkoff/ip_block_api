from flask import Flask, request, jsonify
import ipaddress
import logging
import os
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Явно указываем stdout
    ]
)
logger = logging.getLogger(__name__)

logger.debug("Начало инициализации приложения")
try:
    app = Flask(__name__, static_folder='static')
    logger.debug("Flask инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации Flask: {e}")
    raise

# Отключаем Redis
USE_REDIS = False
redis_client = None
logger.debug("Redis отключен, используем локальное множество")

# Логируем порт
port = os.getenv('PORT', '5000')
logger.debug(f"Переменная окружения PORT: {port}")
logger.info(f"Приложение пытается запуститься на порту: {port}")

# Путь к файлу с черным списком
BLACKLIST_FILE = 'ip_blacklist.txt'

def load_blacklist():
    """Загружает IP-адреса из черного списка в множество."""
    logger.debug(f"Попытка загрузки файла: {BLACKLIST_FILE}")
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            ips = {ip.strip() for ip in f if ip.strip() and is_valid_ip(ip.strip())}
        logger.info(f"Загружено {len(ips)} IP-адресов в локальное множество")
        return ips
    except FileNotFoundError:
        logger.error(f"Файл {BLACKLIST_FILE} не найден")
        return set()
    except Exception as e:
        logger.error(f"Ошибка при загрузке черного списка: {e}")
        return set()

def is_valid_ip(ip):
    """Проверяет, является ли строка валидным IP-адресом."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

# Загружаем черный список
logger.debug("Начало загрузки черного списка")
try:
    blacklist = load_blacklist()
    logger.debug("Черный список загружен")
except Exception as e:
    logger.error(f"Ошибка при загрузке черного списка: {e}")
    raise

@app.route('/check-ip', methods=['GET'])
def check_ip():
    """API для проверки IP-адреса."""
    client_ip = request.args.get('ip')
    logger.debug(f"Запрос к /check-ip, IP: {client_ip}")
    if not client_ip or not is_valid_ip(client_ip):
        logger.warning(f"Неверный IP-адрес: {client_ip}")
        return jsonify({'error': 'Неверный IP-адрес'}), 400
    
    logger.info(f"Проверка IP: {client_ip}")
    is_blacklisted = client_ip in blacklist
    
    if is_blacklisted:
        logger.warning(f"IP {client_ip} в черном списке")
        return jsonify({'blocked': True}), 403
    else:
        logger.info(f"IP {client_ip} разрешен")
        return jsonify({'blocked': False}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка состояния API."""
    logger.debug("Запрос к /health получен")
    return jsonify({'status': 'ok'}), 200

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Раздача статических файлов (например, JavaScript)."""
    logger.debug(f"Запрос к статическому файлу: {filename}")
    return app.send_static_file(filename)

if __name__ == '__main__':
    logger.info(f"Запуск встроенного сервера Flask на порту {port}")
    try:
        app.run(host='0.0.0.0', port=int(port))
    except Exception as e:
        logger.error(f"Ошибка при запуске Flask: {e}")
        raise
