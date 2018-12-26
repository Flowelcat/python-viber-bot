import re
import warnings

from future.utils import string_types

from telegram import Update

from viber.event import Event
from .handler import Handler


class RegexHandler(Handler):
    def __init__(self,
                 pattern,
                 callback,
                 pass_groups=False,
                 pass_groupdict=False,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pass_user_data=False):

        super(RegexHandler, self).__init__(
            callback,
            pass_event_queue=pass_event_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data)

        if isinstance(pattern, string_types):
            pattern = re.compile(pattern)

        self.pattern = pattern
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict

    def check_event(self, event):
        if not isinstance(event, Event) or event.message is None or event.message.text is None:
            return False

        match = re.match(self.pattern, event.message.text)

        return bool(match)

    def handle_event(self, event, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, event)
        match = re.match(self.pattern, event.message.text)

        if self.pass_groups:
            optional_args['groups'] = match.groups()
        if self.pass_groupdict:
            optional_args['groupdict'] = match.groupdict()

        return self.callback(dispatcher.bot, event, **optional_args)
