from future.utils import string_types

from viber.event import Event
from viber.ext.handler import Handler


class CommandHandler(Handler):

    def __init__(self,
                 command,
                 callback,
                 filters=None,
                 pass_args=False,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pass_user_data=False, ):

        super(CommandHandler, self).__init__(
            callback,
            pass_event_queue=pass_event_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data)

        if isinstance(command, string_types):
            self.command = [command.lower()]
        else:
            self.command = [x.lower() for x in command]

        self.filters = filters

        self.pass_args = pass_args

    def check_event(self, event):
        if isinstance(event, Event) and event.message:

            message = event.message

            if message.text and message.text.startswith('/') and len(message.text) > 1 and message.text.strip('/') in self.command:
                if self.filters is None:
                    res = True
                else:
                    res = self.filters(message)

                return res

        return False

    def handle_event(self, request, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, request)

        message = request.message

        if self.pass_args:
            optional_args['args'] = message.text.split()[1:]

        return self.callback(dispatcher.bot, request, **optional_args)
