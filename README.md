# zen-demo-python

> :warning: **SECURITY WARNING**
>
> This is a demonstration application that intentionally contains security vulnerabilities for educational purposes.
> - **DO NOT** run this in production environment
> - **DO NOT** run without proper protection
> - It is strongly recommended to use [Aikido Zen](https://www.aikido.dev/zen) as a security layer


## setup

`python3 -m venv .venv`

`. .venv/bin/activate`

`pip install -r requirements.txt`

## run

`AIKIDO_BLOCK=1 flask --app flaskr run --debug`

Test with database
`DATABASE_URL=postgres://username:passowrd@localhost:5432/aikido?sslmode=disable`

Production test
`./.venv/bin/gunicorn --bind=0.0.0.0:8080 wsgi:app`
