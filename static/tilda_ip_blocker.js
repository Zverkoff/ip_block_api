async function blockFraudulentIPs() {
         try {
             // Получаем IP клиента через ipify
             const response = await fetch('https://api.ipify.org?format=json');
             const data = await response.json();
             const clientIP = data.ip;
             console.log('IP клиента:', clientIP);

             // Проверяем IP через API (замените на ваш URL после деплоя)
             const apiResponse = await fetch('https://YOUR_API_URL/check-ip?ip=' + encodeURIComponent(clientIP));
             const result = await apiResponse.json();

             if (result.blocked) {
                 console.log('IP заблокирован:', clientIP);
                 // Скрываем рекламный блок (замените 'ad-block' на ID вашего рекламного блока)
                 const adBlock = document.getElementById('ad-block');
                 if (adBlock) {
                     adBlock.style.display = 'none';
                 }
                 // Или перенаправляем пользователя
                 // window.location.href = 'https://example.com/blocked';
             } else {
                 console.log('IP разрешен:', clientIP);
             }
         } catch (error) {
             console.error('Ошибка при проверке IP:', error);
         }
     }

     document.addEventListener('DOMContentLoaded', blockFraudulentIPs);