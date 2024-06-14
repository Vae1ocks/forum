## How to start the proj

(docker needed)
1st term:

**docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management**

2nd term:

**celery -A forum worker --loglevel=info**

3rd term:

**docker run -it --rm --name redis -p 6379:6379 redis**

4th term:

**py manage.py runserver**
