"""
"""

import subprocess
import logging

import utils

def notify_toast(title:str, msg:str, button:bool = True, audio:bool = False) -> None:
    """
    """

    app_id = r'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    audio_cd = '<audio src="ms-winsoundevent:Notification.Looping.Alarm2" loop="false"/>' if audio else '<audio silent="true"/>'
    button_cd = (
        '<actions><action content="Ignore" arguments="dismiss" activationType="system"/></actions>')

    script = utils.text_fix(f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null

    $xmlString = @"
    <toast duration="short">
        <visual>
            <binding template="ToastGeneric">
                <text>{title}</text>
                <text>{msg}</text>
            </binding>
        </visual>
        {button_cd if button else ''}
        {audio_cd}
    </toast>
    "@

    $xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
    $xml.LoadXml($xmlString)

    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}').Show($toast)
    """)

    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=0x08000000
    )

class ToastHandler(logging.Handler):
    """
    """

    def __init__(self, title:str, button:bool = True, mute_lowlv:bool = True):
        self.title = title
        self.mute_low_level = mute_lowlv
        self.notify_handler = lambda msg, audio: notify_toast(
            self.title, msg, button=button, audio=audio)

        return super().__init__()

    def emit(self, record:logging.LogRecord) -> None:
        try:
            audio = False if self.mute_low_level and record.levelno<=30 else True
            self.notify_handler(self.format(record), audio=audio)
        except Exception as e:
            print(f"ToastHandler error: {e}")
            self.handleError(record)

def setup(*args, **kwargs) -> None:
    """
    """

    logger = logging.getLogger(utils.package_logg[:-1])

    if not utils._is_windows10_or_later():
        logger.warning('Toast notify: Unsupported OS')
        return

    handler = ToastHandler('Python testing script', *args, **kwargs)
    formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
