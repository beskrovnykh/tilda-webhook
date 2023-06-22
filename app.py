import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from chalice import Chalice, Response
import logging
import json

app = Chalice(app_name='tilda-webhook')
app.log.setLevel(logging.INFO)

SES_CLIENT = boto3.client('ses', region_name='ap-southeast-2')
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

# Загрузка данных о продуктах из JSON-файла
with open('chalicelib/products.json', 'r') as f:
    product_data = json.load(f)


@app.route('/webhook', methods=['POST'])
def webhook():
    request = app.current_request
    webhook_body = request.json_body
    app.log.info(json.dumps(webhook_body))  # Логируем все параметры POST-запроса

    # Получаем данные из запроса
    email = webhook_body.get('email')
    products = webhook_body.get('payment', {}).get('products', [])

    # Отправляем письмо для каждого продукта
    for product in products:
        product_id = product.get('externalid')

        # Находим информацию о продукте в наших данных
        for data in product_data['products']:
            if data['product_id'] == product_id:
                email_subject = data['email_subject']
                email_body = data['email_body']
                break
        else:
            app.log.error(f"Не найден продукт с ID {product_id}")
            continue

        # Отправляем письмо
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = email_subject
            msg.attach(MIMEText(email_body, 'plain'))

            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USERNAME, email, text)
            server.quit()

        except Exception as error:
            app.log.error(f"Ошибка при отправке письма: {error}")
            return Response(body='Ошибка при отправке письма', status_code=500)

    return Response(body='OK', status_code=200)
#
