import hashlib
import json
from datetime import datetime
from flask import Flask, request, abort

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['HOST'] = '0.0.0.0'
app.config['PORT'] = 11111
app.config['API_KEY'] = ''  # insert your application API key here


class NotificationField(object):
    TYPE = 'type'
    TIMESTAMP = 'timestamp'
    APP = 'appId'
    SCOPE = 'scopeId'
    USER = 'userId'
    SIGNATURE = 'signature'


class Type(object):
    SCOPE_CREATED = 'ScopeCreated'
    SCOPE_DELETED = 'ScopeDeleted'
    SCOPE_JOINED = 'ScopeJoined'
    SCOPE_LEFT = 'ScopeLeft'


def sign(api_key, fields):
    """
    Sign notification fields using supplied API key.

    :param api_key: API key
    :type api_key: str
    :param fields: notification fields
    :type fields: dict
    :rtype: str
    """
    keys = sorted(fields.keys())
    unsigned_parts = [api_key]
    for key in keys:
        if key != NotificationField.SIGNATURE:
            unsigned_parts.append('{0}={1}'.format(key, fields[key]))
    return hashlib.sha256('\n'.join(unsigned_parts)).hexdigest()


@app.route('/json', methods=['POST'])
def json_sink():
    """
    JSON format notification endpoint
    """
    try:
        raw_data = request.get_data()
        data = json.loads(raw_data)
        handle_notification(data)
        return 'OK'
    except ValueError:
        abort(400)


@app.route('/xml', methods=['POST'])
def xml_sink():
    """
    XML format notification endpoint
    """
    app.logger.debug('Got XML: %s', repr(request.get_data()))
    # TODO: implement
    return 'OK'


@app.route('/post', methods=['POST'])
def post_sink():
    """
    HTTP POST x-www-formurlencoded format notification endpoint
    """
    handle_notification(request.values)
    return 'OK'


@app.route('/get')
def get_sink():
    """
    HTTP GET format notification endpoint
    """
    handle_notification(request.values)
    return 'OK'


def handle_notification(fields):
    """
    Handle notification.

    :param fields: notification fields
    :type fields: dict
    :rtype: bool
    """

    # check signature
    if NotificationField.SIGNATURE in fields:
        expected_signature = sign(app.config['API_KEY'], fields)
        if fields[NotificationField.SIGNATURE] != expected_signature:
            # handle wrong signature (log attempt?)
            app.logger.warning('Wrong signature')
            app.logger.debug('%s != %s',
                             repr(fields[NotificationField.SIGNATURE]),
                             repr(expected_signature))
            return False
    else:
        # handle lack of signature (log attempt?)
        app.logger.warning('No signature')
        return False

    # actual handling
    notification_type = fields.get(NotificationField.TYPE)
    timestamp = fields.get(NotificationField.TIMESTAMP)
    app_id = fields.get(NotificationField.APP)
    scope = fields.get(NotificationField.SCOPE)
    user = fields.get(NotificationField.USER)

    if timestamp is not None:
        timestamp = float(timestamp)
        app.logger.info('Time: %s', datetime.utcfromtimestamp(timestamp))

    if notification_type is None:
        # shouldn't happen - feel free to notify us about this bug
        app.logger.warning('Notification is missing type')

    elif notification_type == Type.SCOPE_CREATED:
        app.logger.info('scope "{0}" created for app {1}'.
                        format(scope, app_id))
        # handle scope creation here
        return True

    elif notification_type == Type.SCOPE_DELETED:
        app.logger.info('scope "{0}" deleted for app {1}'.
                        format(scope, app_id))
        # handle scope deletion here
        return True

    elif notification_type == Type.SCOPE_JOINED:
        app.logger.info('user {0} joined scope "{1}" of app {2}'.
                        format(user, scope, app_id))
        # handle scope joined here
        return True

    elif notification_type == Type.SCOPE_LEFT:
        app.logger.info('user {0} left scope "{1}" of app {2}'.
                        format(user, scope, app_id))
        # handle scope left here
        return True

    else:
        # handle unknown notification type here
        # there might be other types added in future, be prepared
        app.logger.error('Unknown notification type: %s',
                         repr(notification_type))
        return False


if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False),
            host=app.config.get('HOST'),
            port=app.config.get('PORT'))
