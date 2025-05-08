def app(environ, start_response):
    get_params = {}
    query_string = environ.get('QUERY_STRING', '')
    if query_string:
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                get_params[key] = value
            else:
                get_params[param] = ''

    post_params = {}
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    if request_body_size > 0 and environ.get('REQUEST_METHOD') == 'POST':
        request_body = environ['wsgi.input'].read(request_body_size)
        post_data = request_body.decode('utf-8')
        for param in post_data.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                post_params[key] = value
            else:
                post_params[param] = ''

    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]

    response_body = "GET параметры:\n"
    for key, value in get_params.items():
        response_body += f"{key}: {value}\n"

    response_body += "\nPOST параметры:\n"
    for key, value in post_params.items():
        response_body += f"{key}: {value}\n"

    start_response(status, headers)
    return [response_body.encode('utf-8')]

application = app