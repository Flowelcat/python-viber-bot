

class Handler(object):
    def __init__(self,
                 callback,
                 pass_event_queue=False,
                 pass_job_queue=False,
                 pass_user_data=False):
        self.callback = callback
        self.pass_event_queue = pass_event_queue
        self.pass_job_queue = pass_job_queue
        self.pass_user_data = pass_user_data

    def check_event(self, event):
        raise NotImplementedError

    def handle_event(self, event, bot):
        raise NotImplementedError

    def collect_optional_args(self, dispatcher, event=None):
        optional_args = dict()

        if self.pass_event_queue:
            optional_args['event_queue'] = dispatcher.event_queue
        if self.pass_job_queue:
            optional_args['job_queue'] = dispatcher.job_queue
        if self.pass_user_data:
            if event.user_id:
                user_id = event.user_id
            elif event.user:
                user_id = event.user.id
            else:
                user_id = None

            if self.pass_user_data:
                optional_args['user_data'] = dispatcher.user_data[user_id if user_id else None]

        return optional_args