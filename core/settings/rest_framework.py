REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API системы выплат',
    'VERSION': '1.0.0',
    'DESCRIPTION': 'REST API для управления заявками на выплату',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Платежи', 'description': 'Операции с заявками на выплату'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'SECURITY': [{'basicAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'basicAuth': {
                'type': 'http',
                'scheme': 'basic',
            }
        }
    },
}
