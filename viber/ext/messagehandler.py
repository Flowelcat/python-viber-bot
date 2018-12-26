from viber.event import Event
from .handler import Handler


class MessageHandler(Handler):

    def __init__(self,
                 filters,
                 callback,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pass_user_data=False):

        super(MessageHandler, self).__init__(
            callback,
            pass_event_queue=pass_event_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data)

        self.filters = filters

    def check_event(self, event):
        if isinstance(event, Event) and event.message:
            if not self.filters:
                res = True

            else:
                message = event.message
                res = self.filters(message)
        else:
            res = False

        return res

    def handle_event(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, update)

        return self.callback(dispatcher.bot, update, **optional_args)
