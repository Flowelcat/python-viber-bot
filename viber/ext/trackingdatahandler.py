import re

from future.utils import string_types

from viber.event import Event
from .handler import Handler


class TrackingDataHandler(Handler):
    """
    Note:
        Not working when user send's picture.
    """
    def __init__(self,
                 callback,
                 filters=None,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pattern=None,
                 pass_groups=False,
                 pass_groupdict=False,
                 pass_user_data=False):

        super(TrackingDataHandler, self).__init__(
            callback,
            pass_event_queue=pass_event_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data)

        if isinstance(pattern, string_types):
            pattern = re.compile(pattern)

        self.pattern = pattern
        self.filters = filters
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict

    def check_event(self, event):
        if isinstance(event, Event) and event.message and event.message.tracking_data:
            if self.pattern:
                if event.message.tracking_data:
                    match = re.match(self.pattern, event.message.tracking_data)
                    if not self.filters:
                        return bool(match)
                    else:
                        return  bool(match) and self.filters(event.message)
            else:
                return True

    def handle_event(self, update, dispatcher):

        optional_args = self.collect_optional_args(dispatcher, update)
        if self.pattern:
            match = re.match(self.pattern, update.message.tracking_data)

            if self.pass_groups:
                optional_args['groups'] = match.groups()
            if self.pass_groupdict:
                optional_args['groupdict'] = match.groupdict()

        return self.callback(dispatcher.bot, update, **optional_args)
