#!/usr/bin/python3

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from wikipedia import PageError, DisambiguationError, WikipediaException, wikipedia
import wikipediaapi
import requests
import unicodedata

from datetime import date
import time
import smtplib
import config
from email.mime.text import MIMEText


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def url_soup(url):
    response = requests.get(url=url)
    response.encoding = "urf-8"
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def test_page(person):
    ua = UserAgent()
    fake_ua = {'user-agent': ua.random}
    wiki_wiki = wikipediaapi.Wikipedia(
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        user_agent=f'{fake_ua}'
    )
    page_py = wiki_wiki.page(f"{person}")
    if page_py.exists():
        languages = page_py.langlinks
        for lang in languages.keys():
            if lang == 'ru':
                return languages['ru'].title
        return False


def get_list_person():
    day, month, year = date.today().day, date.today().strftime('%B'), date.today().strftime('%Y')
    list_person = []
    url = f'https://en.wikipedia.org/wiki/Deaths_in_{year}#{month}'
    soup = url_soup(url)
    temp_soup = soup.find('div', id='mw-content-text').find('div', class_='mw-parser-output').find_all('ul')
    for i in temp_soup[1:day + 1]:
        for x in i.find_all('li'):
            list_person.append(x.find('a')['title'])
    return list_person


def send_email(message, url='Нет ссылки'):
    sender = config.EMAIL_S           # Почта отправителя
    password = config.EMAIL_PASSWORD  # Пароль
    recipient = config.EMAIL_R        # Почта получателя

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()


    try:
        server.login(sender, password)
        msg = MIMEText(f'{message}\n{url}')
        msg["Subject"] = 'Deaths in 2023'
        server.sendmail(sender, recipient, msg.as_string())
        return f"Сообщение отправлено"
    except Exception as _ex:
        return f"Ошибка: {_ex}"


def send_message(person):
    try:
        wikipedia.set_lang('en')
        person_temp = wikipedia.page(f"{person}")
        page = test_page(person_temp.url.split('/')[-1])
        if page:
            wikipedia.set_lang('ru')
            person_temp = wikipedia.page(f"{page}")
            return send_email(remove_accents(person_temp.summary.split('\n')[0]), person_temp.url)
        else:
            wikipedia.set_lang('en')
            return send_email(person_temp.summary.split('\n')[0], person_temp.url)
    except (PageError, DisambiguationError, WikipediaException):
        return send_email(f"Сообщение отправлено, но нет статьи для {person}")


def main():
    #print(send_email('Запуск'))
    last_list_person = get_list_person()
    while True:
        now_list_person = get_list_person()
        if len(last_list_person) < len(now_list_person):
            list_person = list(set(now_list_person) - set(last_list_person))
            for i in list_person:
                print(send_message(i))
            last_list_person = now_list_person
        time.sleep(60)



if __name__ == '__main__':
    main()
