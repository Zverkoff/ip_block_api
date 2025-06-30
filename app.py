from flask import Flask, request, jsonify
     import ipaddress
     import logging
     import redis
     import os

     # Настройка логирования
     logging.basicConfig(
         level=logging.INFO,
         format='%(asctime)s [%%(levelname)s] %%(message)s',
         handlers=[
             logging.FileHandler('ip_block_api.log', encoding='utf-8'),
             logging.StreamHandler()
         ]
     )
     logger = logging.getLogger(__name__)

     app = Flask(__name__, static_folder='static')

     # Подключение к Redis
     try:
         redis_client = redis.Redis(
             host=os.getenv('REDIS_HOST', 'localhost'),
             port=int(os.getenv('REDIS_PORT', 6379)),
             db=0,
             decode_responses=True
         )
         redis_client.ping()
         USE_REDIS = True
         logger.info("Подключение к Redis успешно")
     except Exception as e:
         logger.warning(f"Не удалось подключиться к Redis: {e}. Используем локальное множество.")
         USE_REDIS = False

     # Путь к файлу с черным списком
     BLACKLIST_FILE = 'ip_blacklist.txt'

     def load_blacklist():
         """Загружает IP-адреса из черного списка в Redis или множество."""
         try:
             with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                 ips = {ip.strip() for ip in f if ip.strip() and is_valid_ip(ip.strip())}
             
             if USE_REDIS:
                 redis_client.flushdb()
                 for ip in ips:
                     redis_client.set(ip, 1)
                 logger.info(f"Загружено {len(ips)} IP-адресов в Redis")
             else:
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

     # Загружаем черный список при старте
     blacklist = load_blacklist()

     @app.route('/check-ip', methods=['GET'])
     def check_ip():
         """API для проверки IP-адреса."""
         client_ip = request.args.get('ip')
         if not client_ip or not is_valid_ip(client_ip):
             return jsonify({'error': 'Неверный IP-адрес'}), 400
         
         logger.info(f"Проверка IP: {client_ip}")
         
         is_blacklisted = (redis_client.exists(client_ip) if USE_REDIS else client_ip in blacklist)
         
         if is_blacklisted:
             logger.warning(f"IP {client_ip} в черном списке")
             return jsonify({'blocked': True}), 403
         else:
             logger.info(f"IP {client_ip} разрешен")
             return jsonify({'blocked': False}), 200

     @app.route('/health', methods=['GET'])
     def health_check():
         """Проверка состояния API."""
         return jsonify({'status': 'ok'}), 200

     @app.route('/static/<path:filename>')
     def serve_static(filename):
         """Раздача статических файлов (например, JavaScript)."""
         return app.send_static_file(filename)

     if __name__ == '__main__':
         app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))