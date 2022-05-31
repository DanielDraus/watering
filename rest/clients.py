""""Clients to talk to slack and Ubidots."""  # pylint: disable=invalid-name
import urequests
import utime



class Slack:
    def __init__(self, app_id, secret_id, token):
        """
        Get an "incoming-webhook" URL from your slack account.
        @see https://api.slack.com/incoming-webhooks
        eg: https://hooks.slack.com/services/<app_id>/<secret_id>/<token>
        """
        self._url = "https://hooks.slack.com/services/%s/%s/%s" % (
            app_id,
            secret_id,
            token,
        )

    def slack_it(self, msg):
        """ Send a message to a predefined slack channel."""
        headers = {"content-type": "application/json"}
        data = '{"text":"%s"}' % msg
        resp = urequests.post(self._url, data=data, headers=headers)
        return "Message Sent" if resp.status_code == 200 else "Failed to sent message"



class Ubidots:
    def __init__(self, TOKEN, device_label):
        self.url = "https://things.ubidots.com/api/v1.6/devices/{}?token={}".format(
            device_label, TOKEN
        )

    def post_request(self, payload):
        """Creates the headers for the HTTP requests and Makes the HTTP requests"""
        print("[DEBUG] Uploading Payload: %s" % payload)
        assert isinstance(payload, dict)

        status = 400
        attempts = 0
        while status >= 400 and attempts <= 5:
            req = urequests.post(url=self.url, json=payload)
            status = req.status_code
            attempts += 1
            utime.sleep(1)
            print("[DEBUG] Sending data to Ubidots...")

        # Processes results
        if status == 200:
            print("[INFO] Request made properly, Updated Ubidots with %s." % payload)
            return True
        else:
            print(
                "[ERROR] Could not send data after 5 attempts, please check "
                "your token credentials and internet connection."
            )
            return False

