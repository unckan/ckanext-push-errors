[![Tests](https://github.com/unckan/ckanext-push-errors/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/unckan/ckanext-push-errors/actions)


# ckanext-push-errors

CKAN extension to push critical error to external URLs (like Slack).  


## Requirements

Youu'll requerie an external service to receive the messages. This service must be able to receive POST or GET requests.  

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10            | tested        |
| 2.11            | not yet       |

## Installation

To install ckanext-push-errors:

```bash
pip install -e git+https://github.com/unckan/ckanext-push-errors.git@0.1.0#egg=ckanext-superset
pip install -r https://raw.githubusercontent.com/unckan/ckanext-push-errors/refs/tags/0.1.0/requirements.txt
```

Then add `push_errors` to the `ckan.plugins` setting in your CKAN config file.  

## Config settings

Available settings. Many of them can be formatted with context values:

 - `ckanext.push_errors.url=http://myserver.com`: The URL to push the message
 - `ckanext.push_errors.method=POST`: The method to use (POST or GET only)
 - `ckanext.push_errors.headers='{"Authorization": "Token 123"}'`: A JSON string with the headers to send
 - `ckanext.push_errors.data:'{"message": "{message}"}'`: A JSON string with the data to send
 - `ckanext.push_errors.title="PUSH_ERROR v{push_errors_version} - CKAN {ckan_version}\n{now}\n\n"`: The title (first part) of the message

### Config settings for known platforms

#### Slack

You can post all errors to a Slack channel. You'll need to create a webhook in Slack.
Then use the following settings:

 - `ckanext.push_errors.url=https://hooks.slack.com/services/T02XXXXXX/B061XXXXXX/GASXXXxxxXXXxxx` (something like this).
 - `ckanext.push_errors.method=POST`:
 - `ckanext.push_errors.headers="{}"`
 - `ckanext.push_errors.data='{"text": "{message}", "username": "CKAN PUSH ERRORS", "icon_url": "https://github.com/unckan/ckanext-push-errors/raw/main/icons/server-error.png"}'`: Slack requires the `text` field to be present.

To create a webhook in Slack:
 - Create a new channel if you want to send this notifications to a new channel. If not, you can use any existing channel.
 - Good look with this incredible complex way to create a webhook: https://api.slack.com/messaging/webhooks

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
