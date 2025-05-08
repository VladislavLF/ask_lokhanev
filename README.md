Проект «Вопросы и Ответы» (Технопарк МГТУ. Программа по веб-разработке (1 семестр). Дисциплина: Web-технологии). <br />
 Автор: Лоханев В.Ф. (WEB-12). <br />
 Верстка сайта находится в директории Layout. <br />
 Заполнение базы данных MySQL осуществляется по management command: python manage.py fill_db [ratio]. Предварительно необходимо настроить DATABASES в settings.py под свою базу данных.  <br />

EER Diagram
![image](https://github.com/user-attachments/assets/0a79bf83-4cb7-4241-ac31-d0bbb29bd874)

Главная страница
![image](https://github.com/user-attachments/assets/6a8d3bb6-c619-4968-8c0c-a52284cc2197)

Страница вопроса
![image](https://github.com/user-attachments/assets/95f65d1b-400d-4f07-afd3-a8535b7ead87)

Задать вопрос
![image](https://github.com/user-attachments/assets/31c42db2-512f-44b1-8282-df32ff8c075e)

Войти
![image](https://github.com/user-attachments/assets/8c05183b-87a7-493a-8dd8-f705c7f91abc)

Регистрация
![image](https://github.com/user-attachments/assets/43a36498-46b8-4a3e-bbe7-f5afe6542c77)

Профиль
![image](https://github.com/user-attachments/assets/79de809b-026d-4931-9aaa-af9de9dc4a11)

Отдача статического документа напрямую через nginx <br /> 
Запрос: <br />
`ab -n 5000 http://127.0.0.1/static/css/styles.css` <br />
Ответ: <br />
```
Server Software:        nginx/1.18.0
Server Hostname:        127.0.0.1
Server Port:            80

Document Path:          /static/css/styles.css
Document Length:        8582 bytes

Concurrency Level:      1
Time taken for tests:   1.112 seconds
Complete requests:      5000
Failed requests:        0
Total transferred:      44240000 bytes
HTML transferred:       42910000 bytes
Requests per second:    4495.73 [#/sec] (mean)
Time per request:       0.222 [ms] (mean)
Time per request:       0.222 [ms] (mean, across all concurrent requests)
Transfer rate:          38845.93 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       2
Processing:     0    0   0.2      0       3
Waiting:        0    0   0.2      0       3
Total:          0    0   0.2      0       3

Percentage of the requests served within a certain time (ms)
  50%      0
  66%      0
  75%      0
  80%      0
  90%      0
  95%      0
  98%      1
  99%      1
 100%      3 (longest request)
```

Отдача статического документа напрямую через gunicorn <br />
Запрос: <br />
`ab -n 5000 http://127.0.0.1:8000/static/css/styles.css` <br /> 
Ответ: <br />
```
Server Software:        gunicorn
Server Hostname:        127.0.0.1
Server Port:            8000

Document Path:          /static/css/styles.css
Document Length:        8582 bytes

Concurrency Level:      1
Time taken for tests:   31.084 seconds
Complete requests:      5000
Failed requests:        0
Total transferred:      44730000 bytes
HTML transferred:       42910000 bytes
Requests per second:    160.86 [#/sec] (mean)
Time per request:       6.217 [ms] (mean)
Time per request:       6.217 [ms] (mean, across all concurrent requests)
Transfer rate:          1405.29 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       3
Processing:     1    6  35.1      2     609
Waiting:        0    6  35.1      1     609
Total:          1    6  35.1      2     609

Percentage of the requests served within a certain time (ms)
  50%      2
  66%      2
  75%      2
  80%      2
  90%      3
  95%      4
  98%     20
  99%    213
 100%    609 (longest request)
```

Отдача динамического документа напрямую через gunicorn <br />
Запрос: <br />
`ab -n 500 http://127.0.0.1:8000/` <br />
Ответ: <br />
```
Server Software:        gunicorn
Server Hostname:        127.0.0.1
Server Port:            8000

Document Path:          /
Document Length:        123311 bytes

Concurrency Level:      1
Time taken for tests:   485.510 seconds
Complete requests:      500
Failed requests:        0
Total transferred:      61804500 bytes
HTML transferred:       61655500 bytes
Requests per second:    1.03 [#/sec] (mean)
Time per request:       971.019 [ms] (mean)
Time per request:       971.019 [ms] (mean, across all concurrent requests)
Transfer rate:          124.31 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       1
Processing:   934  971  41.2    959    1291
Waiting:      933  970  41.2    958    1290
Total:        934  971  41.2    959    1291

Percentage of the requests served within a certain time (ms)
  50%    959
  66%    964
  75%    970
  80%    975
  90%   1005
  95%   1064
  98%   1125
  99%   1169
 100%   1291 (longest request)
```

Отдача динамического документа через проксирование запроса с nginx на gunicorn <br />
Запрос: <br />
`ab -n 500 http://127.0.0.1/` <br />
Ответ: <br />
```
Server Software:        nginx/1.18.0
Server Hostname:        127.0.0.1
Server Port:            80

Document Path:          /
Document Length:        123311 bytes

Concurrency Level:      1
Time taken for tests:   581.364 seconds
Complete requests:      500
Failed requests:        0
Total transferred:      61822500 bytes
HTML transferred:       61655500 bytes
Requests per second:    0.86 [#/sec] (mean)
Time per request:       1162.728 [ms] (mean)
Time per request:       1162.728 [ms] (mean, across all concurrent requests)
Transfer rate:          103.85 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       1
Processing:   940 1163 259.7   1045    2124
Waiting:      940 1162 259.7   1045    2124
Total:        940 1163 259.7   1046    2124

Percentage of the requests served within a certain time (ms)
  50%   1046
  66%   1119
  75%   1224
  80%   1329
  90%   1625
  95%   1790
  98%   1890
  99%   1925
 100%   2124 (longest request)
```

Отдача динамического документа через проксирование запроса с nginx на gunicorn, при кэшировние ответа на nginx (proxy cache) <br />
Запрос: <br />
`ab -n 500 http://127.0.0.1/` <br />
Ответ: <br />
```
Server Software:        nginx/1.18.0
Server Hostname:        127.0.0.1
Server Port:            80

Document Path:          /
Document Length:        123311 bytes

Concurrency Level:      1
Time taken for tests:   1.317 seconds
Complete requests:      500
Failed requests:        0
Total transferred:      61843000 bytes
HTML transferred:       61655500 bytes
Requests per second:    379.70 [#/sec] (mean)
Time per request:       2.634 [ms] (mean)
Time per request:       2.634 [ms] (mean, across all concurrent requests)
Transfer rate:          45862.87 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       2
Processing:     0    3  48.2      0    1077
Waiting:        0    2  48.1      0    1077
Total:          0    3  48.2      0    1077

Percentage of the requests served within a certain time (ms)
  50%      0
  66%      0
  75%      0
  80%      1
  90%      1
  95%      1
  98%      2
  99%      3
 100%   1077 (longest request)
```

Насколько быстрее отдается статика по сравнению с WSGI? <br />
Ответ: <br />
> Для ответа на вопрос, необходимо обратиться к параметру TPR (Time per request). <br />
> Nginx TPR: 0.222 [ms] (mean) <br />
> Gunicorn TPR: 6.217 [ms] (mean) <br />
> Разница на 5.995 [ms] (mean), nginx отдает статику быстрее в 28 раз в среднем. v

Во сколько раз ускоряет работу proxy_cache? <br />
Ответ: <br />
> Сравним время отдачи динамического документа через nginx без кеширования и с кешированием. <br />
> Без кеширования: 1162.728 [ms] (mean) <br />
> С кешированием: 2.634 [ms] (mean) <br />
> Таким образом, proxy_cache ускоряет работу в 441 раза. <br />
