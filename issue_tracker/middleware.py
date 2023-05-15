import sys
import traceback
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .channels.backends.discord_backend import Channel
from .channels.channels_factory import channel_transformer


class ExceptionHandleMiddleware:
    def __init__(self, get_response=None):
        """
        Initializes a new instance of the ExceptionHandleMiddleware class.

        Args:
            get_response: The next middleware in the chain. Optional.
        """
        self.get_response = get_response
        self.channels = {}

    def __call__(self, request):
        """
        Process the incoming request and call the next middleware in the chain.

        Args:
            request: The incoming request.

        Returns:
            The response generated by the next middleware in the chain.
        """
        return self.get_response(request)

    def add_channel(self, name: str, channel: Channel):
        """
        Adds an issue tracker channel to the list of channels used by the middleware.

        Args:
            name: The name of the issue tracker channel.
            channel: The Channel instance to add.
        """
        self.channels[name] = channel

    def process_exception(self, request, exception):
        """
        Process the exception and send notifications to the configured issue tracker channels.

        Args:
            request: The request object.
            exception: The exception object.

        Raises:
            ImproperlyConfigured: If the issue tracker channels configuration is missing.
        """
        exception_type = exception.__class__.__name__
        kind, info, data = sys.exc_info()
        data = "\n".join(traceback.format_exception(kind, info, data))

        if not settings.ISSUE_TRACKER_CHANNELS_CONFIGURATION:
            raise ImproperlyConfigured("issue tracker channels configuration missing")

        for channel_name in settings.ISSUE_TRACKER_CHANNELS_CONFIGURATION:
            channel = self.channels.get(channel_name)
            if not channel:
                # Create the channel object if not already created
                channel = channel_transformer.get_channel(name=channel_name)
                self.add_channel(channel_name, channel)
            channel.send_notification(
                configuration=settings.ISSUE_TRACKER_CHANNELS_CONFIGURATION[channel_name], request=request,
                data=data, exception_type=exception_type
            )
